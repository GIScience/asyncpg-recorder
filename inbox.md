# Inbox

## Features

- [ ] Add tests for all asyncpg fetch functions
- [ ] Make it work with asyncpg pooling


## Improvements

- [x] Spin up one testcontainer instance per session to avoid spinning up a new testcontainer for each usage of `use_cassette`
- [x] Use pytest node id to generate cassette names
- [ ] Get rid of testcontainers
  - Maybe use https://github.com/jackc/pgmock to find out what kind of requests are made during connection using asyncpg
  - Connection wrapper for `asyncpg_recorder` could take everything and return whatever asyncpg needs
- [ ] Make it work with pytest-xdist (share one testcontainer across workers)
- [ ] Disable usage of cassettes (during development work in case a real database is available.)
- [ ] Get rid of pickle
- [ ] Make pytest optional
- [ ] If a function deeper than `_execute` is wrapped will results be just text (not yet converted to Python types?). This will make serialization trivial.


## Build

- [x] CI
- [x] License
- [x] Pypi
