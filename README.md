# Asyncpg Recorder

## Installation

```bash
uv add git+https://github.com/GIScience/asyncpg-recorder.git
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


## Development

### Tests

```bash
uv run pytest
```

### Release

This project uses [CalVer](https://calver.org/).

Format is: `YYYY.MM.DD` (E.g `2025.9.2`).

In case of releasing twice on one day add a micro number starting with 1: `YYYY.MM.DD_micro` (E.g. `2025.9.2_1`).


## Limitation

- Works only with pytest
- Depends on [testcontainers](testcontainers-python.readthedocs.io/) 
  - Testcontainers is used to boot up a temporary Postgres instance to which asyncpg will be connected.
  - This slows test suite down.


## Inbox

See [inbox.md](/inbox.md)

