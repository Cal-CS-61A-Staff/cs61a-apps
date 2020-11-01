from functools import wraps
from os import getenv

import requests

from examtool.api.auth import get_token, refresh_token


def server_only(func):
    @wraps(func)
    def wrapped(**kwargs):
        if getenv("ENV") == "SERVER":
            return func(**kwargs)
        else:
            method = func.__name__
            try:
                return call_server(method, kwargs)
            except PermissionError:
                refresh_token()
            return call_server(method, kwargs)

    return wrapped


def call_server(method, kwargs):
    token = get_token()
    resp = requests.post(
        "https://us-central1-cs61a-140900.cloudfunctions.net/exam-admin/api/{method}".format(
            method=method
        ),
        json={**kwargs, "token": token},
    )
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 401:
        raise PermissionError
    else:
        raise Exception(resp.text)
