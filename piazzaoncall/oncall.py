import hashlib

import datetime
import numpy as np
import pandas as pd
import pytz
import re
from dateutil.parser import parse

from common.db import connect_db
from common.rpc.auth import piazza_course_id
from piazza import network
from slack import send

STAFF_csv = pd.read_csv("staff_roster.csv")
STAFF = STAFF_csv.loc[STAFF_csv.index.repeat(STAFF_csv.Weight)].reset_index(drop=True)

TIMEZONE = pytz.timezone("America/Los_Angeles")

NIGHT_START, NIGHT_END = datetime.time(0, 30), datetime.time(15, 30)
MORNING = datetime.time(7, 0)


with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS status (
    last_sent INTEGER
)"""
    )
    ret = db("SELECT last_sent FROM status").fetchone()
    if ret is None:
        db("INSERT INTO STATUS (last_sent) VALUES (0)")


class Main:
    def __init__(self):
        with connect_db() as db:
            self.last_sent = datetime.datetime.fromtimestamp(
                db("SELECT last_sent FROM status").fetchone()[0], TIMEZONE
            )
        self.rhtml = re.compile(r"<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")
        self.roncall = re.compile(r"oncall:\s*(\S+)")  # '\[oncall: .*\]'

        self.urgent_threshold = 3
        self.url_starter = f"https://piazza.com/class/{piazza_course_id()}?cid="

    def send_message(self):
        """ Sends a message for all unresolved posts or followups made after
        self.ignore_before. Uses weights column from input CSV to proportionally
        allocate staff members to questions"""
        message, high_priority = "", ""
        # [network.get_post(cid=108)]
        for post in network.list_unresolved():
            post_id = post.get("nr")

            assigned = self.oncall(post)
            if assigned == "ignore":
                print(
                    f"{datetime.datetime.today().date()}: @{post_id} is marked as ignore"
                )
                continue
            elif assigned:
                str = ""
                for email in assigned:
                    str += f"<!{email}> "
                str += f"your assigned post (<{self.url_starter}{post_id}|@{post_id}>) needs help!\n"
                message += str
                continue

            for p in self.select_staff(post):
                # [[email, 61, True], [email2, 61_f1, False]]
                str = f"<!{p[0]}> please help <{self.url_starter}{p[1]}|@{p[1]}>\n"
                if p[2]:
                    high_priority += str
                else:
                    message += str

        if message:
            starter = "Good morning! Here are today's piazza assignments. You will receive a daily reminder "
            + "about your unresolved piazza posts. *If you do not know how to answer your post(s), post in general.*\n\n"
            # print(starter + message)
            send(starter + message, course="cs61a")
        if high_priority:
            starter = f"<!channel> These messages have been unanswered for {self.urgent_threshold} days. "
            + "*If you were assigned one of these posts, reply to this message after you have resolved it.*\n\n"
            # print(starter + high_priority)
            send(starter + high_priority, course="cs61a")

    def oncall(self, post):
        """Returns email of staff member on call if specified in body of instructor piazza post using syntax
        oncall: <bConnected Username> (berkeley email without @berkeley.edu). oncall: IGNORE can be used to tell
        the bot to exclude the post from """
        if not (
            "instructor-question" in post.get("tags")
            or "instructor-note" in post.get("tags")
        ):
            return None
        text = re.sub(self.rhtml, "", post.get("history")[0].get("content"))
        usernames = [u.lower() for u in re.findall(self.roncall, text)]
        if usernames:
            if "ignore" in usernames:
                return "ignore"
            else:
                return [u + "@berkeley.edu" for u in usernames]
        return None

    def select_staff(self, post):
        """Selects staff member(s) for the post. Randomly assigns a staff member to answer the post and any
        unresolved followups (one staff member for the post itself, one additional staff member for each unresolved
        followup. Returns a list of lists each containing three elements:
            1. Staff member email
            2. post_id (Ex: 61, 61_f1)
            3. Boolean indicating priority (True=urgent)
        Urgent post @61 with with unresolved followup @61_f1 would return [[email, 61, True], [email2, 61_f1, False]]"""
        ret_lst = []
        post_id = str(post.get("nr"))
        if post.get("no_answer", False):
            ret_lst.append([self.pick_staff(post_id), post_id, self.is_urgent(post)])
        id = 0
        for child in post.get("children", []):
            if not (child.get("type", "fail") == "followup"):
                continue
            id += 1
            if not child.get("no_answer"):
                continue
            f_id = post_id + "_f" + str(id)
            ret_lst.append([self.pick_staff(f_id), f_id, self.is_urgent(post)])
        return ret_lst

    def pick_staff(self, post_id):
        """Given a post ID, assign a staff member and return staff member's email. Staff members selected from
        STAFF dataframe (imported from staff_roster.csv)"""
        post_hash = sum(
            [ord(c) for c in hashlib.sha224((str(post_id)).encode("utf-8")).hexdigest()]
        )
        staff_index = post_hash % len(STAFF.index)
        return STAFF["email"].iloc[staff_index]

    def is_urgent(self, post):
        """Returns a boolean indicating whether the input post or followup is urgent. For a post to be urgent,
        it must be made after self.ignore_before and more than self.urgent_threshold business days old. For a followup
        to be urgent, it must be made after self.ignore_before and its NEWEST reply must be more than
        self.urgent_threshold business days old. Notes are never urgent, but their followups can be. """
        kind = post.get("type")
        if kind == "note":
            return False
        if kind == "question":
            newest = parse(post.get("created", "2001-08-27T04:53:21Z")).date()
        elif kind == "followup":
            children = post.get("children", [])
            if children:
                newest = parse(
                    children[-1].get("created", "2001-08-27T04:53:21Z")
                ).date()
            else:
                newest = post.get("created", "2001-08-27T04:53:21Z").date()
        else:
            print("Unknown post type: " + post.get("type"))
            newest = parse("2001-08-27T04:53:21Z").date()
        today = datetime.datetime.utcnow().date()
        return np.busday_count(newest, today) >= self.urgent_threshold

    def run(self):
        tod_in_ca = datetime.datetime.now(tz=TIMEZONE).time()
        day = datetime.datetime.now(tz=TIMEZONE).weekday()

        if day >= 5:
            print(f"{tod_in_ca}: Skipping — weekend: {day}")
        elif tod_in_ca < MORNING:
            print(f"{tod_in_ca}: Skipping — before morning: {tod_in_ca}")
        elif self.last_sent.date() == datetime.datetime.today().date():
            print(
                f"{tod_in_ca}: Skipping — already sent today: {self.last_sent.date()}"
            )
        else:
            self.send_message()
            print(f"{tod_in_ca}: SENT MESSAGE FOR {datetime.datetime.today().date()}")
            with connect_db() as db:
                db(
                    "UPDATE status SET last_sent=(%s)",
                    [datetime.datetime.today().timestamp()],
                )

if __name__ == '__main__':
    print('in here')
    run = Main()
    run.send_message()
