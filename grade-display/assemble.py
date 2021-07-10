import os
import pandas as pd
import numpy as np
import requests

from common.rpc.howamidoing import upload_grades
from common.rpc.auth import read_spreadsheet

ROSTER = "data/roster.csv"
GRADES = "data/okpy_grades.csv"
MT1 = "data/mt1.csv"  # midterm scores from Gradescope
MT2 = "data/mt2.csv"  # midterm scores from Gradescope
SECTIONS = "data/sections.csv"  # section scores from sections.cs61a.org

# ---------------------------

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# helpful functions
def csv(name):
    return pd.read_csv(os.path.join(__location__, name), dtype={"sid": str, "SID": str})


def web_csv(url, sheet):
    resp = read_spreadsheet(url=url, sheet_name=sheet)
    cols = resp[0]
    data = [x[: len(cols)] for x in resp[1:]]
    for row in data:
        while len(row) < len(cols):
            row.append(0)
    return pd.DataFrame(data, columns=cols)


# exam recovery calculations
def attendance(row):
    return row["Section Attendance (Total)"]


def exam_recovery(your_exam_score, attendance, max_exam_score, cap=10):
    if your_exam_score == 0:
        return 0
    half_score = max_exam_score / 2
    max_recovery = max(0, (half_score - your_exam_score) / 2)
    recovery_ratio = min(attendance, cap) / cap
    return max_recovery * recovery_ratio


def assemble(gscope, recovery=False, adjustments=[]):
    print("Loading scores data...")
    roster = csv(ROSTER).rename(columns={"sid": "SID", "email": "Email"})
    grades = csv(GRADES)

    if gscope:
        for name in gscope:
            scores = csv(f"data/{name}.csv")[["SID", "Total Score"]]
            scores = scores.fillna(0)
            grades = (
                pd.merge(grades, scores, how="left", on="SID")
                .rename(columns={"Total Score": f"{gscope[name]} (Raw)"})
                .fillna(0)
            )

    if adjustments:
        print("Applying adjustments...")
        for url, sheet in adjustments:
            adj = web_csv(url, sheet)
            for col in adj.columns[1:]:
                adj[col] = pd.to_numeric(adj[col])
            adj = adj.replace("", np.nan).fillna(0)
            grades = pd.merge(grades, adj, how="left", on="Email").fillna(0)

    print("Adding section attendance...")
    sections = csv(SECTIONS).replace("", np.nan).fillna(0)
    grades = pd.merge(grades, sections, how="left", on="Email").fillna(0)

    # in su21, grant everyone points for discussion 0
    grades['Discussion 0'] = 1.0

    if recovery:
        print("Calculating recovery points...")
        if "mt1" in gscope:
            grades["Midterm 1 (Recovery)"] = grades.apply(
                lambda row: exam_recovery(row["Midterm 1 (Raw)"], attendance(row), 40),
                axis=1,
            )

        if "mt2" in gscope:
            grades["Midterm 2 (Recovery)"] = grades.apply(
                lambda row: exam_recovery(row["Midterm 2 (Raw)"], attendance(row), 50),
                axis=1,
            )

        if "mt" in gscope:
            grades["Midterm (Recovery)"] = grades.apply(
                lambda row: exam_recovery(row["Midterm (Raw)"], attendance(row), 55),
            )

    out = pd.merge(roster, grades, how="left", on="Email")
    columns = [*grades.columns, "name"]
    out = out.rename(columns={"SID_x": "SID"})

    # finalize
    out = out[columns]
    out["TA"] = ""
    out = out.replace("", np.nan)

    finalized = out.fillna(0)
    finalized = finalized.rename(columns={"name": "Name"})
    finalized = finalized.applymap(lambda x: 1 if x == "Yes" else 0 if x == "No" else x)

    print("Writing to file...")
    finalized.to_csv("data/grades.csv", index=False)

    print("Uploading data to Howamidoing...")
    upload = finalized.to_csv(index=False)
    upload_grades(data=upload)
    print("Done.")


if __name__ == "__main__":
    assemble()
