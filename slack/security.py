import hashlib
import hmac
import time
from functools import wraps

from flask import abort, request

from common.oauth_client import get_user, login
from common.rpc.secrets import get_secret

AUTHORIZED_ROLES = ["staff", "instructor", "grader"]


def slack_signed(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        data = request.get_data().decode("utf-8")
        timestamp = request.headers["X-Slack-Request-Timestamp"]
        slack_signature = request.headers["X-Slack-Signature"]
        if abs(time.time() - int(timestamp)) > 60 * 5:
            abort(403)
        basestring = "v0:" + timestamp + ":" + data
        my_signature = (
            "v0="
            + hmac.new(
                get_secret(secret_name="SIGNING_SECRET").encode(),
                basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        if hmac.compare_digest(my_signature.encode(), slack_signature.encode()):
            return route(*args, **kwargs)
        else:
            abort(403)

    return wrapped


def get_staff_endpoints():
    try:
        ret = get_user()
        for course in ret["participations"]:
            if course["role"] not in AUTHORIZED_ROLES:
                continue
            yield course["course"]["offering"]
    except Exception as e:
        # fail safe!
        print(e)
        return False


def logged_in(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if not list(get_staff_endpoints()):
            return login()
        return route(*args, **kwargs)

    return wrapped
