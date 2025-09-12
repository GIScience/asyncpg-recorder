import logging
from pathlib import Path

from testcontainers.postgres import PostgresContainer

from asyncpg_recorder import main
from asyncpg_recorder.config import _read_config

POSTGRES: PostgresContainer


def pytest_configure(config):
    cassettes_dir = _read_config().get("cassettes-dir", "")
    if cassettes_dir:
        Path(
            Path(config.rootpath) / Path(cassettes_dir),
        ).mkdir(parents=True, exist_ok=True)

    main.ROOT_DIR = config.rootpath
    main.CASSETTES_DIR = cassettes_dir


def pytest_sessionstart(session):
    logging.info("Start Postgres testcontainer for the entire pytest session.")

    global POSTGRES
    POSTGRES = PostgresContainer("postgres").start()  # type: ignore
    dsn = "postgres://{user}:{password}@127.0.0.1:{port}/{database}".format(
        user=POSTGRES.username,
        password=POSTGRES.password,
        port=POSTGRES.get_exposed_port(5432),
        database=POSTGRES.dbname,
    )
    main.DSN = dsn


def pytest_sessionfinish(session, exitstatus):
    logging.info("Stop Postgres testcontainer.")

    global POSTGRES
    POSTGRES.stop()
