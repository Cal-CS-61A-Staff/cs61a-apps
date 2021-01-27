import os
import urllib.parse

import flask
import requests
from flask import current_app, g, session, request, redirect, abort, jsonify
from flask_oauthlib.client import OAuth
from werkzeug import security
from urllib.parse import urlparse

from common.rpc.auth import get_endpoint
from common.rpc.secrets import get_secret
from common.url_for import get_host, url_for

AUTHORIZED_ROLES = ("staff", "instructor", "grader")

REDIRECT_KEY = "REDIRECT_KEY"


def get_user():
    g.user_data = g.get("user_data") or current_app.remote.get("user")
    return g.user_data.data["data"]


def is_logged_in():
    return "access_token" in session


def is_staff(course):
    return is_enrolled(course, roles=AUTHORIZED_ROLES)


def is_enrolled(course, *, roles=None):
    try:
        endpoint = get_endpoint(course=course)
        for participation in get_user()["participations"]:
            if roles and participation["role"] not in roles:
                continue
            if participation["course"]["offering"] != endpoint and endpoint is not None:
                continue
            return True
        return False
    except Exception as e:
        # fail safe!
        print(e)
        return False


def login():
    session[REDIRECT_KEY] = urlparse(request.url)._replace(netloc=get_host()).geturl()
    return redirect(url_for("login"))


def create_oauth_client(
    app: flask.Flask,
    consumer_key,
    secret_key=None,
    success_callback=None,
    return_response=None,
):
    oauth = OAuth(app)

    if os.getenv("ENV") == "prod":
        if secret_key is None:
            app.secret_key = get_secret(secret_name="OKPY_OAUTH_SECRET")
        else:
            app.secret_key = secret_key
    else:
        consumer_key = "local-dev-all"
        app.secret_key = "kmSPJYPzKJglOOOmr7q0irMfBVMRFXN"

    if not app.debug:
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Lax",
        )

    remote = oauth.remote_app(
        "ok-server",  # Server Name
        consumer_key=consumer_key,
        consumer_secret=app.secret_key,
        request_token_params={"scope": "all", "state": lambda: security.gen_salt(10)},
        base_url="https://okpy.org/api/v3/",
        request_token_url=None,
        access_token_method="POST",
        access_token_url="https://okpy.org/oauth/token",
        authorize_url="https://okpy.org/oauth/authorize",
    )

    def check_req(uri, headers, body):
        """ Add access_token to the URL Request. """
        if "access_token" not in uri and session.get("access_token"):
            params = {"access_token": session.get("access_token")[0]}
            url_parts = list(urllib.parse.urlparse(uri))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)

            url_parts[4] = urllib.parse.urlencode(query)
            uri = urllib.parse.urlunparse(url_parts)
        return uri, headers, body

    remote.pre_request = check_req

    @app.route("/oauth/login")
    def login():
        if app.debug:
            response = remote.authorize(callback=url_for("authorized", _external=True))
        else:
            response = remote.authorize(
                url_for("authorized", _external=True, _scheme="https")
            )
        return response

    @app.route("/oauth/authorized")
    def authorized():
        resp = remote.authorized_response()
        if resp is None:
            return "Access denied: error=%s" % (request.args["error"])
        if isinstance(resp, dict) and "access_token" in resp:
            session["access_token"] = (resp["access_token"], "")
            if return_response:
                return_response(resp)

        if success_callback:
            success_callback()

        target = session.get(REDIRECT_KEY)
        if target:
            session.pop(REDIRECT_KEY)
            return redirect(target)
        return redirect(url_for("index"))

    @app.route("/api/user", methods=["POST"])
    def client_method():
        if "access_token" not in session:
            abort(401)
        token = session["access_token"][0]
        r = requests.get("https://okpy.org/api/v3/user/?access_token={}".format(token))
        if not r.ok:
            abort(401)
        return jsonify(r.json())

    @remote.tokengetter
    def get_oauth_token():
        return session.get("access_token")

    app.remote = remote
