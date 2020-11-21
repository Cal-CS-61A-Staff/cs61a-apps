import click
from sicp.clone import run_apps_clone

@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    pass

@cli.command()
@click.argument('repo')
@click.argument('dest', default='')
def clone(repo, dest):
    """Clone REPO to DEST.

    REPO is the name of the 61a repo to set up.
    Currently, only "apps" is supported. By
    default, DEST is set to the name of REPO.
    """
    if repo == "apps":
        run_apps_clone(dest if dest else 'cs61a-apps')
    else:
        click.echo("No need to use sicp for that! Just git clone.", err=True)


if __name__ == "__main__":
    cli()
