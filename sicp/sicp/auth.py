import click, requests

from common.rpc.auth_utils import refresh_token, get_token


@click.group("auth")
def auth():
    """
    Commands to interface with authentication.
    """
    pass


@auth.command()
def whoami():
    """Get current user information.

    NUM is the PR number you want to build targets
    for, and TARGETS is the list of apps you want
    to build within that PR. If no targets are passed
    in, then all apps modified in the PR are built.
    """
    r = requests.get(
        "https://okpy.org/api/v3/user/?access_token={}".format(get_token())
    )
    if not r.ok:
        print("You don't appear to be logged in.")

    data = r.json()["data"]
    print(f"Hi {data.get('name')}! You're logged in as {data.get('email')}.")


@auth.command()
def login():
    """
    Log into Ok and get an access token.
    """
    refresh_token()
