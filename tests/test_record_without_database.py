import pytest

import asyncpg_recorder
from tests import main

pytestmark = pytest.mark.asyncio


@asyncpg_recorder.use_cassette
async def test_select_now_without_database():
    """No `use_cassette` decorator. Database is not reachable."""
    with pytest.raises(OSError):
        await main.select_now()
