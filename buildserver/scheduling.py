import sys
from datetime import timedelta
from time import time
from typing import Dict, List, Optional

from common.db import connect_db
from common.rpc.auth import post_slack_message
from common.rpc.paste import get_paste_url, paste_text
from github_utils import BuildStatus, update_status

BUILD_TIME = timedelta(minutes=20).total_seconds()

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS builds (
    unix int,
    app varchar(128),
    pr_number int,
    status varchar(128),
    packed_ref varchar(256),
    url varchar(256),
    log_url varchar(256),
    build_limit_time int
);
"""
    )

"""
Each pushed_ref corresponds to a particular commit.
For each (app, pr_number) tuple, there will be a number of rows, at most one row per packed_ref.
There will be some number of rows with status = success or failure, at most one with status = building,
at most one with status = queued, and some number with status = pushed. 
"""

TARGETS_BUILT_ON_WORKER = ["website-base"]


def enqueue_builds(
    targets: List[str],
    pr_number: int,
    packed_ref: str,
) -> Dict[str, List[str]]:
    """
    Returns a map of packed_ref -> List[app_name] containing those apps that can now be built,
    and enqueues the rest to be built when the blocking buildserver run terminates
    """

    with connect_db() as db:
        # Before anything, we need to clear any stalled builds
        db(
            "UPDATE builds SET status='failure' WHERE status='building' AND build_limit_time < %s",
            [time()],
        )
        # First, we enqueue all our current targets
        for target in targets:
            status = db(
                "SELECT status FROM builds WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                [
                    target,
                    pr_number,
                    packed_ref,
                ],
            ).fetchone()
            if status == BuildStatus.building.name:
                # no need to start a second build for the same (app, packed_ref)
                continue

            # enqueues itself and dequeues anyone else who is queued
            db(
                "UPDATE builds SET status='pushed' WHERE app=%s AND pr_number=%s AND packed_ref!=%s AND status='queued'",
                [target, pr_number, packed_ref],
            )
            if status is None:
                # we have just been pushed or manually triggered
                db(
                    "INSERT INTO builds VALUES (%s, %s, %s, 'queued', %s, NULL, NULL, NULL)",
                    [time(), target, pr_number, packed_ref],
                )
            else:
                db(
                    "UPDATE builds SET status='queued' WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                    [target, pr_number, packed_ref],
                )

    # force db flush
    with connect_db() as db:
        # Then, we dequeue any target that is now ready to be built
        can_build_list = []
        queued = db(
            "SELECT app, packed_ref FROM builds WHERE status='queued'",
        ).fetchall()
        for app, packed_ref in queued:
            if app in TARGETS_BUILT_ON_WORKER:
                # we can only build one target on the worker at a time, even if it will deploy to a different service
                conflicts = db(
                    "SELECT * FROM builds WHERE app=%s AND status='building'",
                    [app],
                ).fetchall()
            else:
                conflicts = db(
                    "SELECT * FROM builds WHERE app=%s AND pr_number=%s AND status='building'",
                    [app, pr_number],
                ).fetchall()

            if conflicts:
                # cannot build app, because someone else is currently building
                continue
            else:
                # we can build now!
                db(
                    "UPDATE builds SET status='building', build_limit_time=%s WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                    [time() + BUILD_TIME, app, pr_number, packed_ref],
                )
                can_build_list.append((app, packed_ref))

    # group output by packed_ref for convenience of caller
    can_build = {}
    for app, packed_ref in can_build_list:
        if packed_ref not in can_build:
            can_build[packed_ref] = []
        can_build[packed_ref].append(app)
    for packed_ref in set(packed_ref for app, packed_ref in queued):
        update_status(packed_ref, pr_number)
    return can_build


def report_build_status(
    target: str,
    pr_number: int,
    packed_ref: str,
    status: BuildStatus,
    url: Optional[str],
    log_data: Optional[str],
    *,
    private: bool
):
    try:
        log_url = get_paste_url(
            paste_text(data=log_data, is_private=private, retries=3)
        )
    except Exception:
        print(log_data, file=sys.stderr)
        print("Paste failure, logs were dumped to stdout", file=sys.stderr)
        try:
            post_slack_message(
                course="cs61a",
                message="Paste failed on buildserver, continuing anyway, please check logs ASAP",
                purpose="infra",
            )
        except:
            pass
        log_url = "https://logs.cs61a.org/service/buildserver"

    with connect_db() as db:
        existing = db(
            "SELECT * FROM builds WHERE app=%s AND pr_number=%s AND packed_ref=%s",
            [
                target,
                pr_number,
                packed_ref,
            ],
        ).fetchone()

        build_limit_time = (
            time() + BUILD_TIME if status == BuildStatus.building else None
        )

        if not existing:
            # we have just been pushed or manually triggered
            db(
                "INSERT INTO builds VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    time(),
                    target,
                    pr_number,
                    status.name,
                    packed_ref,
                    url,
                    log_url,
                    build_limit_time,
                ],
            )
        else:
            db(
                "UPDATE builds SET status=%s, url=%s, log_url=%s, build_limit_time=%s "
                "WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                [
                    status.name,
                    url,
                    log_url,
                    build_limit_time,
                    target,
                    pr_number,
                    packed_ref,
                ],
            )
    update_status(
        packed_ref,
        pr_number,
    )
