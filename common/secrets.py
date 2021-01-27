from os import getenv


def get_master_secret():
    return getenv("APP_MASTER_SECRET")
