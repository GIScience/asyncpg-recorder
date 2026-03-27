# CHANGELOG

## Release 0.8.0

- fix: request postgres only for pytest items which are functions (4fc691d)

## Release 0.7.0

* tests/docs: handle different hashes due to different Python version (af1db0f)
    * The same database request on Python >= 3.14 yields a different hash for cassette entry than on Python <= 3.13. If it is important to run tests against both Python version ranges you need to record twice.

## Release 0.6.0

* fix(name): create parent directories but not filename as directory (547908e)
    * This avoids creation of empty directories with names ending in `.raw`

## Release 0.5.0

### Breaking Changes

* support Python 3.11 and bump asyncpg version to greater equals 0.31 (5598199)
    * Please re-create all cassettes. Cassette entry hashes changed after asyncpg version bump.

## Release 0.4.0

* build/tests: add pytest-randomly to run tests in random order (fe71b0f)
* build: migrate pre-commit hooks to prek (82c44f9)
* build: upgrade dependencies (d3fd87e)
* fix: resolve cassette file name as late as possible (d8f53b1)

## Release 0.3.0

- fix: create sub-directories in cassette directory during nameing of cassette file (f73ec93)

## Release 0.2.0

- feat: make test run faster if now aysncpg-recorder usage found by starting postgres testcontainer only if @use_cassette is in use (4a808f8)
