# Asyncpg Recorder

[![Build Status](https://jenkins.heigit.org/buildStatus/icon?job=asyncpg-recorder/main)](https://jenkins.heigit.org/job/asyncpg-recorder/job/main/)
[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=asyncpg-recorder&metric=alert_status)](https://sonarcloud.io/dashboard?id=asyncpg-recorder)
[![PyPI - Version](https://img.shields.io/pypi/v/asyncpg-recorder)](https://pypi.org/project/asyncpg-recorder/)
[![LICENSE](https://img.shields.io/github/license/GIScience/asyncpg-recorder)](COPYING)
[![status: active](https://github.com/GIScience/badges/raw/master/status/active.svg)](https://github.com/GIScience/badges#active)

## Installation

```bash
uv add asyncpg-recorder
```

## Usage

```python
import asyncpg
from asyncpg_recorder import use_cassette


async def query():
    con = await asyncpg.connect(DSN)
    res = await con.fetch("SELECT NOW();")
    await con.close()
    return res


@use_cassette
def test_select_now_replay():
    query()
```

When using pytest parametrized fixtures put the `@use_cassette` decorator on the test function not the fixture:

```python
import asyncpg
from asyncpg_recorder import use_cassette
import pytest
import pytest_asyncio


@pytest_asyncio.fixture(params=[False, True])
async def param(request):
    return request.param


@pytest.mark.asyncio
@pytest.mark.usefixtures("param")
@use_cassette
async def test_parametrized_fixtures(path):
    async def query():
      con = await asyncpg.connect(DSN)
      res = await con.fetch("SELECT NOW();")
      await con.close()
      return res

    await select_version()
```

If you want to save the cassettes in a specific directory, set the variable cassettes-dir in your pyproject.toml.
The path should be relative to pyproject.toml.

```toml
[tool.asyncpg-recorder]
"cassettes-dir"="tests/cassettes"
```

## Development

### Tests

```bash
uv run pre-commit install
uv run pytest
```

### Release

This project uses [SemVer](https://semver.org/).

To make a new release run `./scripts/release.sh <version number>`.


## Limitation

- Works only with pytest
- Depends on [testcontainers](https://testcontainers-python.readthedocs.io/)
  - Testcontainers is used to boot up a temporary Postgres instance to which asyncpg will be connected.
  - This slows test suite down.
