from common.rpc.sections import rpc_export_attendance
from datetime import datetime, timedelta
import json
import pandas as pd

FIRST_DISCS = [
    datetime(year=2021, month=6, day=22, hour=0).timestamp(),
    datetime(year=2021, month=6, day=24, hour=0).timestamp(),
]
WEEKS = 8


def export():
    print("Getting section attendance...")

    raw = json.loads(rpc_export_attendance(full=True)["custom"]["attendances"])
    sections = pd.DataFrame()

    for student, data in raw.items():
        curr_week, csv = 0, {}
        starts = FIRST_DISCS[:]
        while curr_week < WEEKS * len(FIRST_DISCS):
            if all([start > datetime.now().timestamp() for start in starts]):
                # short circuit to avoid pointlessly checking future weeks
                curr_week = WEEKS * len(FIRST_DISCS)
                continue
            for i in range(len(starts)):
                start = starts[i]
                end = start + timedelta(hours=47).total_seconds()
                attended = any(
                    [
                        start <= log["start_time"] <= end
                        for log in data
                        if log["status"] == "present"
                    ]
                )
                csv[f"Discussion {curr_week}"] = int(attended)
                curr_week += 1
                starts[i] = start + timedelta(days=7).total_seconds()
        sections = sections.append({"Email": student, **csv}, ignore_index=True)

    print("Saving section attendance...")
    sections.to_csv("data/sections.csv", index=False)
    print("Done.")


if __name__ == "__main__":
    export()
