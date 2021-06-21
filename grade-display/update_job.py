# Spring 2021 Sequence of Actions

import os, roster_export, okpy_export, sys
import gs_export, sections_export, assemble

from typing import List, Tuple

from common.rpc.auth import get_endpoint
from common.db import connect_db


def update(recovery=False):
    if not os.path.exists("data"):
        try:
            os.makedirs("data")
        except FileExistsError as e:
            print("Data folder exists, false alarm!")

    sections = "sp21" in get_endpoint(course="cs61a")

    with connect_db() as db:
        gscope: List[Tuple[str, str]] = db(
            "SELECT name, gs_code FROM gscope",
            [],
        ).fetchall()
        adjustments: List[Tuple[str, str]] = db(
            "SELECT url, sheet FROM adjustments",
            [],
        ).fetchall()

    print("=================================================")
    roster_export.export()

    print("=================================================")
    okpy_export.export()

    gs_assignments = {}

    if not gscope:
        print("No Gradescope assignments found!", file=sys.stderr)

    for name, gs_code in gscope:
        print("=================================================")
        full_name = gs_export.export(name, gs_code)
        if full_name:
            gs_assignments[name] = full_name
        else:
            print(
                f"Gradescope export for '{name} ({gs_code})' failed.", file=sys.stderr
            )

    if sections:
        print("=================================================")
        sections_export.export()

    print("=================================================")
    assemble.assemble(
        gscope=gs_assignments,
        recovery=recovery,
        sections=sections,
        adjustments=adjustments,
    )

    print("=================================================")


if __name__ == "__main__":
    update()
