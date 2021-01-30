assert False  # don't run this!

import csv
import os
import sys
from datetime import datetime, timedelta

import pytz

sys.path.append(os.path.abspath("../server"))

from common.rpc.auth import read_spreadsheet


from main import app
from models import Section, User, db

staff_reader = read_spreadsheet(
    url="https://docs.google.com/spreadsheets/d/1qHgmwwg_kt3mhQtY3pFFimuAEom1AIxgThQ82_DdoHw/",
    sheet_name=f"Tutor Mapping",
)

student_reader = read_spreadsheet(
    url="https://docs.google.com/spreadsheets/d/1qHgmwwg_kt3mhQtY3pFFimuAEom1AIxgThQ82_DdoHw/",
    sheet_name=f"Student Mapping",
)


pst = pytz.timezone("US/Pacific")

lookup = {}

with app.app_context():
    db.drop_all()
    db.create_all()

    users = {}

    for row in staff_reader[1:]:
        name, email, time, group, is_npe = row
        is_npe = is_npe == "TRUE"
        day, hour_str = time.split(" ")
        if day == "Thu":
            day = 21
        elif day == "Wed":
            day = 20
        else:
            assert False, f"Unknown day {day}"

        hour = int(hour_str[:-2])
        if hour_str[-2:] == "PM" and hour != 12:
            hour += 12

        start_time = pst.localize(
            datetime(year=2021, month=1, day=day, hour=hour, minute=10)
        )
        end_time = start_time + timedelta(minutes=50)

        if email not in users:
            users[email] = User(email=email, name=name, is_staff=True)

        section = Section(
            id=group,
            start_time=start_time.timestamp(),
            end_time=end_time.timestamp(),
            capacity=9,
            staff=users[email],
        )

        if is_npe:
            section.tags = ["NPE"]

        lookup[group] = section

        db.session.add(section)

    for row in student_reader[1:]:
        name, email, time, group, npe = row
        lookup[group].students.append(User(email=email, name=name, is_staff=False))

    db.session.commit()
