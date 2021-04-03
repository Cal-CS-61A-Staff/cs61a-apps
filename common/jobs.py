from functools import wraps

from flask import Flask


def job(app: Flask, endpoint):
    """Adds a URL rule for a recurring job at ``/jobs/<endpoint>``.

    :param app: the app the method belongs to
    :type app: ~flask.Flask

    :param endpoint: the endpoint to route to the method
    :type endpoint: str

    :return: a decorator which can be applied to a function to bind it to
        ``/jobs/<endpoint>``
    """

    def decorator(func):
        @wraps(func)
        def wrapped():
            func()
            return ""

        app.add_url_rule(
            f"/jobs/{endpoint}",
            func.__name__ + "_job",
            wrapped,
            strict_slashes=False,
            methods=["POST"],
        )

        return func

    return decorator
