import string
from os import getenv
from random import SystemRandom


def get_master_secret():
    return getenv("APP_MASTER_SECRET")


def new_secret():
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64)
    )
