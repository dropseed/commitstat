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

![commitstat on pull request checks](https://user-images.githubusercontent.com/649496/121754532-7df7b880-cada-11eb-8b0a-7457f0bb0ed8.png)

## Quick install

You can install commitstat locally to test your parsing patterns, but commit statuses will only be created when run in CI.

```console
$ curl https://raw.githubusercontent.com/dropseed/commitstat/master/install.sh | bash -s -- -b $HOME/bin
```

## Options

### `--name`

The name of the stat.
Will show up as `commitstat/{name}` when submitted as a GitHub commit status.
Changing the name for an existing stat will break the pass/fail comparison until the new name shows up on your main/master branch.

### `--goal` (optional)

Either "increase" or "decrease". This is the direction you *want* the stat to go. For example, test coverage should "increase" and if it actually decreases, then a failling status will be reported. If the stat is new or doesn't change, it is considered successful.

If you don't specify a goal, then you'll get a successful status and the stat/change will be purely informational.

### `--regex` (optional)

A regular expression to parse the file/stdin for a specific value.
There should be exactly one capture group in your regular expression (using parentheses) and you can include extra characters like a percent sign "%".
The extra characters will simply be removed when comparing the values (ex. "36%" will be interpreted as "36").
You'll receive an error if you mix units (ex. "1mb" and "1gb").

By default commitstat assumes the input is simply a number and a regex isn't needed (ex. `stat --format %s app.zip | commitstat -` on Ubuntu).

## GitHub Action

You can run commitstat right after your tests and once you have some sort of stat to parse.
Use different names to report multiple stats per commit.

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

### File sizes

Report the size of a file (in bytes) using `stat` on Ubuntu (note that the options for stat can differ depending on your OS).

```console
$ stat --format %s app.zip | commitstat -
```

## How it works

Stats are stored directly in GitHub through the commit status API.
The stat is always the first number in the description which makes it easy to parse.

<!-- https://excalidraw.com/#json=5675361668956160,KJvEUJXgl5Sw7CV39_-04w -->

![commitstat git](https://user-images.githubusercontent.com/649496/121432738-a9df3680-c940-11eb-9a4f-a5be6e3fb05b.png)
