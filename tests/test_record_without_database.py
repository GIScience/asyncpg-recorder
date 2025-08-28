import pytest

from tests import main


async def test_select_now_without_database():
    """No `use_cassette` decorator. Database is not reachable."""
    with pytest.raises(ValueError):
        await main.select_now()
