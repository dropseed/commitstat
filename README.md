# commitstat

A CI tool for reporting and comparing stats on commits and pull requests.
It can parse a stat from a file or stdin,
check whether the number has increased or decreased from the previous commit or main branch,
and then report a pass/fail status on GitHub.

```console
$ commitstat coverage-report.txt --regex "\| Total\s*\|\s*([\d\.]+%)" --goal increase --name coverage
```

Can be used to check test coverage, typing coverage, file sizes, and more.
The status can be purely informative, or be set as a required status check (via GitHub branch protection) to ensure that something like test coverage doesn't get worse because of a pull request.

This is a lightweight alternative to hosted services like [Codecov](https://about.codecov.io/) and [Coveralls](https://coveralls.io/).
All of the data that commitstat uses is stored directly in the GitHub commit status and doesn't involve any third-party services or hosting.
There aren't any visualization tools built-in but you can always store artifacts in your CI provider or look at coverage reports locally.

![commitstat-example](https://user-images.githubusercontent.com/649496/121426939-c166f100-c939-11eb-8061-f97cf0f10407.png)

## Quick install

You can install commitstat locally to test your parsing patterns, but commit statuses will only be created when run in CI.

```console
$ curl https://raw.githubusercontent.com/dropseed/commitstat/master/install.sh | bash -s -- -b $HOME/bin
```

## GitHub Action

You can run commitstat right after your tests and once you have some sort of stat to parse.

```yml
name: test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v2

      # Run your tests, generate coverage files, etc.

      - name: Install commitstat
        run: curl https://raw.githubusercontent.com/dropseed/commitstat/master/install.sh | bash -s -- -b $HOME/bin

      - name: Run commitstat
        run: $HOME/bin/commitstat coverage-report.txt --regex "\| Total\s*\|\s*([\d\.]+%)" --goal increase --name coverage
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Example uses

### mypy

Parse the [mypy](https://mypy.readthedocs.io/en/stable/command_line.html#report-generation) imprecision text report (lower number is better).

```console
$ mypy src --ignore-missing-imports --no-incremental --txt-report ./.reports/mypy
$ commitstat .reports/mypy/index.txt --regex "\| Total\s*\|\s*([\d\.]+%)" --goal decrease --name mypy
```

### pytest-cov

Parse the [pytest-cov](https://github.com/pytest-dev/pytest-cov) default HTML report for the total coverage percentage.

```console
$ pytest --cov=src --cov-report=html:.reports/src/pytest src
$ commitstat .reports/pytest/index.html --regex "<span class=\"pc_cov\">(\d+%)<\/span>" --goal increase --name pytest
```

### Go test coverage

Parse total test coverage from the [built-in go coverage tool](https://blog.golang.org/cover).

```console
$ go test ./... -coverprofile=coverage.out
$ go tool cover -func coverage.out | commitstat - --regex "total:\s+\(statements\)\s+([\d\.]+%)" --goal increase --name coverage
```
