import click
from sparklines import sparklines

from collections import OrderedDict


class CommitStats:
    def __init__(self):
        self.stats = {}  # Keep a reference to stats by key
        self.commits = []  # Keep an ordered list of commits

    def append_commit(self, commit):
        self.commits.append(commit)

    def add_or_update(self, *, commit, key, value, type):
        self.stats.setdefault(key, CommitStat(type=type)).add_or_update(commit, value)

    def print(self, values_only=False, sep="\t"):
        if not values_only:
            print("commit", end=sep)
            for key in self.stats.keys():
                print(key, end=sep)
            print()

        for commit in self.commits:
            if not values_only:
                print(commit, end=sep)

            for stat in self.stats.values():
                print(stat.get(commit), end=sep)
            print()

    def sparklines(self):
        for key, stat in self.stats.items():
            click.secho(
                f"{click.style(key, bold=True)} "
                + f"(min {stat.min()}, max {stat.max()}, avg {stat.avg()})"
            )
            for s in sparklines(stat.commit_values.values()):
                print(s)
            print()

    def get(self, key, commit):
        return self.stats[key].get(commit)

    def commit_has_stat(self, commit, key):
        key_exists = key in self.stats
        commit_has_value = commit in self.stats[key].commit_values
        return key_exists and commit_has_value

    def commits_missing_stats(self, keys):
        """Get a list of commits where any of the given stat keys are missing"""
        commits = []

        for commit in self.commits:
            for key in keys:
                if not self.commit_has_stat(commit, key):
                    commits.append(commit)
                    break

        return commits


class CommitStat:
    """A single stat for multiple commits, stored by commit sha"""

    def __init__(self, type="number"):
        # self.key = key  # doesn't need to know this?
        self.commit_values = OrderedDict()
        self.type = type

    def parse_value(self, value):
        if isinstance(value, str):
            # Strip whitespace
            value = value.strip()

            if self.type == "%":
                value = value.rstrip("%")

            if "." in value:
                value = float(value)
            else:
                value = int(value)

        return value

    def add_or_update(self, commit, value):
        try:
            self.commit_values[commit] = self.parse_value(value)
        except ValueError:
            print(
                f'Could not parse value "{value}" on commit {commit}. '
                + 'Setting value to "missing".'
            )

    def get(self, commit):
        return self.commit_values[commit]

    def min(self):
        v = min(self.commit_values.values())
        return self.format_value(v)

    def max(self):
        v = max(self.commit_values.values())
        return self.format_value(v)

    def avg(self):
        avg = sum(self.commit_values.values()) / len(self.commit_values.values())
        avg = round(avg, 2)
        return self.format_value(avg)

    def format_value(self, value):
        if self.type == "%":
            return f"{value}%"
        return value
