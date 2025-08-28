import json
import logging
import os
import pickle
import zlib
from functools import wraps
from inspect import signature
from json import JSONDecodeError
from pathlib import Path
from typing import Callable

import asyncpg

# will be instantiated on pytest session start (see plugin.py)
DSN: str = ""


class CassetteNotFoundError(FileNotFoundError):
    pass


class HashError(KeyError):
    pass


# TODO: Fix C901
def use_cassette(func: Callable):  # noqa: C901
    """Replay or record database response."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
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
                hash = str(zlib.crc32(pickle.dumps(args)))
                try:
                    with open(path.with_suffix(".json"), "r") as file:
                        cassette = json.load(file)
                except (FileNotFoundError, JSONDecodeError):
                    try:
                        with open(path.with_suffix(".pickle"), "rb") as file:
                            cassette = pickle.load(file)  # noqa: S301
                    except FileNotFoundError as e:
                        # raise custom error to avoid catching any other error
                        raise CassetteNotFoundError from e
                try:
                    return cassette[hash]["results"]
                except KeyError as e:
                    # raise custom error to avoid catching any other error
                    raise HashError from e

            logging.info("Try to replay from cassette.")

            asyncpg.connect = connect_wrapper
            asyncpg.connection.Connection._execute = execute_wrapper

            return await func(*args, **kwargs)

        except (HashError, CassetteNotFoundError):
            # Record
            # -----
            # Record input arguments and database response.
            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                path = name()
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash = str(zlib.crc32(pickle.dumps(args)))
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
                    hash: {
                        "results": [dict(r) for r in result],
                        # TODO:
                        # "results": pickle.dumps(result),
                        # https://github.com/MagicStack/asyncpg/pull/1000
                        **args_to_kwargs(execute_original, execute_args),
                        **kwargs,
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

            logging.info("Record to cassette.")

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
    node_id = os.environ["PYTEST_CURRENT_TEST"]
    if "[" in node_id and "]" in node_id:
        start = node_id.index("[") + 1
        end = node_id.index("]")
        params = f"[{node_id[start:end]}]"
    else:
        params = ""
    file_path = Path(
        node_id.replace(" (call)", "")
        .replace(" (setup)", "")
        .replace(" (teardown)", "")
        .replace("::", "--")
        .replace(f"{params}", "")
        + ".cassette.raw"  # .raw will be replaced by .with_suffix during file access
    )
    return file_path.resolve()
