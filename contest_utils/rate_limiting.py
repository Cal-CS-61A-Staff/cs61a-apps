import os
import time
from functools import wraps

from flask import request, abort, current_app

from common.course_config import get_endpoint
from common.db import connect_db
from contest_utils.oauth import create_remote


def validate(data, timeout):
    for participation in data["participations"]:
        if participation["course"]["offering"] == get_endpoint("cs61a"):
            break
    else:
        abort(
            401, "You are not enrolled in CS 61A, and so are not authorized to submit."
        )

    email = data["email"]

    with connect_db() as db:
        ret = db(
            "SELECT last_access FROM accesses WHERE email=(%s)", [email]
        ).fetchone()

    now = int(time.time())
    if ret and now - ret[0] < timeout:
        abort(
            429,
            "You have made many requests in a short amount of time. Please wait a bit and try again.",
        )

    with connect_db() as db:
        db("DELETE FROM accesses WHERE email=(%s)", [email])
        db("INSERT INTO accesses VALUES (%s, %s)", [email, now])


def ratelimited(timeout):
    def decorator(route):
        @wraps(route)
        def wrapper(*args, **kwargs):
            remote = create_remote(current_app)
            token = request.form["token"]
            data = remote.get("user", token=token).data["data"]
            validate(data, timeout.total_seconds())
            return route(*args, **kwargs)

        return wrapper

    return decorator
