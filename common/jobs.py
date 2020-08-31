from flask import Flask


def job(app: Flask, endpoint):
    def decorator(func):
        app.add_url_rule(
            f"/jobs/{endpoint}",
            func.__name__,
            func,
            strict_slashes=False,
            methods=["POST"],
        )

    return decorator
