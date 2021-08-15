from time import time
from datetime import timedelta

from common.db import connect_db
from common.jobs import job
from common.rpc.buildserver import deploy_prod_app_sync

AUTO_REBUILDS = {
    "website-base": timedelta(hours=1),
    "cs170-website": timedelta(hours=1),
}

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS auto_rebuilds (
    app varchar(128),
    unix integer  
)"""
    )


def create_rebuilder(app):
    @job(app, "rebuilder")
    def rebuilder():
        now = int(time())
        for app, interval in AUTO_REBUILDS.items():
            with connect_db() as db:
                last_rebuild = db(
                    "SELECT MAX(unix) FROM auto_rebuilds WHERE app=(%s)", [app]
                ).fetchone()
                if (
                    not last_rebuild
                    or not last_rebuild[0]
                    or now - last_rebuild[0] > interval.total_seconds()
                ):
                    db(
                        "INSERT INTO auto_rebuilds (app, unix) VALUES (%s, %s)",
                        [app, now],
                    )
                    deploy_prod_app_sync(target_app=app, noreply=True)
