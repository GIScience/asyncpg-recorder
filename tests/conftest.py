from os import PathLike
from asyncpg import Path
from tests import main

import pytest
from uuid import uuid4
from testcontainers.postgres import PostgresContainer


@pytest.fixture()
def postgres(monkeypatch):
    """Spin up a Postgres container for testing.

    Connection string will be different for each test session.
    """
    with PostgresContainer("postgres:15") as postgres:
        dsn = "postgres://{user}:{password}@127.0.0.1:{port}/{database}".format(
            user=postgres.username,
            password=postgres.password,
            port=postgres.get_exposed_port(5432),  # 5432 is default port of postgres
            database=postgres.dbname,
        )
        monkeypatch.setattr(main, "DSN", dsn)
        yield


@pytest.fixture
def tmp_cassette_json(tmp_path):
    tmp_dir = tmp_path / str(uuid4())
    tmp_dir.mkdir()
    cassette = tmp_dir / "cassette.json"
    yield cassette
    try:
        cassette.unlink()
    except Exception:
        pass


@pytest.fixture
def tmp_cassette_pickle(tmp_path):
    tmp_dir = tmp_path / str(uuid4())
    tmp_dir.mkdir()
    cassette = tmp_dir / "cassette.pickle"
    yield cassette
    try:
        cassette.unlink()
    except Exception:
        pass
