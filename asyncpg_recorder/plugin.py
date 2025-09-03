import logging

from py_pglite import PGliteManager

from asyncpg_recorder import main

MANAGER: PGliteManager


def pytest_configure(config):
    main.ROOT_DIR = config.rootpath


def pytest_sessionstart(session):
    logging.info("Start Postgres testcontainer for the entire pytest session.")

    global MANAGER
    MANAGER = PGliteManager()
    MANAGER.start()
    dsn = MANAGER.get_connection_string()
    main.DSN = dsn.replace("+psycopg", "")


def pytest_sessionfinish(session, exitstatus):
    logging.info("Stop Postgres testcontainer.")

    global MANAGER
    MANAGER.start()
