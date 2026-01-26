import json
import logging
import os
import pickle
import zlib
from collections import OrderedDict
from functools import wraps
from inspect import signature
from json import JSONDecodeError
from pathlib import Path
from typing import Callable

import asyncpg
from asyncpg.protocol.protocol import _create_record as Record  # noqa: N812

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
    func.asyncpg_recorder = True

    # TODO: Fix C901
    @wraps(func)
    async def wrapper(*args, **kwargs) -> list[Record]:  # noqa: C901
        connect_original = asyncpg.connect
        execute_original = asyncpg.connection.Connection._execute

        try:
            # Replay
            # ------
            # Connect to a temporary Postgres database and return recorded response.
            @wraps(connect_original)
            async def connect_wrapper(*args, **kwargs):
                return await connect_original(dsn=DSN)

            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                path = name()
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash_ = str(zlib.crc32(pickle.dumps(args)))
                path_json = path.with_suffix(".json")
                path_pickle = path.with_suffix(".pickle")
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
                path = name()
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash_ = str(zlib.crc32(pickle.dumps(args)))
                result = await execute_original(
                    self,
                    *execute_args,
                    **execute_kwargs,
                )
                try:
                    try:
                        with open(path.with_suffix(".json"), "r") as file:
                            cassette = json.load(file)
                    except (FileNotFoundError, JSONDecodeError):
                        with open(path.with_suffix(".pickle"), "rb") as file:
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
                    with open(path.with_suffix(".json"), "w") as file:
                        json.dump(cassette, file)
                except TypeError:
                    # remove partly written JSON file
                    if path.with_suffix(".json").exists():
                        path.with_suffix(".json").unlink()
                    with open(path.with_suffix(".pickle"), "wb") as file:
                        pickle.dump(cassette, file)
                return result

            logger.info("Record to cassette.")

            asyncpg.connect = connect_original  # reset
            asyncpg.connection.Connection._execute = execute_wrapper
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


def name() -> Path:
    # TODO: support base dir (then rewrite tests to use tmp_dir)
    # TODO: Try out with xdist
    global ROOT_DIR
    global CASSETTES_DIR
    node_id = os.environ["PYTEST_CURRENT_TEST"]
    if "[" in node_id and "]" in node_id:
        start = node_id.index("[") + 1
        end = node_id.rindex("]")
        params = f"[{node_id[start:end]}]"
    else:
        params = ""
    file_path = Path(
        node_id.replace(" (call)", "")
        .replace(" (setup)", "")
        .replace(" (teardown)", "")
        .replace("::", "--")
        .replace(f"{params}", "")
        # .raw will be replaced by .with_suffix during file access
        + ".cassette.raw"
    )
    if CASSETTES_DIR is not None:
        for i, part in enumerate(CASSETTES_DIR.parts):
            if part == file_path.parts[i]:
                continue
            else:
                break
        else:
            i = 0
        file_path = ROOT_DIR / CASSETTES_DIR / Path(*file_path.parts[i:])
    else:
        file_path = ROOT_DIR / file_path
    file_path = file_path.resolve()
    file_path.mkdir(parents=True, exist_ok=True)
    return file_path
