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
        if pr_number == 0:
            db("DELETE FROM apps WHERE app=%s", [app.name])
            if app.config["repo"]:
                db(
                    "INSERT INTO apps (app, repo, autobuild) VALUES (%s, %s, %s)",
                    [app.name, app.config["repo"], True],
                )
