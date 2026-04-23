"""Set of functions for testing.

They differ in how connection is established to the Postgres database and which
SQL execution function is called.
"""

import logging

import asyncpg

logger = logging.getLogger(__name__)
# DSN in libpq connection URI format
DSN = ""


async def select_now():
    con = await asyncpg.connect(DSN)
    res = await con.fetch("SELECT NOW();")
    await con.close()
    return res


async def select_version_connect_fetch() -> list[asyncpg.Record]:
    con = await asyncpg.connect(DSN)
    res = await con.fetch("SHOW server_version")
    await con.close()
    return res


async def select_version_connect_fetchrow() -> asyncpg.Record:
    con = await asyncpg.connect(DSN)
    res = await con.fetchrow("SHOW server_version")
    await con.close()
    return res


async def select_version_connect_fetchrow_with_query_logger() -> asyncpg.Record:
    con = await asyncpg.connect(DSN)
    with con.query_logger(lambda record: logger.info(record)):
        res = await con.fetchrow("SHOW server_version")
    await con.close()
    return res


async def select_version_pool_fetch():
    pass


async def select_version_pool_fetchrow():
    pass
