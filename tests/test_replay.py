"""Cassettes are present. Database is not reachable.

Cassettes have been recorded by adding the `postgres` fixture to the tests for one run.
"""

import datetime
from tests import main
from asyncpg_recorder import use_cassette

import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
@use_cassette
async def test_select_now():
    results = await main.select_now()
    assert isinstance(results[0]["now"], datetime.datetime)
    assert results[0]["now"] == datetime.datetime(
        2025, 8, 25, 10, 2, 4, 438553, tzinfo=datetime.timezone.utc
    )
    # assert isinstance(result[0], Record)


@pytest.mark.asyncio
@use_cassette
async def test_select_version():
    results = await main.select_version_connect_fetch()
    assert isinstance(results[0]["server_version"], str)
    assert results[0]["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"
    # assert isinstance(result[0], Record)


@pytest.mark.asyncio
@use_cassette
async def test_multiple_calls_with_same_cassette():
    async def query_1():
        return await main.select_version_connect_fetch()

    async def query_2():
        return await main.select_version_connect_fetchrow()

    await query_1()
    await query_2()
