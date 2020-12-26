import random

from flask import request, abort

from english_words import english_words_set as words  # list of words to generate links

from common.db import connect_db
from constants import NOT_LOGGED_IN, NOT_AUTHORIZED, NOT_FOUND, ServerFile
from oauth_utils import check_auth


def attempt_generated_shortlink(path, app):
    with connect_db() as db:
        try:
            ret = db("SELECT * FROM staffLinks WHERE link=%s;", [path]).fetchone()
            if ret is not None:
                return ServerFile(
                    ret["link"],
                    ret["fileName"],
                    "",
                    ret["fileContent"].decode(),
                    ret["shareRef"],
                    False,
                )._asdict()

            ret = db("SELECT * FROM studentLinks WHERE link=%s;", [path]).fetchone()

            if ret is None:
                return NOT_FOUND

            if check_auth(app):
                return ServerFile(
                    ret["link"],
                    ret["fileName"],
                    "",
                    ret["fileContent"].decode(),
                    ret["shareRef"],
                    False,
                )._asdict()
            else:
                return NOT_AUTHORIZED
        except Exception:
            return NOT_LOGGED_IN


def create_shortlink_generator(app):
    def save_file(db_name):
        file_name, file_content, share_ref = (
            request.form["fileName"],
            request.form["fileContent"],
            request.form["shareRef"],
        )
        with connect_db() as db:
            link = "".join(random.sample(words, 1)[0].title() for _ in range(3))
            db(
                f"INSERT INTO {db_name} VALUES (%s, %s, %s, %s)",
                [link, file_name, file_content, share_ref],
            )
        return "code.cs61a.org/" + link

    @app.route("/api/share", methods=["POST"])
    def share():
        return save_file("studentLinks")

    @app.route("/api/staff_share", methods=["POST"])
    def staff_share():
        if not check_auth(app):
            abort(403)

        return save_file("staffLinks")


def setup_shortlink_generator():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS studentLinks (
           link varchar(128),
           fileName varchar(128),
           fileContent BLOB,
           shareRef varchar(128))"""
        )
        db(
            """CREATE TABLE IF NOT EXISTS staffLinks (
           link varchar(128),
           fileName varchar(128),
           fileContent BLOB,
           shareRef varchar(128))"""
        )


#  ALTER TABLE staffLinks ADD shareRef varchar(128);
