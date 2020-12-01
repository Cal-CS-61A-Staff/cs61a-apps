import json
import traceback
from functools import wraps

import flask
import requests
from cachetools import TTLCache
from flask import has_request_context, jsonify, request

from common.rpc.auth_utils import get_token, refresh_token
from common.secrets import get_master_secret


class Service:
    def __init__(self, route):
        self.route = route


def create_service(app: str, override=None):
    app = override or app.split(".")[-1]

    def route(path):
        def decorator(func):
            @wraps(func)
            def wrapped(**kwargs):
                noreply = kwargs.pop("noreply", False)
                endpoints = []
                if has_request_context() and not noreply:
                    proxied_host = request.headers.get("X-Forwarded-For-Host")
                    if proxied_host:
                        parts = proxied_host.split(".")
                        if "pr" in parts:
                            pr = parts[0]
                            endpoints.append(f"https://{pr}.{app}.pr.cs61a.org{path}")
                endpoints.append(f"https://{app}.cs61a.org{path}")

                if app == "sb":
                    endpoints = [
                        f"https://121.sandbox.pr.cs61a.org{path}"
                        # f"http://localhost:5000{path}"
                    ]  # FIXME DO NOT MERGE @nocommit

                for i, endpoint in enumerate(endpoints):
                    if noreply:
                        try:
                            requests.post(endpoint, json=kwargs, timeout=1)
                        except requests.exceptions.ReadTimeout:
                            pass
                    else:
                        try:
                            resp = requests.post(endpoint, json=kwargs)
                            if i != len(endpoints) - 1:
                                # if a PR build reports failure, try the prod build
                                resp.raise_for_status()
                        except:
                            if i != len(endpoints) - 1:
                                # on a PR build, try the main endpoint next
                                continue
                            else:
                                raise
                        if resp.status_code == 401:
                            raise PermissionError(resp.text)
                        elif resp.status_code == 500:
                            raise Exception(resp.text)
                        resp.raise_for_status()
                        return resp.json()

            def bind(app: flask.Flask):
                def decorator(func):
                    def handler():
                        kwargs = request.json
                        try:
                            return jsonify(func(**kwargs))
                        except PermissionError as e:
                            return str(e), 401
                        except Exception as e:
                            traceback.print_exc()
                            return str(e), 500

                    app.add_url_rule(path, func.__name__, handler, methods=["POST"])
                    return func

                return decorator

            wrapped.bind = bind

            return wrapped

        return decorator

    return Service(route)


def requires_master_secret(func):
    @wraps(func)
    def wrapped(**kwargs):
        return func(**kwargs, master_secret=get_master_secret())

    return wrapped


def requires_access_token(func):
    @wraps(func)
    def wrapped(**kwargs):
        try:
            return func(**kwargs, access_token=get_token())
        except PermissionError:
            refresh_token()
            return func(**kwargs, access_token=get_token())

    return wrapped


def cached(ttl: int = 1800):
    """
    Caches the return value of this RPC method for `ttl` seconds (defaults to 1800s)
    """
    cache = TTLCache(1000, ttl)

    def decorator(func):
        @wraps(func)
        def wrapped(**kwargs):
            key = json.dumps(kwargs)
            if key not in cache:
                cache[key] = func(**kwargs)
            return cache[key]

        return wrapped

    return decorator
