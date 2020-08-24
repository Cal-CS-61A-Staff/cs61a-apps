import json
from functools import wraps

import flask
import requests
from cachetools import TTLCache
from flask import jsonify, request

from common.secrets import get_master_secret


class Service:
    def __init__(self, route):
        self.route = route


def create_service(app: str):
    app = app.split(".")[-1]

    def route(path):
        def decorator(func):
            endpoint = f"https://{app}.cs61a.org{path}"

            @wraps(func)
            def wrapped(**kwargs):
                if kwargs.pop("noreply", False):
                    try:
                        requests.post(endpoint, json=kwargs, timeout=1)
                    except requests.exceptions.ReadTimeout:
                        pass
                else:
                    return requests.post(endpoint, json=kwargs).json()

            def bind(app: flask.Flask):
                def decorator(func):
                    def handler():
                        kwargs = request.json
                        return jsonify(func(**kwargs))

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
