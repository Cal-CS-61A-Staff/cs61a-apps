from os import getenv

from flask import jsonify

import requests

import examtool.api.database as db
import examtool.api.email as mail


def handle_api_call(method, kwargs):
    target = kwargs["exam"]
    token = kwargs.pop("token")
    course = target.split("-")[0]
    ret = requests.get("https://okpy.org/api/v3/user/", params={"access_token": token})
    if ret.status_code != 200:
        return "", 401
    email = ret.json()["data"]["email"]
    if not is_admin(email, course):
        return "", 401
    try:
        if method in mail.__dict__:
            return jsonify(mail.__dict__[method](**kwargs))
        else:
            return jsonify(db.__dict__[method](**kwargs))
    except Exception as e:
        return repr(e), 500


def is_admin(email, course):
    if getenv("ENV") == "dev":
        return True
    return requests.post(
        "https://auth.apps.cs61a.org/admins/is_admin",
        json={
            "client_name": getenv("AUTH_CLIENT_NAME"),
            "secret": getenv("AUTH_CLIENT_SECRET"),
            "email": email,
            "course": course,
        },
    ).json()
