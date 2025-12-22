from pathlib import Path

import pytest

from asyncpg_recorder.main import name

pytestmark = pytest.mark.asyncio


async def test_cassette_dir_not_set(monkeypatch):
    monkeypatch.setattr("asyncpg_recorder.main.CASSETTES_DIR", None)
    result = name()

    expected = Path(
        Path(__file__).parent / "test_name.py--test_cassette_dir_not_set.cassette.raw"
    )
    assert result.is_absolute()
    assert result == expected


async def test_cassette_dir_set(monkeypatch):
    path = Path("tests/cassettes")
    monkeypatch.setattr("asyncpg_recorder.main.CASSETTES_DIR", path)
    result = name()
    assert result.is_absolute()
    expected = (
        Path(__file__).parent.parent
        / "cassettes"
        / "name"
        / "test_name.py--test_cassette_dir_set.cassette.raw"
    )
    assert result == expected
    assert result.exists()


async def test_cassette_dir_set_nested(monkeypatch):
    path = Path("tests/name/cassettes")
    monkeypatch.setattr("asyncpg_recorder.main.CASSETTES_DIR", path)
    result = name()
    assert result.is_absolute()
    expected = (
        Path(__file__).parent.parent
        / "name"
        / "cassettes"
        / "test_name.py--test_cassette_dir_set_nested.cassette.raw"
    )
    assert result == expected
    assert result.exists()
