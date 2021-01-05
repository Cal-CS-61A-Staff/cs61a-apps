import json
import traceback
from functools import wraps

import flask
import requests
from cachetools import TTLCache
from flask import Response, has_request_context, jsonify, request, stream_with_context

from common.rpc.auth_utils import get_token, refresh_token
from common.secrets import get_master_secret

STATUS_MARKER = "__INTERNAL_STATUS_MARKER"


class Service:
    def __init__(self, route):
        self.route = route


def create_service(app: str, override=None):
    app = override or app.split(".")[-1]

    def route(path, *, streaming=False):
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

                if (
                    not get_master_secret()
                    and "_impersonate" in kwargs
                    and not "_sudo_token" in kwargs
                ):
                    from common.rpc.secrets import (
                        get_secret_from_server,
                    )  # placed here to avoid circular imports

                    print(f"Attempting to impersonate {kwargs.get('_impersonate')}")

                    try:
                        sudo_secret = get_secret_from_server(
                            secret_name="MASTER",
                            _impersonate=kwargs.pop("_impersonate"),
                            _sudo_token=get_token(),
                        )
                    except PermissionError:
                        refresh_token()
                        try:  # second attempt, in case the first was just an expired token
                            sudo_secret = get_secret_from_server(
                                secret_name="MASTER",
                                _impersonate=kwargs.pop("_impersonate"),
                                _sudo_token=get_token(),
                            )
                        except PermissionError:
                            raise PermissionError(
                                "You must be logged in as an admin to do that."
                            )
                            return

                    kwargs["master_secret"] = sudo_secret

                for i, endpoint in enumerate(endpoints):
                    if noreply:
                        try:
                            requests.post(endpoint, json=kwargs, timeout=1)
                        except requests.exceptions.ReadTimeout:
                            pass
                    else:
                        try:
                            resp = requests.post(
                                endpoint, json=kwargs, stream=streaming
                            )
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
                        if streaming:

                            def generator():
                                buffer = []
                                ok = True
                                for x in resp.iter_content():
                                    buffer.append(x.decode("ascii"))
                                    buff_string = "".join(buffer)
                                    if STATUS_MARKER in buff_string:
                                        # We are now reading in the error message
                                        # Stop flushing the buffer
                                        ok = False
                                    if ok and len(buff_string) > len(STATUS_MARKER):
                                        yield buff_string[: -len(STATUS_MARKER)]
                                        buffer = [buff_string[-len(STATUS_MARKER) :]]
                                buff_string = "".join(buffer)
                                if not buff_string.endswith(STATUS_MARKER):
                                    # some error occurred
                                    pos = buff_string.index(STATUS_MARKER)
                                    raise Exception(
                                        buff_string[pos + len(STATUS_MARKER) :]
                                    )
                                yield from buffer[: -len(STATUS_MARKER)]

                            return generator()
                        else:
                            return resp.json()

            def bind(app: flask.Flask):
                def decorator(func):
                    def handler():
                        kwargs = request.json
                        try:
                            out = func(**kwargs)
                            if streaming:
                                # we should stream our response
                                def generator():
                                    try:
                                        for x in out:
                                            yield bytes(
                                                x, encoding="ascii", errors="replace"
                                            )
                                    except Exception as e:
                                        yield STATUS_MARKER
                                        yield bytes(
                                            str(e), encoding="ascii", errors="replace"
                                        )
                                    else:
                                        yield STATUS_MARKER

                                return Response(stream_with_context(generator()))
                            else:
                                return jsonify(out)
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
