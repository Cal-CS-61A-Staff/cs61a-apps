from os import getenv
from urllib.parse import urlparse

from flask import request, url_for as flask_url_for


def get_host() -> str:
    """Get the current host URL from request headers.

    :return: ``X-Forwarded-For-Host`` or ``Host``

    .. note::
        61A apps use ``X-Forwarded-For-Host``, which is not a standard header,
        for legacy reasons. This may be fixed in the future, but not for now.
    """
    return request.headers.get("X-Forwarded-For-Host") or request.headers.get("Host")


def url_for(*args, **kwargs) -> str:
    """Return the absolute URL target for the requested method.

    Uses :func:`~flask.url_for` to get the relative endpoint, then prepends the
    host from :func:`get_host` to the URL to make it absolute.

    All arguments are passed directly into :func:`~flask.url_for`.

    :return: the absolute target URL
    """
    host = get_host()
    redirect_url = urlparse(flask_url_for(*args, **kwargs))
    # noinspection PyProtectedMember
    return redirect_url._replace(
        netloc=host, scheme="https" if getenv("ENV") == "prod" else "http"
    ).geturl()
