import click

from sicp.build import build
from sicp.clone import clone
from sicp.venv import venv
from sicp.pr import pr


@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    pass


cli.add_command(clone)
cli.add_command(build)
cli.add_command(venv)
cli.add_command(pr)

if __name__ == "__main__":
    cli()
