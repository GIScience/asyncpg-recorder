"""Cassettes are present. Database is not reachable.

Cassettes have been recorded by adding the `postgres` fixture to the tests for one run.
"""

import datetime
import sys
from pathlib import Path

import pytest
from asyncpg import Record

from asyncpg_recorder import use_cassette
from tests import main

FIXTURE_DIR = Path(__file__).parent / "fixtures"


pytestmark = pytest.mark.asyncio


@use_cassette
async def test_select_version_fetch():
    results = await main.select_version_connect_fetch()
    assert isinstance(results[0], Record)
    assert results[0]["server_version"] == "18.3 (Debian 18.3-1.pgdg13+1)"
    assert results[0][0] == "18.3 (Debian 18.3-1.pgdg13+1)"


@use_cassette
async def test_select_version_fetchrow():
    results = await main.select_version_connect_fetchrow()
    assert isinstance(results, Record)
    assert results["server_version"] == "18.3 (Debian 18.3-1.pgdg13+1)"
    assert results[0] == "18.3 (Debian 18.3-1.pgdg13+1)"


@use_cassette
async def test_select_now():
    results = await main.select_now()
    assert isinstance(results[0], Record)

    # different cassette entries are used for different Python versions
    if sys.version_info[0] == 3 and sys.version_info[1] < 14:
        expected = datetime.datetime(
            2026, 3, 26, 6, 31, 6, 833132, tzinfo=datetime.timezone.utc
        )
    else:
        expected = datetime.datetime(
            2026, 3, 26, 5, 42, 45, 76056, tzinfo=datetime.timezone.utc
        )
    assert results[0]["now"] == expected
    assert results[0][0] == expected


@use_cassette
async def test_multiple_calls_with_same_cassette():
    async def query_1():
        return await main.select_version_connect_fetch()

    async def query_2():
        return await main.select_version_connect_fetchrow()

    await query_1()
    await query_2()


# TODO:
async def test_empty_cassette_present():
    pass
