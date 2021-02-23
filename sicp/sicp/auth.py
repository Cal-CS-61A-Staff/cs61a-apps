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
    """
    Get current user information.
    """
    r = requests.get(
        "https://okpy.org/api/v3/user/?access_token={}".format(get_token())
    )
    if not r.ok:
        print("You don't appear to be logged in.")

    data = r.json()["data"]
    print(f"Hi {data.get('name')}! You're logged in as {data.get('email')}.")


@auth.command()
@click.option(
    "--browser/--no-browser",
    default=True,
    help="Choose between browser-based and browserless authentication",
)
def login(browser):
    """
    Log into Ok and get an access token.
    """
    refresh_token(no_browser=not browser)
