import string
from os import getenv
from random import SystemRandom


def get_master_secret():
    """Get ``APP_MASTER_SECRET`` from the environment using :func:`os.getenv`.

    :return: the master secret
    """
    return getenv("APP_MASTER_SECRET")


def new_secret():
    """Get a new 64-character secret, with each character a random uppercase
    letter or a digit.

    :return: the randomly-generated secret
    """
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64)
    )
