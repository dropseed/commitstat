import subprocess
import click
from .core import Stats


@click.group()
def cli():
    pass


@cli.command()
@click.option("--key", "-k", required=True)
@click.option("--value", "-v", required=True)  # value as arg so it's pipeable?
@click.option("--commitish", default="HEAD")
@click.option("--quiet", "-q", is_flag=True)
def save(key, value, commitish, quiet):
    Stats().save(key=key, value=value, commitish=commitish, quiet=quiet)


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option("--key", "-k", "keys", default=[], multiple=True)
@click.option("--default-value", "-d", default="0")
@click.option("--summarize", "-s", is_flag=True)
@click.option("--values-only", is_flag=True)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def log(keys, default_value, values_only, summarize, git_log_args):
    Stats().log(
        keys=keys,
        default_value=default_value,
        values_only=values_only,
        summarize=summarize,
        git_log_args=list(git_log_args),
    )


@cli.command()
@click.argument("commitish", default="HEAD")
def show(commitish):
    try:
        Stats().show(commitish)
    except subprocess.CalledProcessError as e:
        exit(e.returncode)


@cli.command()
def push():
    Stats().push()


@cli.command()
def fetch():
    Stats().fetch()


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option("--key", "-k", required=True)
@click.option("--command", "-c", required=True)
@click.argument("git_log_args", nargs=-1, type=click.UNPROCESSED)
def regen(key, command, git_log_args):
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

    if not click.prompt(
        f'Regenerate "{key}" stat for {len(commits)} commits?', default=True
    ):
        exit(1)

    try:
        with click.progressbar(commits, show_pos=True, show_eta=True) as items:
            for commit in items:
                subprocess.check_call(
                    ["git", "checkout", commit],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                )

                value = (
                    subprocess.check_output(command, shell=True).decode("utf-8").strip()
                )
                Stats().save(key=key, value=value, commitish=commit, quiet=True)
    finally:
        # Make sure we reset to the ref where we started
        subprocess.check_call(
            ["git", "checkout", current_branch],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )


@cli.command()
@click.option("--key", "-k", default="")
@click.option("--commitish", default="HEAD")
def delete(key, commitish):
    Stats().delete(key, commitish)


if __name__ == "__main__":
    cli()
