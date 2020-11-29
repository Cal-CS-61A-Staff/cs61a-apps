import click

from sicp.build import build
from sicp.clone import clone


@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    pass


cli.add_command(clone)
cli.add_command(build)

if __name__ == "__main__":
    cli()
