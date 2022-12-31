from .stats import CommitStats
import subprocess


class Stats:
    def __init__(self):
        self.stats_ref = "commitstats"
        self.stats_ref_path = "refs/notes/commitstats"

    def save(self, *, key, value, commitish="HEAD"):
        # TODO use the new CommitStats classes for this?
        # would be nice to keep existing order for stats though in message
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
            if message.strip() == existing_stats.strip():
                return

            subprocess.check_call(
                [
                    "git",
                    "notes",
                    "--ref",
                    self.stats_ref,
                    "remove",
                    commitish,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            message = stat_line

        subprocess.check_call(
            [
                "git",
                "notes",
                "--ref",
                self.stats_ref,
                "add",
                "--message",
                message,
                commitish,
            ],
        )

    def delete(self, key, commitish="HEAD"):
        if existing_stats := self.get(commitish):
            edited_stat_lines = []

            for line in existing_stats.splitlines():
                if not line.startswith(f"{key}:"):
                    edited_stat_lines.append(line)

            if edited_stat_lines:
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
            else:
                subprocess.check_call(
                    [
                        "git",
                        "notes",
                        "--ref",
                        self.stats_ref,
                        "remove",
                        commitish,
                    ],
                )

    def clear(self, remote):
        if remote:
            subprocess.check_call(
                ["git", "push", "--delete", "origin", self.stats_ref_path]
            )
        else:
            subprocess.check_call(["git", "update-ref", "-d", self.stats_ref_path])

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

    def log(self, *, keys, config, values_only, fmt, git_log_args=[]):
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

        commit = False

        for line in output.splitlines():
            if commit is None:
                commit = line
                stats.append_commit(commit)
                # Fill empty values first for all the keys we expect
                for key in keys:
                    stats.add(
                        commit=commit,
                        key=key,
                        value=config.default_for_stat(key),
                        type=config.type_for_stat(key),
                    )
                continue

            if line == "COMMIT":
                commit = None
                continue

            if not line.strip():
                continue

            key, value = line.split(":", 1)

            if key in keys:
                stats.add(
                    commit=commit,
                    key=key,
                    value=value,
                    type=config.type_for_stat(key),
                )

        if fmt == "tsv":
            stats.print(values_only=values_only, sep="\t")
        elif fmt == "csv":
            stats.print(values_only=values_only, sep=",")
        elif fmt == "sparklines":
            stats.sparklines()

    def push(self):
        subprocess.check_call(["git", "push", "origin", self.stats_ref_path])

    def fetch(self, force=False):
        args = [
            "git",
            "fetch",
            "origin",
            f"{self.stats_ref_path}:{self.stats_ref_path}",
        ]
        if force:
            args.append("--force")
        subprocess.check_call(args)
