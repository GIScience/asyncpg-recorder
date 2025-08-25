import datetime
from tests import main
from asyncpg_recorder import use_cassette

from asyncpg import Record
import pytest
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_now_with_database():
    """No `use_cassette` decorator. Database is reachable."""
    result = await main.select_now()
    assert isinstance(result[0]["now"], datetime.datetime)
    assert isinstance(result[0], Record)


@pytest.mark.asyncio
async def test_select_now_without_database():
    """No `use_cassette` decorator. Database is not reachable."""
    with pytest.raises(ValueError):
        await main.select_now()


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_version_fetchrow(path):
    @use_cassette
    async def select_version():
        return await main.select_version_connect_fetchrow()

    path = path.with_suffix(".json")
    assert not path.exists()
    result = await select_version()
    assert path.exists()

    with open(path) as file:
        cassette = json.load(file)

    assert (
        result["server_version"]
        == cassette["342758293"]["results"][0]["server_version"]
    )
    # assert isinstance(cassette["result"], Record)


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_version_fetch(path):
    @use_cassette
    async def select_version():
        return await main.select_version_connect_fetch()

    path = path.with_suffix(".json")
    assert not path.exists()
    result = await select_version()
    assert path.exists()

    with open(path) as file:
        cassette = json.load(file)

    assert (
        result[0]["server_version"]
        == cassette["820789923"]["results"][0]["server_version"]
    )
    # assert isinstance(cassette["result"][0], Record)


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_now_pickle(path):
    @use_cassette
    async def select_now():
        return await main.select_now()

    path = path.with_suffix(".pickle")
    assert not path.exists()
    await select_now()
    assert path.exists()


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_multiple_calls_with_same_cassette(path: Path):
    @use_cassette
    async def query_1():
        return await main.select_version_connect_fetch()

    @use_cassette
    async def query_2():
        return await main.select_version_connect_fetchrow()

    path = Path(path).with_suffix(".json")
    # assert not path.exists()
    await query_1()
    with open(path, "r") as file:
        cassette_1 = json.load(file)

    await query_2()
    with open(path, "r") as file:
        cassette_2 = json.load(file)

    assert cassette_1 != cassette_2
    assert set(cassette_1.keys()).issubset(set(cassette_2.keys()))
