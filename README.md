# commitstat

A lightweight tool to store metrics and stats directly in your git repo as [git notes](https://git-scm.com/docs/git-notes).

The easiest way to install this for yourself or in CI is with [pipx](https://pypa.github.io/pipx/):

```console
$ pipx install git+https://github.com/dropseed/commitstat@git-stats
```

The tool is then available as:

```console
$ git stats
Usage: git-stats [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  ci      All-in-one fetch, save, push
  clear   Delete all existing stats
  delete  Delete a single stat
  fetch   Fetch stats from remote
  log     Log stats for commits matching git log args
  push    Push stats to remote
  regen   Regenerate stats for all commits matching git log args (using...
  save    Save a stat for a commit
  show    Show stats for a commit
  test    Output stats but don't save them
```

Stats are generated by running shell commands.
You can save the names of your stats and their commands in `commitstat.yml`:

```yaml
# commitstat.yml
stats:
  todos:
    run: |
      grep "TODO" -r app -c | awk -F: '{sum+=$NF} END {print sum}'
  num-python-deps:
    run: |
      grep "\[\[package\]\]" poetry.lock -c
  coverage:
    default: 0%
    run: |
      if [ "$CI" != "true" ]; then
        # Don't need to run the test itself in CI (already ran)
        poetry run coverage -m pytest > /dev/null
      fi
      poetry run coverage report | tail -n 1 | awk '{print $4}'
```

To test your stats on your working directory, run:

```console
$ git stats test
```

You can `save` and `push` stats locally,
but typically you'll have this running in CI automatically:

```yaml
name: test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    # ...
    - run: pipx run --spec git+https://github.com/dropseed/commitstat@git-stats git-stats ci

```

By default, `ci` will try to also regenerate any missing stats for the latest 10 commits (useful if you push multiple commits at once).

But in order for this to work, you need more commits accessible in CI (TODO can you log off the git remote?). In GitHub Actions, you can use `fetch-depth` to do this:

```yaml
name: test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 10
    # ...
    - run: pipx run --spec git+https://github.com/dropseed/commitstat@git-stats git-stats ci
```

You can also send the stats to the GitHub Actions summary:

```yaml
name: test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 10
    # ...
    - run: |
        pipx install git+https://github.com/dropseed/commitstat@git-stats
        git stats ci

        echo "## Commit Stats" >> "$GITHUB_STEP_SUMMARY"
        echo '```' >> "$GITHUB_STEP_SUMMARY"
        git stats log --format sparklines --reverse >> "$GITHUB_STEP_SUMMARY"
        echo '```' >> "$GITHUB_STEP_SUMMARY"

```

## Retroactive stats

You're probably introducing this into an existing project,
and will want to generate some stats for existing commits.

To do that, use:

```console
$ git stats regen
```

You can specify a key(s) with `git stats regen --key todos`,
and any additional options will be used to select the commits to regenerate stats for (via `git log`).
So, you can regenerate stats for the latest 50 commits with:

```console
$ git stats regen -n 50
```

## Sparklines

```console
$ git stats fetch
$ git stats log --key todos --values-only -n 50 --reverse --format sparklines
todos (min 0, max 43, avg 25.4)
▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▇▇▇███████████████████████████████
```
