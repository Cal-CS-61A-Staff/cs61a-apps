assert False  # don't run this!

import csv
import os
import sys
from datetime import datetime, timedelta

import pytz

sys.path.append(os.path.abspath("../server"))

from main import app
from models import Section, User, db

with open("tutor_assignments.csv") as f:
    reader = list(csv.reader(f))

pst = pytz.timezone("US/Pacific")

lookup = {}

with app.app_context():
    db.drop_all()
    db.create_all()

    users = {}

    for row in reader[1:]:
        name, email, time, group, is_npe = row
        is_npe = is_npe == "TRUE"
        hour, mins = time.split(":")
        hour = int(hour)
        mins = int(mins)
        start_time = pst.localize(
            datetime(year=2020, month=8, day=26, hour=hour + 12, minute=mins)
        )
        end_time = start_time + timedelta(minutes=25)

        if email not in users:
            users[email] = User(email=email, name=name, is_staff=True)

        section = Section(
            start_time=start_time.timestamp(),
            end_time=end_time.timestamp(),
            capacity=5,
            staff=users[email],
        )

        if is_npe:
            section.tags = ["NPE"]

        lookup[time, group] = section

        db.session.add(section)

    with open("student_tutorials.csv") as f:
        reader = list(csv.reader(f))

        for row in reader[1:]:
            name, email, time, group = row
            lookup[time, group].students.append(
                User(email=email, name=name, is_staff=False)
            )

    db.session.commit()
