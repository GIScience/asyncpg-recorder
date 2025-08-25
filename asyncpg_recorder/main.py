from inspect import signature
import os
import pickle
from typing import Callable
from json import JSONDecodeError
import zlib
import json
import asyncpg
from functools import wraps
from pathlib import Path
from testcontainers.postgres import PostgresContainer


def use_cassette(func: Callable):
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
                # TODO: add name to container
                # TODO: start only one container per test session
                with PostgresContainer("postgres") as postgres:
                    dsn = "postgres://{user}:{password}@127.0.0.1:{port}/{database}".format(
                        user=postgres.username,
                        password=postgres.password,
                        port=postgres.get_exposed_port(5432),
                        database=postgres.dbname,
                    )
                    return await connect_original(dsn=dsn)

            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                path = name()
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash = str(zlib.crc32(pickle.dumps(args)))
                try:
                    with open(path.with_suffix(".json"), "r") as file:
                        cassette = json.load(file)
                except (FileNotFoundError, JSONDecodeError):
                    with open(path.with_suffix(".pickle"), "rb") as file:
                        cassette = pickle.load(file)
                return cassette[hash]["results"]

            asyncpg.connect = connect_wrapper
            asyncpg.connection.Connection._execute = execute_wrapper

            return await func(*args, **kwargs)

        except (KeyError, FileNotFoundError):
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
                            cassette = pickle.load(file)
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

            asyncpg.connect = connect_original  # reset
            asyncpg.connection.Connection._execute = execute_wrapper
            return await func(*args, **kwargs)

    return wrapper


def args_to_kwargs(func, args):
    return dict(
        zip(
            list(signature(func).parameters.keys())[1:],
            args,
        )
    )


def name() -> Path:
    # TODO: support base dir (then rewrite tests to use tmp_dir)
    # TODO: support postfix (write test with multiple calls to verify)
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
        + ".cassette.raw"  # .raw will be replaced by Path.with_suffix during file access
    )
    return file_path.resolve()
