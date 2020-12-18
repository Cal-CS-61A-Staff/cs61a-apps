import pandas as pd
import numpy as np

from common.rpc.howamidoing import download_grades


def export():
    grades_json = download_grades()
    df = pd.DataFrame(grades_json["scores"], columns=grades_json["header"])
    df = df.apply(pd.to_numeric, errors="ignore")

    df["Midterm 1"] = df["Midterm 1 (Raw)"] + df["Midterm 1 (Recovery)"]
    df["Midterm 2"] = df["Midterm 2 (Raw)"] + df["Midterm 2 (Recovery)"]
    df["Exams"] = df["Midterm 1"] + df["Midterm 2"]

    hw_calc = lambda row: min(
        18, np.sum([row[f"Homework {i} (Total)"] for i in range(1, 11)])
    )
    df["Homework"] = df.apply(hw_calc, axis=1)

    df["Hog Project"] = (
        df["Hog (Total)"] + df["Hog (Checkpoint 1)"] + df["Hog (Composition)"]
    )
    df["Cats Project"] = (
        df["Cats (Total)"] + df["Cats (Checkpoint 1)"] + df["Cats (Composition)"]
    )
    df["Ants Project"] = (
        df["Ants (Total)"] + df["Ants (Checkpoint 1)"] + df["Ants (Composition)"]
    )

    def scheme_calc(row):
        scheme_raw = (
            row["Scheme (Total)"]
            + row["Scheme (Checkpoint 1)"]
            + row["Scheme (Checkpoint 2)"]
        )
        return max(scheme_raw, row["Scheme Challenge Version (Total)"])

    df["Scheme Project"] = df.apply(scheme_calc, axis=1)
    df["Projects"] = (
        df["Hog Project"]
        + df["Cats Project"]
        + df["Ants Project"]
        + df["Scheme Project"]
    )

    lab_calc = lambda row: min(
        11, np.sum([row[f"Lab {i} (Total)"] for i in range(1, 15) if i != 3])
    )
    df["Lab"] = df.apply(lab_calc, axis=1)

    dis_calc = lambda row: min(6, row["Tutorial Attendance (Raw)"])
    df["Discussion"] = df.apply(dis_calc, axis=1)

    df["Adjustments"] = (
        df["Hog Contest"]
        + df["Academic Dishonesty Penalty"]
        + df["Homework 10 Extra Credit Point (Total)"]
    )

    df["Raw Score"] = (
        df["Exams"]
        + df["Homework"]
        + df["Projects"]
        + df["Lab"]
        + df["Discussion"]
        + df["Adjustments"]
    )

    return df.to_csv(index=False)
