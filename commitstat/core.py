from .stats import CommitStats
import subprocess


class Stats:
    def __init__(self):
        self.stats_ref = "stats"
        self.stats_ref_path = "refs/notes/stats"

    def save(self, *, key, value, commitish="HEAD", quiet=False):
        stat_line = f"{key}: {value}"

        if existing_stats := self.get(commitish):
            edited_stat_lines = []
            had_stat = False

            for line in existing_stats.splitlines():
                if line.startswith(f"{key}:"):
                    # Update the existing stat
                    edited_stat_lines.append(stat_line)
                    had_stat = True
                else:
                    # Keep other existing stats
                    edited_stat_lines.append(line)

            if not had_stat:
                # Append the new stat
                edited_stat_lines.append(stat_line)

            message = "\n".join(edited_stat_lines)
        else:
            message = stat_line

        subprocess.check_call(
            [
                "git",
                "notes",
                "--ref",
                self.stats_ref,
                "add",
                "--force",
                "--message",
                message,
                commitish,
            ],
            # Don't show the "Overwriting existing notes for commit"
            stderr=subprocess.DEVNULL,
        )

        if not quiet:
            self.show(commitish)

    def delete(self, key, commitish="HEAD"):
        if existing_stats := self.get(commitish):
            edited_stat_lines = []

            for line in existing_stats.splitlines():
                if not line.startswith(f"{key}:"):
                    edited_stat_lines.append(line)

            message = "\n".join(edited_stat_lines)

            subprocess.check_call(
                [
                    "git",
                    "notes",
                    "--ref",
                    self.stats_ref,
                    "add",
                    "--force",
                    "--message",
                    message,
                    commitish,
                ],
                # Don't show the "Overwriting existing notes for commit"
                stderr=subprocess.DEVNULL,
            )

    def get(self, commitish="HEAD"):
        try:
            return subprocess.check_output(
                ["git", "notes", "--ref", self.stats_ref, "show", commitish],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8")
        except subprocess.CalledProcessError:
            return None

    def show(self, commitish="HEAD"):
        subprocess.check_call(
            ["git", "notes", "--ref", self.stats_ref, "show", commitish]
        )

    def log(self, *, keys, default_value, values_only, summarize, git_log_args=[]):
        stats = CommitStats()

        output = subprocess.check_output(
            [
                "git",
                "log",
                f"--show-notes={self.stats_ref_path}",
                "--format=COMMIT\n%H\n%N",
                *git_log_args,
            ]
        ).decode("utf-8")

        commit = ""

        for line in output.splitlines():
            if commit is None:
                commit = line
                stats.append_commit(commit)
                continue

            if line == "COMMIT":
                commit = None
                continue

            if not line.strip():
                continue

            key, value = line.split(":", 1)

            if key in keys or not keys:
                # TODO default value may have to be per-key... config file?
                stats.add(
                    commit=commit, key=key, value=value, default_value=default_value
                )

        stats.print(values_only=values_only)

    def push(self):
        subprocess.check_call(["git", "push", "origin", self.stats_ref_path])

    def fetch(self):
        subprocess.check_call(["git", "fetch", "origin", self.stats_ref_path])
