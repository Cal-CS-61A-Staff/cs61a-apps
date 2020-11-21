import click
from sicp.clone import run_apps_clone, run_61a_clone


@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    pass


@cli.command()
@click.argument("repo")
@click.argument("dest", default="")
def clone(repo, dest):
    """Clone REPO to DEST.

    REPO is the name of the 61a repo to set up.
    Currently, "apps" and "cs61a" are supported.
    By default, DEST is set to the name of REPO.
    """
    if repo == "apps":
        run_apps_clone(dest if dest else "cs61a-apps")
    elif repo == "cs61a":
        run_61a_clone(dest if dest else "berkeley-cs61a")
    else:
        click.echo("No need to use sicp for that! Just git clone.", err=True)


if __name__ == "__main__":
    cli()
