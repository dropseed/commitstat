import os
import sys
import subprocess
import click
from .core import Stats
from .config import Config


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
def test(keys):
    """Output stats but don't save them"""
    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()

    for key in keys:
        try:
            command = config.command_for_stat(key)
        except KeyError:
            click.secho(f"Unknown stat key: {key}", fg="red")
            exit(1)

        click.echo(f"Generating value for {key}: ", nl=False)
        value = subprocess.check_output(command, shell=True).decode("utf-8").strip()
        if value:
            click.secho(str(value), fg="green")
        else:
            click.secho(f"Skipping empty value for {key}", fg="yellow")


@cli.command()
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
def save(keys):
    """Save stat for the current commit"""
    commitish = "HEAD"

    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()

    stats = Stats()

    for key in keys:
        try:
            command = config.command_for_stat(key)
        except KeyError:
            click.secho(f"Unknown stat key: {key}", fg="red")
            exit(1)

        click.echo(f"Generating value for {key}: ", nl=False)
        value = subprocess.check_output(command, shell=True).decode("utf-8").strip()
        if value:
            click.secho(str(value), fg="green")
            stats.save(key=key, value=value, commitish=commitish)
        else:
            click.secho(f"Skipping empty value for {key}", fg="yellow")

    click.secho(f"\nStats for {commitish}:", bold=True)
    stats.show(commitish)

    # TODO if CI and stat config has a "goal", then create github status?


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
@click.option("--values-only", is_flag=True)
@click.option(
    "--format", "fmt", default="tsv", type=click.Choice(["tsv", "csv", "sparklines"])
)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def log(keys, values_only, fmt, git_log_args):
    """Log stats for commits matching git log args"""
    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()
    Stats().log(
        keys=keys,
        config=config,
        values_only=values_only,
        fmt=fmt,
        git_log_args=list(git_log_args),
    )


@cli.command()
@click.argument("commitish", default="HEAD")
def show(commitish):
    """Show stats for a commit"""
    try:
        Stats().show(commitish)
    except subprocess.CalledProcessError as e:
        exit(e.returncode)


@cli.command()
def push():
    """Push stats to remote"""
    try:
        Stats().push()
    except subprocess.CalledProcessError as e:
        click.secho("\nHave you created any stats yet?", fg="yellow")
        exit(e.returncode)


@cli.command()
@click.option("--force", "-f", is_flag=True)
def fetch(force):
    """Fetch stats from remote"""
    Stats().fetch(force=force)


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
@click.option(
    "--stash",
    is_flag=True,
    help="Stash your local changes after the config is loaded",
)
@click.option("--missing-only", is_flag=True)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def regen(keys, stash, missing_only, git_log_args):
    """
    Regenerate stats for all commits matching git log args
    (using the config as it existed pre-stash)
    """
    current_branch = (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode("utf-8")
        .strip()
    )

    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()

    stats = Stats().load(
        keys=keys, config=config, fill_defaults=False, git_log_args=list(git_log_args)
    )

    commits = stats.commits

    if missing_only:
        total_commits = len(commits)
        commits = stats.commits_missing_stats(keys)
        prompt = (
            f"Regenerate {list(keys)} stats for {len(commits)}"
            + f" of {total_commits} commits?"
        )
    else:
        prompt = f"Regenerate {list(keys)} stats for {len(commits)} commits?"

    # Let CI skip this if it can't prompt
    if not os.isatty(sys.stdin.fileno()) or not click.prompt(prompt, default=True):
        exit(1)

    if stash:
        subprocess.check_call(["git", "stash"], stdout=subprocess.DEVNULL)

    try:
        with click.progressbar(
            commits, show_pos=True, show_eta=True, label="Commits"
        ) as items:
            for commit in items:
                # TODO --missing-only option to only fill in
                # blanks (skip checkout etc. if nothing needed)

                try:
                    subprocess.check_call(
                        ["git", "checkout", commit],
                        stderr=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                    )
                except subprocess.CalledProcessError:
                    raise Exception(
                        f"Failed to checkout {commit}... "
                        + "if you have edited your config, try --stash."
                    )

                for key in keys:
                    if missing_only and stats.commit_has_stat(commit, key):
                        # Can skip this...
                        continue

                    command = config.command_for_stat(key)
                    value = (
                        subprocess.check_output(command, shell=True)
                        .decode("utf-8")
                        .strip()
                    )
                    Stats().save(key=key, value=value, commitish=commit)
    finally:
        # Make sure we reset to the ref where we started
        subprocess.check_call(
            ["git", "checkout", current_branch],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        if stash:
            subprocess.check_call(["git", "stash", "pop"], stdout=subprocess.DEVNULL)


@cli.command()
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
@click.option("--commitish", default="HEAD")
def delete(keys, commitish):
    """Delete a single stat"""
    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()

    stats = Stats()
    for key in keys:
        stats.delete(key, commitish)

    try:
        stats.show(commitish)
    except subprocess.CalledProcessError:
        # Stats probably all deleted
        pass


@cli.command()
@click.option("--remote", is_flag=True)
def clear(remote):
    """Delete all existing stats"""
    click.confirm("Are you sure you want to clear all existing stats?", abort=True)

    Stats().clear(remote=remote)

    if remote:
        click.secho("Remote stats cleared", fg="green")
    else:
        click.secho("Local stats cleared", fg="green")


@cli.command()
@click.option(
    "--key",
    "-k",
    "keys",
    default=[],
    multiple=True,
    help="Stats to include (all if not specified)",
)
@click.option(
    "--regen-missing/--no-regen-missing",
    default=True,
    help="Regenerate stats on commits missing them",
)
@click.option("--git-name", default="github-actions")
@click.option("--git-email", default="github-actions@github.com")
@click.pass_context
def ci(ctx, keys, regen_missing, git_name, git_email):
    """All-in-one fetch, save, push"""
    # TODO pass these to save instead of setting config?
    click.secho("Setting git user.name and user.email...", fg="cyan")
    subprocess.check_call(
        ["git", "config", "user.name", git_name],
    )
    subprocess.check_call(
        ["git", "config", "user.email", git_email],
    )

    click.secho("Fetching stats from remote...", fg="cyan")
    ctx.invoke(fetch)

    click.secho("\nSaving stats for the current commit...", fg="cyan")
    ctx.invoke(save, keys=keys)

    if regen_missing:
        click.secho(
            "\nRegenerating stats for last 10 commits if they are missing...", fg="cyan"
        )
        ctx.invoke(regen, keys=keys, missing_only=True, git_log_args=["-n", "10"])

    click.secho("\nPushing stats to remote...", fg="cyan")
    ctx.invoke(push)


if __name__ == "__main__":
    cli()
