from urllib.parse import urlparse

from flask import request, url_for as flask_url_for


def url_for(*args, **kwargs) -> str:
    host = request.headers.get("X-Forwarded-For-Host") or request.headers.get("Host")
    redirect_url = urlparse(flask_url_for(*args, **kwargs))
    # noinspection PyProtectedMember
    return redirect_url._replace(netloc=host, scheme="https").geturl()
