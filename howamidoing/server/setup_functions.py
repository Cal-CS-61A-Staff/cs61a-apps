import csv
from io import StringIO
import json
import datetime


def set_default_config(db):
    with open("./public/config/config.js") as config:
        data = config.read()
    db("DELETE FROM configs WHERE courseCode=%s", ["cs61a"])
    db("INSERT INTO configs VALUES (%s, %s)", ["cs61a", data])


def set_grades(data, course_code, db):
    reader = csv.reader(StringIO(data))
    header = next(reader)
    email_index = header.index("Email")
    db("DELETE FROM students WHERE courseCode=%s", [course_code])
    db("DELETE FROM headers WHERE courseCode=%s", [course_code])
    db("INSERT INTO headers VALUES (%s, %s)", [course_code, json.dumps(header)])
    for row in reader:
        short_data = {x: row[header.index(x)] for x in ["Email", "SID", "Name"]}
        db(
            "INSERT INTO students VALUES (%s, %s, %s, %s)",
            [course_code, row[email_index], json.dumps(short_data), json.dumps(row)],
        )
    db("DELETE FROM lastUpdated WHERE courseCode=%s", [course_code])
    db(
        "INSERT INTO lastUpdated VALUES (%s, %s)",
        [course_code, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    )
