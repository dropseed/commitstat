import subprocess
import click
from .core import Stats
from .config import Config


@click.group()
def cli():
    pass


@cli.command()
@click.option("--key", "-k", "keys", default=[], multiple=True)
@click.option("--commitish", default="HEAD")
@click.option("--quiet", "-q", is_flag=True)
def save(keys, commitish, quiet):
    """Save a stat for a commit"""
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

    if not quiet:
        click.secho(f"\nStats for {commitish}:", bold=True)
        stats.show(commitish)

    # TODO if CI and stat config has a "goal", then create github status?


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option("--key", "-k", "keys", default=[], multiple=True)
@click.option("--summarize", "-s", is_flag=True)
@click.option("--values-only", is_flag=True)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def log(keys, values_only, summarize, git_log_args):
    """Log stats for commits matching git log args"""
    config = Config.load_yaml()
    Stats().log(
        keys=keys,
        config=config,
        values_only=values_only,
        summarize=summarize,
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
def fetch():
    """Fetch stats from remote"""
    Stats().fetch()


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option("--key", "-k", "keys", default=[], multiple=True)
@click.option(
    "--stash",
    is_flag=True,
    help="Stash your local changes after the config is loaded",
)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def regen(keys, stash, git_log_args):
    """
    Regenerate stats for all commits matching git log args
    (using the config as it existed pre-stash)
    """
    current_branch = (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode("utf-8")
        .strip()
    )

    args = ["git", "log", "--format=%H"]
    if git_log_args:
        args.extend(git_log_args)

    try:
        output = subprocess.check_output(args).decode("utf-8")
    except subprocess.CalledProcessError as e:
        exit(e.returncode)

    commits = output.splitlines()

    config = Config.load_yaml()
    if not keys:
        keys = config.stats_keys()

    if not click.prompt(
        f"Regenerate {list(keys)} stats for {len(commits)} commits?", default=True
    ):
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

                subprocess.check_call(
                    ["git", "checkout", commit],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )

                for key in keys:
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
@click.option("--key", "-k", "keys", default=[], multiple=True)
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
@click.option("--key", "-k", "keys", default=[], multiple=True)
@click.option("--git-author", default="github-actions")
@click.option("--git-email", default="github-actions@github.com")
@click.pass_context
def ci(ctx, keys, git_author, git_email):
    """All-in-one fetch, save, push"""
    click.secho("Setting git user.name and user.email...", fg="cyan")
    subprocess.check_call(
        ["git", "config", "user.name", git_author],
    )
    subprocess.check_call(
        ["git", "config", "user.email", git_email],
    )

    click.secho("Fetching stats from remote...", fg="cyan")
    ctx.invoke(fetch)

    click.secho("\nSaving stats...", fg="cyan")
    ctx.invoke(save, keys=keys)

    click.secho("\nPushing stats to remote...", fg="cyan")
    ctx.invoke(push)


if __name__ == "__main__":
    cli()
