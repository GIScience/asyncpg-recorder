import logging

from testcontainers.postgres import PostgresContainer

from asyncpg_recorder import main


def pytest_sessionstart(session):
    logging.info("Start Postgres testcontainer for the entire pytest session.")
    main.POSTGRES = PostgresContainer("postgres").start()


def pytest_sessionfinish(session, exitstatus):
    logging.info("Stop Postgres testcontainer.")
    main.POSTGRES.stop()
