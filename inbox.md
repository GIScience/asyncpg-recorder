# Inbox

## Features

- [ ] Add tests for all asyncpg fetch functions
- [ ] Make it work with asyncpg pooling


## Improvements

- [x] Spin up one testcontainer instance per session to avoid spinning up a new testcontainer for each usage of `use_cassette`
- [x] Use pytest node id to generate cassette names
- [ ] Get rid of testcontainers
- [ ] Get rid of pickle
- [ ] If a function deeper than `_execute` is wrapped will results be just text (not yet converted to Python types?). This will make serialization trivial.


## Build

- [ ] CI
- [ ] License
- [ ] Pypi
