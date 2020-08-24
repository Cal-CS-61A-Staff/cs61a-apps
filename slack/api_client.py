import json
from functools import wraps

import requests
from flask import abort

from common.db import connect_db
from common.rpc.secrets import validates_master_secret
from common.rpc.slack import list_channels, post_message


def api_secure(f):
    @wraps(f)
    @validates_master_secret
    def wrapped(app, is_staging, **kwargs):
        if app != "auth":
            abort(401)
        return f(**kwargs)

    return wrapped


def create_api_client(app):
    @list_channels.bind(app)
    @api_secure
    def handle_list_channels(course):
        with connect_db() as db:
            bot_token, = db(
                "SELECT bot_access_token FROM bot_data WHERE course = (%s)", [course]
            ).fetchone()

        resp = requests.post(
            "https://slack.com/api/users.conversations",
            {"exclude_archived": True, "types": "public_channel,private_channel"},
            headers={"Authorization": "Bearer {}".format(bot_token)},
        ).json()

        return resp["channels"]

    @post_message.bind(app)
    @api_secure
    def handle_post_message(course, message, channel):
        with connect_db() as db:
            bot_token, = db(
                "SELECT bot_access_token FROM bot_data WHERE course = (%s)", [course]
            ).fetchone()

        if isinstance(message, str):
            message = email_replace(message, bot_token)
            requests.post(
                "https://slack.com/api/chat.postMessage",
                json={"channel": channel, "text": message},
                headers={"Authorization": "Bearer {}".format(bot_token)},
            )
        else:
            stringify = json.dumps(message)
            stringify = email_replace(stringify, bot_token)
            message = json.loads(stringify)
            requests.post(
                "https://slack.com/api/chat.postMessage",
                json={"channel": channel, "blocks": message},
                headers={"Authorization": "Bearer {}".format(bot_token)},
            )


def email_replace(message, bot_token):
    users = requests.get(
        "https://slack.com/api/users.list", params={"token": bot_token}
    ).json()
    for member in users["members"]:
        message = message.replace(
            f"<!{member['profile'].get('email')}>", f"<@{member['id']}>"
        )
    return message
