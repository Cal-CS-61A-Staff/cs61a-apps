import os
import pandas as pd
import requests

from common.rpc.howamidoing import upload_grades
from common.rpc.auth import read_spreadsheet

ROSTER = "data/roster.csv"
GRADES = "data/okpy_grades.csv"
MT1 = "data/mt1.csv"  # midterm scores from Gradescope
MT2 = "data/mt2.csv"  # midterm scores from Gradescope
TUTORIALS = "data/tutorials.csv"  # tutorial scores from tutorials.cs61a.org

# ---------------------------

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# helpful functions
def csv(name):
    return pd.read_csv(os.path.join(__location__, name), dtype={"sid": str, "SID": str})


def web_csv(url, sheet):
    resp = read_spreadsheet(url=url, sheet_name=sheet)
    cols = resp[0]
    data = [x[: len(cols)] for x in resp[1:]]
    return pd.DataFrame(data, columns=cols)


# exam recovery calculations
def attendance(row):
    return row["Tutorial Attendance (Raw)"]  # special formula for FA20 restructure


#    return sum(row["Discussion {} (Total)".format(i)] for i in range(1, 13) if i != 8)


def exam_recovery(your_exam_score, attendance, max_exam_score, cap=10):
    if your_exam_score == 0:
        return 0
    half_score = max_exam_score / 2
    max_recovery = max(0, (half_score - your_exam_score) / 2)
    recovery_ratio = min(attendance, cap) / cap
    return max_recovery * recovery_ratio


def assemble(gscope, recovery=False, sections=False, adjustments=[]):
    print("Loading scores data...")
    roster = csv(ROSTER).rename(columns={"sid": "SID", "email": "Email"})
    grades = csv(GRADES)

    # Fall 2020 Tutorials
    if sections:
        tutorials = csv(TUTORIALS)
        tutorials = tutorials.fillna(0)
        grades = pd.merge(grades, tutorials, how="left", on="Email")

        grades["Tutorial Attendance (Raw)"] = grades[
            ["Tutorial Attendance (Total)", "Tutorial Attendance CS Scholars (Total)"]
        ].values.max(1)
        grades = grades.drop(
            [
                "Tutorial Attendance (Total)",
                "Tutorial Attendance CS Scholars (Total)",
                "Tutorial Attendance (Might be outdated, check tutorials.cs61a.org and howamidoing.cs61a.org) (Total)",
            ],
            axis=1,
        )

    if gscope:
        for name in gscope:
            scores = csv(f"data/{name}.csv")[["SID", "Total Score"]]
            scores = scores.fillna(0)
            grades = pd.merge(grades, scores, how="left", on="SID").rename(
                columns={"Total Score": f"{gscope[name]} (Raw)"}
            )

    out = pd.merge(roster, grades, how="left", on="Email")
    columns = [*grades.columns, "name"]

    if recovery:
        print("Calculating recovery points...")
        if "mt1" in gscope:
            out["Midterm 1 (Recovery)"] = out.apply(
                lambda row: exam_recovery(row["Midterm 1 (Raw)"], attendance(row), 40),
                axis=1,
            )
            columns.append("Midterm 1 (Recovery)")

        if "mt2" in gscope:
            out["Midterm 2 (Recovery)"] = out.apply(
                lambda row: exam_recovery(row["Midterm 2 (Raw)"], attendance(row), 50),
                axis=1,
            )
            columns.append("Midterm 2 (Recovery)")

    out = out.rename(columns={"SID_x": "SID"})

    if adjustments:
        print("Applying adjustments...")
        adj = web_csv(*adjustments)
        adj = adj.fillna(0)
        out = pd.merge(out, adj, how="left", on="Email")
        columns.append(adj.columns[1:])

    # finalize
    out = out[columns]

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
