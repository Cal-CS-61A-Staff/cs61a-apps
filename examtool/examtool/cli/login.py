import click

from examtool.api.auth import refresh_token


@click.command()
def login():
    """
    Login to OKPy.
    """
    token = refresh_token()
    print("Token = {}".format(token))
    print("Token automatically saved")


if __name__ == "__main__":
    login()
