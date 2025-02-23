"""Cassettes are present. Database is not reachable."""

import datetime
from tests import main
from asyncpg_recorder import use_cassette

import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
@use_cassette(FIXTURE_DIR / "now.pickle")
async def test_select_now():
    results = await main.select_now()
    assert isinstance(results[0]["now"], datetime.datetime)
    assert results[0]["now"] == datetime.datetime(
        2025, 8, 18, 12, 7, 15, 642678, tzinfo=datetime.timezone.utc
    )
    # assert isinstance(result[0], Record)


@pytest.mark.asyncio
@use_cassette(FIXTURE_DIR / "version.json")
async def test_select_version():
    results = await main.select_version_connect_fetch()
    assert isinstance(results[0]["server_version"], str)
    assert results[0]["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"


@pytest.mark.asyncio
async def test_multiple_calls_with_same_cassette():
    @use_cassette(FIXTURE_DIR / "multiple_calls_with_same_cassette.pickle")
    async def query_1():
        return await main.select_version_connect_fetch()

    @use_cassette(FIXTURE_DIR / "multiple_calls_with_same_cassette.pickle")
    async def query_2():
        return await main.select_version_connect_fetchrow()

    await query_1()
    await query_2()
