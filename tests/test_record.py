import datetime
import json
import sys
from pathlib import Path

import pytest
import pytest_asyncio
import vcr
from asyncpg import Record

from asyncpg_recorder import use_cassette
from tests import main

# Marks all test coroutines in this module
pytestmark = pytest.mark.asyncio

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.usefixtures("postgres")
async def test_select_now_with_database():
    """No `use_cassette` decorator. Database is reachable."""
    result = await main.select_now()
    assert isinstance(result[0]["now"], datetime.datetime)
    assert isinstance(result[0], Record)


@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_select_version_fetchrow(path_json):
    async def select_version():
        return await main.select_version_connect_fetchrow()

    assert not path_json.exists()
    result = await select_version()
    assert path_json.exists()

    if sys.version_info[0] == 3 and sys.version_info[1] < 14:
        hash_ = "342758293"
    else:
        hash_ = "1603757252"

    with open(path_json) as file:
        cassette = json.load(file)
    assert result["server_version"] == cassette[hash_]["results"][0]["server_version"]
    assert result[0] == cassette[hash_]["results"][0]["server_version"]
    assert isinstance(result, Record)


@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_select_version_fetchrow_with_query_logger(path_json):
    async def select_version():
        return await main.select_version_connect_fetchrow_with_query_logger()

    assert not path_json.exists()
    result = await select_version()
    assert path_json.exists()

    if sys.version_info[0] == 3 and sys.version_info[1] < 14:
        hash_ = "342758293"
    else:
        hash_ = "1603757252"

    with open(path_json) as file:
        cassette = json.load(file)
    assert result["server_version"] == cassette[hash_]["results"][0]["server_version"]
    assert result[0] == cassette[hash_]["results"][0]["server_version"]
    assert isinstance(result, Record)


@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_select_version_fetch(path_json):
    async def select_version():
        return await main.select_version_connect_fetch()

    assert not path_json.exists()
    result = await select_version()
    assert path_json.exists()

    if sys.version_info[0] == 3 and sys.version_info[1] < 14:
        hash_ = "820789923"
    else:
        hash_ = "2064987634"

    with open(path_json) as file:
        cassette = json.load(file)
    assert (
        result[0]["server_version"] == cassette[hash_]["results"][0]["server_version"]
    )
    assert result[0][0] == cassette[hash_]["results"][0]["server_version"]
    assert isinstance(result[0], Record)


@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_select_now_pickle(path_pickle):
    async def select_now():
        return await main.select_now()

    assert not path_pickle.exists()
    result = await select_now()
    assert path_pickle.exists()
    assert isinstance(result[0], Record)
    assert isinstance(result[0]["now"], datetime.datetime)
    assert isinstance(result[0][0], datetime.datetime)


@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_multiple_calls_with_same_cassette(path_json: Path):
    async def query_1():
        return await main.select_version_connect_fetch()

    async def query_2():
        return await main.select_version_connect_fetchrow()

    # assert not path.exists()
    await query_1()
    with open(path_json, "r") as file:
        cassette_1 = json.load(file)

    await query_2()
    with open(path_json, "r") as file:
        cassette_2 = json.load(file)

    assert cassette_1 != cassette_2
    assert set(cassette_1.keys()).issubset(set(cassette_2.keys()))


@pytest.mark.parametrize("param", ["foo", "bar"])
@pytest.mark.usefixtures("postgres")
@use_cassette
async def test_parametrized_with_same_cassette(param: str, path_json: Path):
    async def query(param: str):
        return await main.select_version_connect_fetch()

    await query(param)
    if param == "foo":
        with open(path_json, "r") as file:
            cassette = json.load(file)
        assert len(cassette.keys()) == 1
    if query == "bar":
        with open(path_json, "r") as file:
            cassette = json.load(file)
        assert len(cassette.keys()) == 2


@pytest.mark.usefixtures("postgres")
@vcr.use_cassette
@use_cassette
async def test_select_version_fetch_with_vcr_cassette(path_json):
    # Using vcr.py cassette along side asyncpg_recorder cassette resulted in
    # indefinitely waiting for testcontainer to be ready. Solved by keeping container
    # state in plugin.py.
    async def select_version():
        return await main.select_version_connect_fetch()

    assert not path_json.exists()
    await select_version()
    assert path_json.exists()


@pytest_asyncio.fixture(params=[False, True])
async def param(request):
    return request.param


@pytest.mark.usefixtures("postgres", "param")
@use_cassette
async def test_parametrized_fixtures(path_json):
    async def select_version():
        return await main.select_version_connect_fetch()

    assert not path_json.exists()
    await select_version()
    assert path_json.exists()


@pytest.mark.asyncio(loop_scope="class")
class TestParametrizedFixtureUseCassetteOnTest:
    @pytest_asyncio.fixture(params=[False, True], loop_scope="class")
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    @use_cassette
    async def test(self, path_json):
        async def select_version():
            return await main.select_version_connect_fetch()

        assert not path_json.exists()
        await select_version()
        assert path_json.exists()


@pytest.mark.skip("Not supported.")
@pytest.mark.asyncio(loop_scope="class")
class TestParametrizedFixtureUseCassetteOnFixture:
    @pytest_asyncio.fixture(params=[False, True], loop_scope="class")
    @use_cassette
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    async def test(self, path_json):
        async def select_version():
            return await main.select_version_connect_fetch()

        assert not path_json.exists()
        await select_version()
        assert path_json.exists()


@pytest.mark.skip("Not supported.")
class TestParametrizedFixtureUseCassetteOnTestLoopScopeDefault:
    @pytest_asyncio.fixture(params=[False, True])
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    @use_cassette
    async def test(self, path_json):
        async def select_version():
            return await main.select_version_connect_fetch()

        assert not path_json.exists()
        await select_version()
        assert path_json.exists()


@pytest.mark.asyncio(loop_scope="class")
class TestParametrizedFixtureUseCassetteOnTestButQueryDbInFixture:
    @pytest_asyncio.fixture(params=[False, True], loop_scope="class")
    @use_cassette
    async def param(self, request):
        async def select_version():
            return await main.select_version_connect_fetch()

        await select_version()
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    @use_cassette
    async def test(self, path_json):
        assert path_json.exists()
