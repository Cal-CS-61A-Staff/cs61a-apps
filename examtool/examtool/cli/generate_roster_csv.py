import csv
import os
from collections import namedtuple
from datetime import datetime
from os import getenv

import click
import pytz
import requests

TARGET = "https://docs.google.com/spreadsheets/d/1YAHnp7gwGwvfctDYIqFM3OFCQTlp_eY81lD2bq5how8/edit"
SHEET = "Exam #3"

AUTH_KEY = getenv("AUTH_KEY")
AUTH_SECRET = getenv("AUTH_SECRET")

EXAM_STARTS = {
    1588367400: "cs61a-friday-final",  # Fri 2:10PM
    1588410600: "cs61a-friday-final-alt",  # Sat 2:10AM
    1588392600: "cs61a-friday-final-alt-2",  # Fri 9:10PM
    1588399800: "cs61a-friday-final-alt-3",  # Fri 11:10PM
    1588417800: "cs61a-friday-final-alt-4",  # Sat 4:10AM
    1588443000: "cs61a-friday-final-alt-5",
}

Student = namedtuple("Student", ["exam", "deadline"])


def get_unix_timestamp(date_str, time_str):
    date = datetime.strptime(date_str + " " + time_str, "%a %m/%d %I:%M %p")
    date = date.replace(year=2020)
    date = pytz.timezone("America/Los_Angeles").localize(date)
    return int(date.timestamp())


@click.command()
@click.option("--out", default="rosters", prompt=True, type=click.Path())
def main(out):
    data = requests.post(
        "https://auth.apps.cs61a.org/google/read_spreadsheet",
        json={
            "url": TARGET,
            "sheet_name": SHEET,
            "client_name": AUTH_KEY,
            "secret": AUTH_SECRET,
        },
    ).json()

    headers = data[0]

    email_index = headers.index("Email")
    start_time_index = headers.index("Start Time")
    start_date_index = headers.index("Start Date")
    end_time_index = headers.index("End Time")
    end_date_index = headers.index("End Date")

    students = {}

    for row in data[1:]:
        if not row:
            continue
        start_time = get_unix_timestamp(row[start_date_index], row[start_time_index])
        end_time = get_unix_timestamp(row[end_date_index], row[end_time_index])

        if start_time not in EXAM_STARTS:
            raise Exception(
                "Unexpected start_time = {}, {} {}".format(
                    start_time, row[start_date_index], row[start_time_index]
                )
            )

        students[row[email_index]] = Student(
            exam=EXAM_STARTS[start_time], deadline=end_time
        )

    for exam in EXAM_STARTS.values():
        with open(
            os.path.join(out, exam.replace("-", "_").split("_", 1)[1] + "_roster.csv"),
            "w",
        ) as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Email", "Deadline"])
            for email, student in students.items():
                if student.exam == exam:
                    writer.writerow([email, student.deadline])
                else:
                    writer.writerow([email, 0])


if __name__ == "__main__":
    main()
