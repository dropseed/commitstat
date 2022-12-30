class CommitStats:
    def __init__(self):
        self.stats = {}  # Keep a reference to stats by key
        self.commits = []  # Keep an ordered list of commits

    def append_commit(self, commit):
        self.commits.append(commit)

    def add(self, *, commit, key, value, default_value):
        self.stats.setdefault(key, CommitStat(default_value=default_value)).add(
            commit, value
        )

    def print(self, values_only=False, delimiter="\t"):
        if not values_only:
            print("commit", end=delimiter)
            for key in self.stats.keys():
                print(key, end=delimiter)
            print()

        for commit in self.commits:
            if not values_only:
                print(commit, end=delimiter)

            for stat in self.stats.values():
                print(stat.get(commit), end=delimiter)
            print()


class CommitStat:
    """A single stat for multiple commits, stored by commit sha"""

    def __init__(self, default_value=""):
        # self.key = key  # doesn't need to know this?
        self.commit_values = {}
        self.default_value = default_value

    def add(self, commit, value):
        value = value.strip()  # Strip whitespace
        # TODO parse units?
        self.commit_values[commit] = value

    def get(self, commit):
        return self.commit_values.get(commit, self.default_value)
