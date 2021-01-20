import click, os

from sicp.build import build
from sicp.clone import clone
from sicp.venv import venv
from sicp.pr import pr
from sicp.auth import auth
from sicp.send import send

from common.rpc.auth_utils import set_token_path


@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    set_token_path(f"{os.path.expanduser('~')}/.sicp_token")


cli.add_command(clone)
cli.add_command(build)
cli.add_command(venv)
cli.add_command(pr)
cli.add_command(auth)
cli.add_command(send)

if __name__ == "__main__":
    cli()
