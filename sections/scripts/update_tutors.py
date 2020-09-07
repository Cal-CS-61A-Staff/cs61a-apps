import csv
import os
import sys
from datetime import datetime, timedelta

import pytz

sys.path.append(os.path.abspath("../server"))

from common.rpc.auth import read_spreadsheet
from main import app
from models import Section, User, db

hour = 4
min = 30

reader = read_spreadsheet(
    url="https://docs.google.com/spreadsheets/d/1S10VeClOIzcMaEQcRrdzdUl_NCLFNX3YeyK9Z3DXn1U/",
    sheet_name=f"'{hour}:{min+5:02}'",
)

pst = pytz.timezone("US/Pacific")

start_time = pst.localize(
    datetime(year=2020, month=8, day=26, hour=hour + 12, minute=min + 5)
)
end_time = start_time + timedelta(minutes=25)

users = {}


def get_user(email, name):
    if email in users:
        return users[email]
    user = User.query.filter_by(email=email).one_or_none()
    if user is None:
        user = User(email=email, name=name, is_staff=True)
    users[email] = user
    return user


with app.app_context():
    sections = Section.query.filter_by(
        staff=None, start_time=start_time.timestamp(), end_time=end_time.timestamp()
    ).all()

    sections_by_npe = [[], []]
    for section in sections:
        sections_by_npe[section.tag_string == "NPE"].append(section)

    print([len(sections) for sections in sections_by_npe])

    for row in reader:
        if not row:
            break
        if row[0] != "FALSE":
            continue
        assert len(row) == 11
        npe = row[-2] == "TRUE"
        if row[-1] == "TRUE":
            print("Reassigning empty section to tutor: {}, NPE: {}".format(row[1], npe))
            section = sections_by_npe[npe].pop()
            section.staff = get_user(row[2], row[1])

        else:
            print("Creating new section with tutor: {}, NPE: {}".format(row[1], npe))

            section = Section(
                start_time=start_time.timestamp(),
                end_time=end_time.timestamp(),
                capacity=5,
                staff=get_user(row[2], row[1]),
            )

            if npe:
                section.tags = ["NPE"]

            db.session.add(section)

    db.session.commit()
