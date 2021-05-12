import random

from common.rpc.secrets import only
from flask import request, abort


from common.db import connect_db
from common.rpc.code import create_code_shortlink
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
    try:
        with open("sanitized_words.txt") as f:
            words = f.read().split("\n")
    except FileNotFoundError:
        words = [f"word{i}" for i in range(1000)]

    def save_file_web(staff_only):
        file_name, file_content, share_ref = (
            request.form["fileName"],
            request.form["fileContent"],
            request.form["shareRef"],
        )
        return save_file(file_name, file_content, share_ref, staff_only)

    def save_file(file_name, file_content, share_ref, staff_only, link=None):
        db_name = "studentLinks" if staff_only else "staffLinks"
        with connect_db() as db:
            if not link:
                link = "".join(
                    random.sample(words, 1)[0].strip().title() for _ in range(3)
                )
            db(
                f"INSERT INTO {db_name} VALUES (%s, %s, %s, %s)",
                [link, file_name, file_content.encode("utf-8"), share_ref],
            )
        return "code.cs61a.org/" + link

    @app.route("/api/share", methods=["POST"])
    def share():
        return save_file_web(True)

    @app.route("/api/staff_share", methods=["POST"])
    def staff_share():
        if not check_auth(app):
            abort(403)

        return save_file_web(False)

    @create_code_shortlink.bind(app)
    @only("examtool")
    def create_code_shortlink_impl(
        name: str, contents: str, staff_only: bool = True, link: str = None
    ):
        return save_file(name, contents, None, staff_only, link)


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
