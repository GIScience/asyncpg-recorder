import logging
from pathlib import Path

from testcontainers.postgres import PostgresContainer

from asyncpg_recorder import main
from asyncpg_recorder.config import _read_config

logger = logging.getLogger(__name__)

POSTGRES: PostgresContainer
POSTGRES_NEEDED: bool = False
POSTGRES_STARTED: bool = False


def pytest_configure(config):
    cassettes_dir = _read_config().get("cassettes-dir", "")
    if cassettes_dir:
        Path(
            Path(config.rootpath) / Path(cassettes_dir),
        ).mkdir(parents=True, exist_ok=True)

    main.ROOT_DIR = config.rootpath
    main.CASSETTES_DIR = cassettes_dir


def pytest_collection_modifyitems(session, config, items):
    global POSTGRES_NEEDED
    POSTGRES_NEEDED = any(hasattr(item.function, "asyncpg_recorder") for item in items)


def pytest_runtestloop(session):
    global POSTGRES
    global POSTGRES_STARTED

    if not POSTGRES_STARTED and POSTGRES_NEEDED:
        POSTGRES = PostgresContainer("postgres").start()  # type: ignore
        dsn = "postgres://{user}:{password}@127.0.0.1:{port}/{database}".format(
            user=POSTGRES.username,
            password=POSTGRES.password,
            port=POSTGRES.get_exposed_port(5432),
            database=POSTGRES.dbname,
        )
        main.DSN = dsn
        POSTGRES_STARTED = True


def pytest_sessionfinish(session, exitstatus):
    if POSTGRES_STARTED:
        logger.info("Stop Postgres testcontainer.")
        global POSTGRES
        POSTGRES.stop()
