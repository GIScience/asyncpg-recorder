from inspect import signature
import pickle
from typing import Callable
import zlib
import json
import asyncpg
from functools import wraps
from pathlib import Path
from testcontainers.postgres import PostgresContainer


def use_cassette(path: str | Path):
    """Depending on Existenz of the cassette either record or replay response."""
    if isinstance(path, str):
        path = Path(path)

    if path.suffix not in [".json", ".pickle"]:
        raise ValueError("Only .json and .pickle files are supported as cassettes.")

    if path.exists():
        # If cassette exists try to replay, ...
        try:
            return _replay(path)
        except KeyError:
            # For given arguments no record exists. Continue with recording.
            pass
    # ... else record.
    return _record(path)


def _replay(path: Path) -> Callable:
    def _(func: Callable) -> Callable:
        """Connect to a temporary Postgres database and return recorded response."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            connect_original = asyncpg.connect
            execute_original = asyncpg.connection.Connection._execute

            @wraps(connect_original)
            async def connect_wrapper(*args, **kwargs):
                # TODO: add name to container
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
                # TODO: generate hash from args/kwargs
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash = str(zlib.crc32(pickle.dumps(args)))
                cassette = _read_cassette(path)
                return cassette[hash]["results"]

            asyncpg.connect = connect_wrapper
            asyncpg.connection.Connection._execute = execute_wrapper
            return await func(*args, **kwargs)

        return wrapper

    return _


def _record(path: Path) -> Callable:
    def _(func: Callable) -> Callable:
        """Record input arguments and database response."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            execute_original = asyncpg.connection.Connection._execute

            @wraps(execute_original)
            async def execute_wrapper(self, *execute_args, **execute_kwargs):
                args = {"args": execute_args, "kwargs": execute_kwargs}
                hash = str(zlib.crc32(pickle.dumps(args)))
                result = await execute_original(
                    self,
                    *execute_args,
                    **execute_kwargs,
                )
                try:
                    cassette = _read_cassette(path)
                except (FileNotFoundError, json.JSONDecodeError):
                    cassette = {}
                cassette = {
                    hash: {
                        "results": [dict(r) for r in result],
                        # TODO:
                        # "results": pickle.dumps(result),
                        # https://github.com/MagicStack/asyncpg/pull/1000
                        **_args_to_kwargs(execute_original, execute_args),
                        **kwargs,
                    },
                    **cassette,
                }
                _write_cassette(path, cassette)
                return result

            asyncpg.connection.Connection._execute = execute_wrapper
            return await func(*args, **kwargs)

        return wrapper

    return _


def _args_to_kwargs(func, args):
    return dict(
        zip(
            list(signature(func).parameters.keys())[1:],
            args,
        )
    )


def _write_cassette(path: Path, cassette: dict):
    match path.suffix:
        case ".json":
            with open(path, "w") as file:
                json.dump(cassette, file)
        case ".pickle":
            with open(path, "wb") as file:
                pickle.dump(cassette, file)
        case _:
            raise ValueError("Only .json and .pickle files are supported as cassettes.")


def _read_cassette(path: Path) -> dict:
    match path.suffix:
        case ".json":
            with open(path, "r") as file:
                return json.load(file)
        case ".pickle":
            with open(path, "rb") as file:
                return pickle.load(file)
        case _:
            raise ValueError("Only .json and .pickle files are supported as cassettes.")
