import datetime
import pickle
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
async def test_unsupported_file_type():
    with pytest.raises(ValueError):

        @use_cassette("cassette.yaml")
        async def _():
            pass


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_version_fetchrow(tmp_cassette_json: Path):
    @use_cassette(tmp_cassette_json)
    async def select_version():
        return await main.select_version_connect_fetchrow()

    assert not tmp_cassette_json.exists()
    result = await select_version()
    assert tmp_cassette_json.exists()

    with open(tmp_cassette_json) as file:
        cassette = json.load(file)

    assert (
        result["server_version"]
        == cassette["342758293"]["results"][0]["server_version"]
    )
    # assert isinstance(cassette["result"], Record)


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_version_fetch(tmp_cassette_json: Path):
    @use_cassette(tmp_cassette_json)
    async def select_version():
        return await main.select_version_connect_fetch()

    assert not tmp_cassette_json.exists()
    result = await select_version()
    assert tmp_cassette_json.exists()

    with open(tmp_cassette_json) as file:
        cassette = json.load(file)

    assert (
        result[0]["server_version"]
        == cassette["820789923"]["results"][0]["server_version"]
    )
    # assert isinstance(cassette["result"][0], Record)


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_now_pickle(tmp_cassette_pickle: Path):
    @use_cassette(tmp_cassette_pickle)
    async def select_now():
        return await main.select_now()

    assert not tmp_cassette_pickle.exists()
    await select_now()
    assert tmp_cassette_pickle.exists()


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_select_now_json(tmp_cassette_json: Path):
    @use_cassette(tmp_cassette_json)
    async def select_now():
        return await main.select_now()

    # TODO: raise custom error with helpful description
    with pytest.raises(TypeError):
        await select_now()


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres")
async def test_multiple_calls_with_same_cassette(tmp_cassette_pickle: Path):
    @use_cassette(tmp_cassette_pickle)
    async def query_1():
        return await main.select_version_connect_fetch()

    @use_cassette(tmp_cassette_pickle)
    async def query_2():
        return await main.select_version_connect_fetchrow()

    assert not tmp_cassette_pickle.exists()

    await query_1()
    with open(tmp_cassette_pickle, "rb") as file:
        cassette_1 = pickle.load(file)

    await query_2()
    with open(tmp_cassette_pickle, "rb") as file:
        cassette_2 = pickle.load(file)

    assert cassette_1 != cassette_2
    assert set(cassette_1.keys()).issubset(set(cassette_2.keys()))
