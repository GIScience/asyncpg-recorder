# CHANGELOG

## Current Main

* build/tests: add pytest-randomly to run tests in random order (fe71b0f)
* build: migrate pre-commit hooks to prek (82c44f9)
* build: upgrade dependencies (d3fd87e)
* fix: resolve cassette file name as late as possible (d8f53b1)

## Release 0.3.0

- fix: create sub-directories in cassette directory during nameing of cassette file (f73ec93)

## Release 0.2.0

- feat: make test run faster if now aysncpg-recorder usage found by starting postgres testcontainer only if @use_cassette is in use (4a808f8)
