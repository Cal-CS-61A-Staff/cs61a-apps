from time import time
from typing import Dict, List, Optional

from common.db import connect_db
from github_utils import BuildStatus, update_status


with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS builds (
    unix int,
    app varchar(128),
    pr_number int,
    status varchar(128),
    packed_ref varchar(256),
    url varchar(256)
);
"""
    )


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
            if status is None:
                # we have just been pushed or manually triggered
                db(
                    "INSERT INTO builds VALUES (%s, %s, %s, 'queued', %s, NULL)",
                    [time(), target, pr_number, packed_ref],
                )
            else:
                status = BuildStatus(status[0])
                if status == BuildStatus.building:
                    # no need to start a second build for the same (app, packed_ref)
                    continue
                # enqueues itself and dequeues anyone else who is queued
                db(
                    "UPDATE builds SET status='pushed' WHERE app=%s AND pr_number=%s AND packed_ref!=%s AND status='queued'",
                    [target, pr_number, packed_ref],
                )
                db(
                    "UPDATE builds SET status='queued' WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                    [target, pr_number, packed_ref],
                )

        # Then, we dequeue any target that is now ready to be built
        can_build_list = []
        queued = db(
            "SELECT app, packed_ref FROM builds WHERE pr_number=%s AND status='queued'"
        ).fetchall()
        # sanity check that there are no duplicate apps
        assert len(queued) == len({app for app, _ in queued})
        for app, packed_ref in queued:
            conflicts = db(
                "SELECT * FROM builds WHERE app=%s AND pr_number=%s AND status='building'"
            ).fetchall()
            if conflicts:
                # cannot build app, because someone else is currently building
                continue
            else:
                # we can build now!
                db(
                    "UPDATE builds SET status='building' WHERE app=%s AND pr_number=%s AND packed_ref=%s",
                    [app, pr_number, packed_ref],
                )
                can_build_list.append((app, packed_ref))

    # group output by packed_ref for convenience of caller
    can_build = {}
    for app, packed_ref in can_build_list:
        if packed_ref not in can_build:
            can_build[packed_ref] = []
        can_build[packed_ref].append(app)
    for packed_ref in can_build:
        update_status(packed_ref, pr_number)
    return can_build


def report_build_status(
    target: str,
    pr_number: int,
    packed_ref: str,
    status: BuildStatus,
    url: Optional[str],
):
    with connect_db() as db:
        db(
            "UPDATE builds SET status=%s AND url=%s WHERE app=%s AND pr_number=%s AND packed_ref=%s",
            [status.name, url, target, pr_number, packed_ref],
        )
    update_status(
        packed_ref,
        pr_number,
    )
