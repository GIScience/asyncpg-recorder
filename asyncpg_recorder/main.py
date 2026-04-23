import json
import logging
import pickle
import zlib
from collections import OrderedDict
from functools import partial, wraps
from inspect import signature
from json import JSONDecodeError
from pathlib import Path
from typing import Callable

import asyncpg
from asyncpg.protocol.protocol import _create_record as Record  # noqa: N812
from pytest_nodeid_to_filepath import get_filepath

logger = logging.getLogger(__name__)

# will be instantiated on pytest session start (see plugin.py)
DSN: str = ""
ROOT_DIR: Path
CASSETTES_DIR: Path | None = None


class CassetteDecodeError(IOError):
    pass


class CassetteNotFoundError(FileNotFoundError):
    pass


class HashError(KeyError):
    pass


# TODO: Fix C901
def use_cassette(func: Callable):  # noqa: C901
    """Replay or record database response."""
    func.asyncpg_recorder: bool = True

    # TODO: Fix C901
    @wraps(func)
    async def wrapper(*args, **kwargs) -> list[Record]:  # noqa: C901
        connect_original = asyncpg.connect
        execute_original = asyncpg.connection.Connection._execute
        global CASSETTES_DIR
        if CASSETTES_DIR is not None:
            get_filepath_ = partial(get_filepath, directory=CASSETTES_DIR, count=False)
        else:
            get_filepath_ = partial(get_filepath, count=False)

        try:
            # Replay
            # ------
            # Connect to a temporary Postgres database and return recorded response.
            @wraps(connect_original)
            async def connect_wrapper(*args, **kwargs):
                return await connect_original(dsn=DSN)

            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash_ = str(zlib.crc32(pickle.dumps(args)))
                path_json = get_filepath_(extension=".cassette.json")
                path_pickle = get_filepath_(extension=".cassette.pickle")
                if path_json.exists():
                    try:
                        with open(path_json, "r") as file:
                            cassette = json.load(file)
                            logger.info(f"Found cassette at {path_json!s}.")
                    except JSONDecodeError as e:
                        path_json.unlink()
                        raise CassetteDecodeError() from e
                elif path_pickle.exists():
                    try:
                        with open(path_pickle, "rb") as file:
                            cassette = pickle.load(file)  # noqa: S301
                            logger.info(f"Found cassette at {path_pickle!s}.")
                    except EOFError as e:
                        path_pickle.unlink()
                        raise CassetteDecodeError() from e
                else:
                    path = get_filepath_(extension=".cassette")
                    msg = f"Found no cassette at {path!s}.json|.pickle"
                    logger.error(msg)
                    raise CassetteNotFoundError(msg)  # noqa: TRY301
                try:
                    raw = cassette[hash_]
                except KeyError as e:
                    raise HashError from e
                records = []
                for r in raw["results"]:
                    mapping = []
                    for i, k in enumerate(r.keys()):
                        mapping.append((k, i))
                    records.append(Record(OrderedDict(mapping), tuple(r.values())))
                return records

            logger.info("Try to replay from cassette.")

            asyncpg.connect = connect_wrapper  # ty: ignore
            asyncpg.connection.Connection._execute = execute_wrapper  # ty: ignore

            return await func(*args, **kwargs)

        except (HashError, CassetteNotFoundError, CassetteDecodeError):
            # Record
            # -----
            # Record input arguments and database response.
            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash_ = str(zlib.crc32(pickle.dumps(args)))
                path_json = get_filepath_(extension=".cassette.json")
                path_pickle = get_filepath_(extension=".cassette.pickle")
                result = await execute_original(
                    self,
                    *execute_args,
                    **execute_kwargs,
                )
                try:
                    try:
                        with open(path_json, "r") as file:
                            cassette = json.load(file)
                    except (FileNotFoundError, JSONDecodeError):
                        with open(path_pickle, "rb") as file:
                            cassette = pickle.load(file)  # noqa: S301
                except FileNotFoundError:
                    cassette = {}
                cassette = {
                    hash_: {
                        "results": [dict(r) for r in result],
                        # TODO:
                        # "results": pickle.dumps(result),
                        # https://github.com/MagicStack/asyncpg/pull/1000
                        **args_to_kwargs(execute_original, execute_args),
                        **execute_kwargs,
                    },
                    **cassette,
                }
                try:
                    with open(path_json, "w") as file:
                        json.dump(cassette, file)
                except TypeError:
                    # remove partly written JSON file
                    if path_json.exists():
                        path_json.unlink()
                    with open(path_pickle, "wb") as file:
                        pickle.dump(cassette, file)
                return result

            logger.info("Record to cassette.")

            asyncpg.connect = connect_original  # reset
            asyncpg.connection.Connection._execute = execute_wrapper  # type: ignore
            return await func(*args, **kwargs)

        finally:
            # Reset
            # -----
            # Reset mocked asyncpg function to original.
            asyncpg.connect = connect_original
            asyncpg.connection.Connection._execute = execute_original

    return wrapper


def args_to_kwargs(func, args):
    return dict(
        zip(
            list(signature(func).parameters.keys())[1:],
            args,
            strict=False,
        )
    )
