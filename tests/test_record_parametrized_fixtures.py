import pytest
import pytest_asyncio

from asyncpg_recorder import use_cassette
from tests import main


@pytest_asyncio.fixture(params=[False, True])
async def param(request):
    return request.param


@pytest.mark.asyncio
@pytest.mark.usefixtures("postgres", "param")
@use_cassette
async def test_parametrized_fixtures(path):
    async def select_version():
        return await main.select_version_connect_fetch()

    path = path.with_suffix(".pickle")
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

        path = path.with_suffix(".pickle")
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

        path = path.with_suffix(".pickle")
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

        path = path.with_suffix(".pickle")
        assert not path.exists()
        await select_version()
        assert path.exists()
