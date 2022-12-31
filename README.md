# commitstat

A lightweight tool to store metrics and stats directly in your git repo as [git notes](https://git-scm.com/docs/git-notes).

The easiest way to install this for yourself or in CI is with [pipx](https://pypa.github.io/pipx/):

```console
pipx install git+https://github.com/dropseed/commitstat@git-stats
```

The tool is then available as:

```console
$ git stats
Usage: git-stats [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  clear   Delete all existing stats
  delete  Delete a single stat
  fetch   Fetch stats from remote
  log     Log stats for commits matching git log args
  push    Push stats to remote
  regen   Regenerate stats for all commits matching git log args
  save    Save a stat for a commit
  show    Show stats for a commit
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
      poetry run coverage -m pytest > /dev/null
      poetry run coverage report --data-file .forge/.coverage | tail -n 1 | awk '{print $4}'
```
