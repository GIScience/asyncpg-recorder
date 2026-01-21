"""Test interplay between asyncpg-recorder and VCR.py.

Using vcr.py cassette along side asyncpg_recorder cassette resulted in
indefinitely waiting for testcontainer to be ready. Solved by keeping container
state in plugin.py.
"""

import urllib.request

import pytest
import vcr
from vcr.record_mode import RecordMode

from asyncpg_recorder import use_cassette
from tests import main

pytestmark = pytest.mark.asyncio


@use_cassette
@vcr.use_cassette(
    path="tests/test_vcr_alongside_asyncpg_recorder.vcr",
    record_mode=RecordMode.NONE,
)
async def test_vcr_alongside_asyncpg_recorder():
    async def select_version():
        return await main.select_version_connect_fetch()

    def get_domains():
        return urllib.request.urlopen("http://www.iana.org/domains/reserved").read()

    db_results = await select_version()
    assert db_results[0]["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"
    assert db_results[0][0] == "15.13 (Debian 15.13-1.pgdg120+1)"
    get_domains()


# Make sure order of wrapper does not matter
@vcr.use_cassette(
    path="tests/test_vcr_alongside_asyncpg_recorder.vcr",
    record_mode=RecordMode.NONE,
)
@use_cassette
async def test_vcr_alongside_asyncpg_recorder_2():
    async def select_version():
        return await main.select_version_connect_fetch()

    def get_domains():
        return urllib.request.urlopen("http://www.iana.org/domains/reserved").read()

    db_results = await select_version()
    assert db_results[0]["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"
    assert db_results[0][0] == "15.13 (Debian 15.13-1.pgdg120+1)"
    get_domains()
