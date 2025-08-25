from asyncpg_recorder.main import name
from tests import main

import pytest
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
def path():
    p = name()
    yield p
    try:
        p.with_suffix(".json").unlink()
    except FileNotFoundError:
        p.with_suffix(".pickle").unlink()
