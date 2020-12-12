# Fall 2020 Sequence of Actions

import os, roster_export, okpy_export, sys
import gs_export, sections_export, assemble

from typing import List, Tuple

from common.rpc.auth import get_endpoint
from common.db import connect_db

if not os.path.exists("data"):
    try:
        os.makedirs("data")
    except FileExistsError as e:
        print("Data folder exists, false alarm!")

sections = "fa20" in get_endpoint(course="cs61a")

with connect_db() as db:
    gscope: List[Tuple[str, str]] = db(
        "SELECT name, gs_code FROM gscope",
        [],
    ).fetchall()
    acadh: List[Tuple[str, str]] = db(
        "SELECT url, sheet FROM acadh",
        [],
    ).fetchall()


def update():
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
    adj = list(acadh[0]) if acadh else []
    assemble.assemble(
        gscope=gs_assignments, recovery=True, sections=sections, adjustments=adj
    )

    print("=================================================")


if __name__ == "__main__":
    update()
