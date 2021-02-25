import json
import traceback
from functools import wraps
from time import sleep
from typing import List
from urllib.error import HTTPError

import flask
import requests
from cachetools import TTLCache
from flask import Response, has_request_context, jsonify, request, stream_with_context

from common.rpc.auth_utils import get_token, refresh_token
from common.secrets import get_master_secret

STATUS_MARKER = "__INTERNAL_STATUS_MARKER"
GCP_INTERNAL_ERROR_CODE = 503


class Service:
    def __init__(self, route):
        self.route = route


def find_default_endpoints(app: str, path: str):
    endpoints = []
    if has_request_context():
        proxied_host = request.headers.get("X-Forwarded-For-Host")
        if proxied_host:
            parts = proxied_host.split(".")
            if "pr" in parts:
                pr = parts[0]
                endpoints.append(f"https://{pr}.{app}.pr.cs61a.org{path}")
    endpoints.append(f"https://{app}.cs61a.org{path}")
    return endpoints


def select_endpoint(endpoints: List[str], path: str, retries: int):
    # try all the PR candidates
    for i, endpoint in enumerate(endpoints[:-1]):
        try:
            for _ in range(retries + 1):
                # check if the PR / endpoint exists
                check_exists = requests.get(
                    endpoint[: -len(path)],
                    allow_redirects=False,
                )
                if check_exists.status_code == GCP_INTERNAL_ERROR_CODE:
                    # this error is not our fault, retry after a short pause
                    sleep(1)
                    continue
                check_exists.raise_for_status()
                return endpoint
            else:
                # if we exhaust all our retries, give up on this endpoint
                continue
        except (HTTPError, requests.ConnectionError):
            continue

    # fall back to prod
    return endpoints[-1]


def stream_encode(out):
    try:
        for x in out:
            yield bytes(x, encoding="ascii", errors="replace")
    except Exception as e:
        yield STATUS_MARKER
        yield bytes(str(e), encoding="ascii", errors="replace")
    else:
        yield STATUS_MARKER


def receive_stream(resp: Response):
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
        raise Exception(buff_string[pos + len(STATUS_MARKER) :])
    yield from buffer[: -len(STATUS_MARKER)]


def create_service(app: str, override=None, providers=None):
    app = override or app.split(".")[-1]

    def route(path, *, streaming=False):
        def decorator(func):
            @wraps(func)
            def wrapped(*, noreply=False, timeout=1, retries=0, **kwargs):
                assert (
                    not noreply or not retries
                ), "Cannot retry a noreply request, use streaming instead"

                if providers:
                    endpoints = [f"{provider}{path}" for provider in providers]
                else:
                    endpoints = find_default_endpoints(app, path)

                endpoint = select_endpoint(endpoints, path, retries)

                if noreply:
                    try:
                        requests.post(endpoint, json=kwargs, timeout=timeout)
                    except requests.exceptions.ReadTimeout:
                        return
                else:
                    for _ in range(retries + 1):
                        resp = requests.post(endpoint, json=kwargs, stream=streaming)
                        if resp.status_code == GCP_INTERNAL_ERROR_CODE:
                            sleep(1)
                            continue
                        break
                    else:
                        # we exhausted all our retries
                        resp.raise_for_status()

                    if resp.status_code == 401:
                        raise PermissionError(resp.text)
                    elif resp.status_code == 500:
                        raise Exception(resp.text)
                    resp.raise_for_status()
                    if streaming:
                        return receive_stream(resp)
                    else:
                        return resp.json()

            def bind(app: flask.Flask):
                def decorator(func):
                    def handler():
                        kwargs = request.json
                        try:
                            out = func(**kwargs)
                            if streaming:
                                return Response(stream_with_context(stream_encode(out)))
                            else:
                                return jsonify(out)
                        except PermissionError as e:
                            return "", 401
                        except Exception as e:
                            traceback.print_exc()
                            print(str(e))
                            return "", 500

                    app.add_url_rule(path, func.__name__, handler, methods=["POST"])
                    return func

                return decorator

            wrapped.bind = bind

            return wrapped

        return decorator

    return Service(route)


def requires_master_secret(func):
    @wraps(func)
    def wrapped(*, _impersonate=None, _sudo_token=None, **kwargs):
        if _sudo_token:
            return func(**kwargs, _impersonate=_impersonate, _sudo_token=_sudo_token)
        elif not get_master_secret() and _impersonate and not _sudo_token:
            from common.rpc.secrets import (
                get_secret_from_server,
            )  # placed here to avoid circular imports

            print(f"Attempting to impersonate {_impersonate}")

            try:
                sudo_secret = get_secret_from_server(
                    secret_name="MASTER",
                    _impersonate=_impersonate,
                    _sudo_token=get_token(),
                )
            except PermissionError:
                refresh_token()
                try:  # second attempt, in case the first was just an expired token
                    sudo_secret = get_secret_from_server(
                        secret_name="MASTER",
                        _impersonate=_impersonate,
                        _sudo_token=get_token(),
                    )
                except PermissionError:
                    raise PermissionError(
                        "You must be logged in as an admin to do that."
                    )

            master_secret = sudo_secret
        else:
            master_secret = get_master_secret()

        return func(**kwargs, master_secret=master_secret)

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
