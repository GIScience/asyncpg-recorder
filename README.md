# Asyncpg Recorder

## Installation

```bash
uv add git+https://gitlab.heigit.org/mschaub/asyncpg-recorder
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

## Development

### Tests

```bash
uv run pytest
```

## Inbox

See [inbox.md](/inbox.md)

