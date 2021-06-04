# commitstat

A CI tool for reporting and comparing stats on commits. It can parse a stat from a file or stdin, check whether the number has increased or decreased, and then report a pass/fail status.

Can be used to check test coverage, typing coverage, file sizes, and more.

```console
$ commitstat coverage-report.txt --regex "\| Total\s*\|\s*([\d\.]+%)" --goal increase --name coverage
```

```console
$ stat -f %z app.zip | commitstat - --name app-size
```

## Quick install

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
