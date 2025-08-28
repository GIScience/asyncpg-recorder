import pytest
from testcontainers.postgres import PostgresContainer

from asyncpg_recorder.main import name
from tests import main

pytest_plugins = ["pytester"]

@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as mp:
        yield mp

@pytest.fixture(scope="module")
def postgres(monkeypatch_module):
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
        monkeypatch_module.setattr(main, "DSN", dsn)
        yield


@pytest.fixture
def path():
    p = name()
    yield p
    try:
        p.with_suffix(".json").unlink()
    except FileNotFoundError:
        p.with_suffix(".pickle").unlink()
