import datetime
import json
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
    assert result[0] == cassette["342758293"]["results"][0]["server_version"]
    assert isinstance(result, Record)


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
    assert result[0][0] == cassette["820789923"]["results"][0]["server_version"]
    assert isinstance(result[0], Record)


@pytest.mark.usefixtures("postgres")
async def test_select_now_pickle(path):
    @use_cassette
    async def select_now():
        return await main.select_now()

    path = path.with_suffix(".pickle")
    assert not path.exists()
    result = await select_now()
    assert path.exists()
    assert isinstance(result[0], Record)
    assert isinstance(result[0]["now"], datetime.datetime)
    assert isinstance(result[0][0], datetime.datetime)


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


@pytest.mark.parametrize("param", ["foo", "bar"])
@pytest.mark.usefixtures("postgres")
async def test_parametrized_with_same_cassette(param: str, path: Path):
    @use_cassette
    async def query(param: str):
        return await main.select_version_connect_fetch()

    await query(param)
    path = Path(path).with_suffix(".json")
    if param == "foo":
        with open(path, "r") as file:
            cassette = json.load(file)
        assert len(cassette.keys()) == 1
    if query == "bar":
        with open(path, "r") as file:
            cassette = json.load(file)
        assert len(cassette.keys()) == 2


@pytest.mark.usefixtures("postgres")
async def test_select_version_fetch_with_vcr_cassette(path):
    # Using vcr.py cassette along side asyncpg_recorder cassette resulted in
    # indefinitely waiting for testcontainer to be ready. Solved by keeping container
    # state in plugin.py.
    @vcr.use_cassette
    @use_cassette
    async def select_version():
        return await main.select_version_connect_fetch()

    path = path.with_suffix(".json")
    assert not path.exists()
    await select_version()
    assert path.exists()


@pytest_asyncio.fixture(params=[False, True])
async def param(request):
    return request.param


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres", "param")
@use_cassette
async def test_parametrized_fixtures(path):
    async def select_version():
        return await main.select_version_connect_fetch()

    path = path.with_suffix(".json")
    assert not path.exists()
    await select_version()
    assert path.exists()


@pytest.mark.asyncio(loop_scope="class")
class TestParametrizedFixtureUseCassetteOnTest:
    @pytest_asyncio.fixture(params=[False, True], loop_scope="class")
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    @use_cassette
    async def test(self, path):
        async def select_version():
            return await main.select_version_connect_fetch()

        path = path.with_suffix(".json")
        assert not path.exists()
        await select_version()
        assert path.exists()


@pytest.mark.skip("Not supported.")
@pytest.mark.asyncio(loop_scope="class")
class TestParametrizedFixtureUseCassetteOnFixture:
    @pytest_asyncio.fixture(params=[False, True], loop_scope="class")
    @use_cassette
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    async def test(self, path):
        async def select_version():
            return await main.select_version_connect_fetch()

        path = path.with_suffix(".json")
        assert not path.exists()
        await select_version()
        assert path.exists()


@pytest.mark.skip("Not supported.")
@pytest.mark.asyncio
class TestParametrizedFixtureUseCassetteOnTestLoopScopeDefault:
    @pytest_asyncio.fixture(params=[False, True])
    async def param(self, request):
        return request.param

    @pytest.mark.usefixtures("postgres", "param")
    @use_cassette
    async def test(self, path):
        async def select_version():
            return await main.select_version_connect_fetch()

        path = path.with_suffix(".json")
        assert not path.exists()
        await select_version()
        assert path.exists()
