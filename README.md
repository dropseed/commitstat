# commitstat

A CI tool for reporting and comparing stats on commits. It can parse a stat from a file or stdin, check whether the number has increased or decreased, and then report a pass/fail status.

Can be used to check test coverage, typing coverage, file sizes, and more.

```console
$ commitstat coverage-report.txt --regex "\| Total\s*\|\s*([\d\.]+%)" --goal increase --name coverage
```

```console
$ stat -f %z app.zip | commitstat - --name app-size
```
