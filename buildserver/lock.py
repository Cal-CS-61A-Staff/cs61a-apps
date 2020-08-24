from contextlib import contextmanager

from app_config import App, WEB_DEPLOY_TYPES
from common.db import connect_db


@contextmanager
def service_lock(app: App, pr_number: int = 0):
    with connect_db() as db:
        locked = db(
            "SELECT locked FROM services WHERE app=(%s) AND pr_number=(%s)",
            [app.name, pr_number],
        ).fetchone()
        if locked is not None and locked[0]:
            raise BlockingIOError(app, pr_number)
        db(
            "DELETE FROM services WHERE app=(%s) AND pr_number=(%s)",
            [app.name, pr_number],
        )
        db(
            "INSERT INTO services VALUES (%s, %s, %s, %s)",
            [app.name, pr_number, True, app.config["deploy_type"] in WEB_DEPLOY_TYPES],
        )
    try:
        yield None
    finally:
        with connect_db() as db:
            db(
                "UPDATE services SET locked = false WHERE app=(%s) AND pr_number=(%s)",
                [app.name, pr_number],
            )
