from app_config import App, WEB_DEPLOY_TYPES
from common.db import connect_db


def update_config(app: App, pr_number: int):
    with connect_db() as db:
        db(
            "DELETE FROM services WHERE app=(%s) AND pr_number=(%s)",
            [app.name, pr_number],
        )
        db(
            "INSERT INTO services VALUES (%s, %s, %s, %s)",
            [app.name, pr_number, False, app.config["deploy_type"] in WEB_DEPLOY_TYPES],
        )
