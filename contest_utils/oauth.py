from flask import request, current_app
from flask_oauthlib.client import OAuth
from werkzeug import security


CONSUMER_KEY = "hog-contest"


def create_remote(app):
    oauth = OAuth(app)

    remote = oauth.remote_app(
        "ok-server",  # Server Name
        consumer_key=CONSUMER_KEY,
        consumer_secret="dummy",
        request_token_params={"scope": "email", "state": lambda: security.gen_salt(10)},
        base_url="https://okpy.org/api/v3/",
        request_token_url=None,
        access_token_method="POST",
        access_token_url="https://okpy.org/oauth/token",
        authorize_url="https://okpy.org/oauth/authorize",
    )

    return remote


def get_group(endpoint):
    remote = create_remote(current_app)
    token = request.form["token"]
    email = remote.get("user", token=token).data["data"]["email"]
    group_info = remote.get(
        "assignment/{}/group/{}".format(endpoint, email), token=token
    )

    group = []
    for user in group_info.data["data"]["members"]:
        if user["status"] == "active":
            group.append(user["user"]["email"])

    if len(group) > 1:
        return group
    else:
        return [email]
