import click

from examtool.api.auth import refresh_token


@click.command()
@click.option(
    "--browser/--no-browser",
    default=True,
    help="Choose between browser-based and browserless authentication",
)
def login(browser):
    """
    Login to OKPy.
    """
    token = refresh_token(no_browser=not browser)
    print("Token = {}".format(token))
    print("Token automatically saved")


if __name__ == "__main__":
    login()
