from pytest_nodeid_to_filepath import get_filepath
import pytest
from testcontainers.postgres import PostgresContainer

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
    with PostgresContainer("postgres:18.3") as postgres:
        dsn = "postgres://{user}:{password}@127.0.0.1:{port}/{database}".format(
            user=postgres.username,
            password=postgres.password,
            port=postgres.get_exposed_port(5432),  # 5432 is default port of postgres
            database=postgres.dbname,
        )
        monkeypatch_module.setattr(main, "DSN", dsn)
        yield


@pytest.fixture
def path_json():
    p = get_filepath(extension=".cassette.json", directory="tests/cassettes")
    yield p
    p.unlink()


@pytest.fixture
def path_pickle():
    p = get_filepath(extension=".cassette.pickle", directory="tests/cassettes")
    yield p
    p.unlink()
