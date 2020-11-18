import os
import pandas as pd
import requests

from common.rpc.secrets import get_secret

ROSTER = "data/roster.csv"
GRADES = "data/okpy_grades.csv"
MT1 = "data/mt1.csv"             # midterm scores from Gradescope
MT2 = "data/mt2.csv"             # midterm scores from Gradescope
TUTORIALS = "data/tutorials.csv" # tutorial scores from tutorials.cs61a.org

UPLOAD_SECRET = get_secret(secret_name="HAID_SECRET")
ENDPOINT = "https://howamidoing.cs61a.org/setGradesSecret"

# ---------------------------

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# helpful functions
def csv(name):
    return pd.read_csv(os.path.join(__location__, name), dtype={"sid": str, "SID": str})

# exam recovery calculations
def attendance(row):
    return row["Tutorial Attendance (Total)"] # special formula for FA20 restructure
#    return sum(row["Discussion {} (Total)".format(i)] for i in range(1, 13) if i != 8)

def exam_recovery(your_exam_score, attendance, max_exam_score, cap=10):
    if your_exam_score == 0:
        return 0
    half_score = max_exam_score / 2
    max_recovery = max(0, (half_score - your_exam_score) / 2)
    recovery_ratio = min(attendance, cap) / cap
    return max_recovery * recovery_ratio

def assemble(haid=True):
    print("Loading scores data...")
    roster = csv(ROSTER).rename(columns={"sid": "SID", "email": "Email"})
    grades = csv(GRADES)

    grades = grades.drop("Tutorial Attendance (Total)", axis=1)

    # Fall 2020 Tutorials
    tutorials = csv(TUTORIALS)
    tutorials.fillna(0)
    grades = pd.merge(grades, tutorials, how="left", on="Email")

    # Fall 2020 Midterm 1
    mt1 = csv(MT1)[["SID", "Total Score"]]
    mt1.fillna(0)
    grades = pd.merge(grades, mt1, how="left", on="SID").rename(
        columns={
            "Total Score": "Midterm 1 (Raw)"
        }
    )

    # Fall 2020 Midterm 2
    mt2 = csv(MT2)[["SID", "Total Score"]]
    mt2.fillna(0)
    grades = pd.merge(grades, mt2, how="left", on="SID").rename(
        columns={
            "Total Score": "Midterm 2 (Raw)"
        }
    )

    out = pd.merge(roster, grades, how="left", on="Email")


    print("Calculating recovery points...")
    out["Midterm 1 (Recovery)"] = out.apply(
        lambda row: exam_recovery(row["Midterm 1 (Raw)"], attendance(row), 40), axis=1
    )

    out["Midterm 2 (Recovery)"] = out.apply(
        lambda row: exam_recovery(row["Midterm 2 (Raw)"], attendance(row), 50), axis=1
    )

    out = out.rename(columns={"SID_x": "SID"})

    # finalize
    out = out[
        [*grades.columns, "name", "Midterm 1 (Recovery)", "Midterm 2 (Recovery)"]
    ]

    finalized = out.fillna(0)
    finalized = finalized.rename(columns={"name": "Name"})
    finalized = finalized.applymap(lambda x: 1 if x == "Yes" else 0 if x == "No" else x)

    print("Writing to file...")
    finalized.to_csv('data/grades.csv', index=False)

    if haid:
        print("Uploading data to Howamidoing...")
        upload = finalized.to_csv(index=False)
        print(requests.post(ENDPOINT, {"secret": UPLOAD_SECRET, "data": upload}).text)

if __name__ == "__main__":
    assemble()
