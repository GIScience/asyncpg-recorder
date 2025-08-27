import logging

from testcontainers.postgres import PostgresContainer

from asyncpg_recorder import main


POSTGRES: PostgresContainer


def pytest_sessionstart(session):
    logging.info("Start Postgres testcontainer for the entire pytest session.")

    global POSTGRES
    POSTGRES = PostgresContainer("postgres").start()
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
