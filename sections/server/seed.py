from datetime import datetime, timedelta
from os import getenv
from random import choice

import pytz

from main import app
from models import Section, User, db


def seed():
    if getenv("ENV") == "prod":
        return
    with app.app_context():
        db.drop_all()
        db.create_all()
        pst = pytz.timezone("US/Pacific")
        sections = []
        for i in range(100):
            t = pst.localize(
                datetime(year=2020, month=8, day=20, hour=i % 10, minute=0, second=0)
            )
            section = Section(
                description=f"This is the {i}th demo section.",
                start_time=t.timestamp(),
                end_time=(t + timedelta(minutes=30)).timestamp(),
                capacity=5,
            )
            section.tags = ["NPE"]
            sections.append(section)
            db.session.add(section)

        users = []
        for i in range(200):
            section = choice(sections)
            user = User(
                email=f"gobears{i}@berkeley.edu",
                name=f"Oski {i}th of his name",
                is_staff=False,
            )
            user.sections = [section]
            users.append(user)

        db.session.commit()


if __name__ == "__main__":
    seed()
