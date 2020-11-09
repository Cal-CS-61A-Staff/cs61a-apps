from app_config import App
from common.db import connect_db


def update_config(app: App, pr_number: int):
    if pr_number == 0:
        with connect_db() as db:
            db("DELETE FROM apps WHERE app=%s", [app.name])
            if app.config["repo"]:
                db(
                    "INSERT INTO apps (app, repo, autobuild) VALUES (%s, %s, %s)",
                    [app.name, app.config["repo"], True],
                )
