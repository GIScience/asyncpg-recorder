"""Cassettes are present. Database is not reachable.

Cassettes have been recorded by adding the `postgres` fixture to the tests for one run.
"""

import datetime
from pathlib import Path

import pytest
from asyncpg import Record

from asyncpg_recorder import use_cassette
from tests import main

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
@use_cassette
async def test_select_version_fetch():
    results = await main.select_version_connect_fetch()
    assert isinstance(results[0], Record)
    assert results[0]["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"
    assert results[0][0] == "15.13 (Debian 15.13-1.pgdg120+1)"


@pytest.mark.asyncio
@use_cassette
async def test_select_version_fetchrow():
    results = await main.select_version_connect_fetchrow()
    assert isinstance(results, Record)
    assert results["server_version"] == "15.13 (Debian 15.13-1.pgdg120+1)"
    assert results[0] == "15.13 (Debian 15.13-1.pgdg120+1)"


@pytest.mark.asyncio
@use_cassette
async def test_select_now():
    results = await main.select_now()
    assert isinstance(results[0], Record)
    assert results[0]["now"] == datetime.datetime(
        2025, 8, 25, 11, 46, 5, 247390, tzinfo=datetime.timezone.utc
    )
    assert results[0][0] == datetime.datetime(
        2025, 8, 25, 11, 46, 5, 247390, tzinfo=datetime.timezone.utc
    )


@pytest.mark.asyncio
@use_cassette
async def test_multiple_calls_with_same_cassette():
    async def query_1():
        return await main.select_version_connect_fetch()

    async def query_2():
        return await main.select_version_connect_fetchrow()

    await query_1()
    await query_2()
