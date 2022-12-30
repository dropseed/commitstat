import yaml


DEFAULT_FILENAME = "commitstat.yml"


class Config:
    def __init__(self, *, stats):
        self.stats = stats

    @classmethod
    def load_dict(cls, data):
        return cls(stats=data["stats"])

    @classmethod
    def load_yaml(cls, path=DEFAULT_FILENAME):
        with open(path) as f:
            return cls.load_dict(yaml.safe_load(f))

    def stats_keys(self):
        return self.stats.keys()

    def command_for_stat(self, key):
        return self.stats[key]["run"]

    def default_for_stat(self, key):
        return self.stats[key].get("default", 0)
