import pytest

from tests import main

pytestmark = pytest.mark.asyncio


async def test_select_now_without_database():
    """No `use_cassette` decorator. Database is not reachable."""
    with pytest.raises(OSError):
        await main.select_now()
