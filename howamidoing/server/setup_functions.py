import csv
from io import StringIO
import json
import datetime


def set_default_config(db):
    """Sets the configuration to the default configuration, found in
    ``public/config/config.js``.

    :param db: A database query function yielded by :func:`common.db.connect_db`
    :type db: func

    :return: None
    """
    with open("./public/config/config.js") as config:
        data = config.read()
    db("DELETE FROM configs WHERE courseCode=%s", ["cs61a"])
    db("INSERT INTO configs VALUES (%s, %s)", ["cs61a", data])


def set_grades(data, course_code, db):
    """Sets the grades for a particular course based on some input
    ``grades.csv`` file. An example can be found in
    ``public/config/dummy_grade_data.csv``.

    :param data: The contents of a ``grades.csv`` file.
    :type data: str

    :param course_code: The course to set grades for (e.g. 'cs61a').
    :type course_code: str

    :param db: A database query function yielded by :func:`common.db.connect_db`
    :type db: func

    :return: None
    """
    reader = csv.reader(StringIO(data))
    header = next(reader)
    email_index = header.index("Email")
    db("DELETE FROM students WHERE courseCode=%s", [course_code])
    db("DELETE FROM headers WHERE courseCode=%s", [course_code])
    db("INSERT INTO headers VALUES (%s, %s)", [course_code, json.dumps(header)])

    data = []
    for row in reader:
        short_data = {x: row[header.index(x)] for x in ["Email", "SID", "Name", "TA"]}
        data.append(
            [course_code, row[email_index], json.dumps(short_data), json.dumps(row)]
        )
    db(
        "INSERT INTO students VALUES (%s, %s, %s, %s)",
        data,
    )

    db("DELETE FROM lastUpdated WHERE courseCode=%s", [course_code])
    db(
        "INSERT INTO lastUpdated VALUES (%s, %s)",
        [course_code, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    )
