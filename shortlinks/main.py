from enum import Enum

from flask import Flask, redirect, request

import urllib.parse as urlparse

from common.course_config import get_course
from common.db import connect_db
from common.html import error, html, make_row
from common.oauth_client import create_oauth_client, is_enrolled, is_staff, login
from common.rpc.auth import read_spreadsheet
from common.url_for import url_for


class AccessRestriction(Enum):
    ALL = 0
    STAFF = 1
    STUDENT = 2


print("Added this line for investigation.")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS shortlinks (
    shortlink varchar(512),
    url varchar(512),
    creator varchar(512),
    secure int,
    course varchar(128)
)"""
    )

    db(
        """CREATE TABLE IF NOT EXISTS sources (
    url varchar(512),
    sheet varchar(256),
    secure int,
    course varchar(128)
)"""
    )


def add_url_params(url, params_string):
    parse_result = list(urlparse.urlsplit(url))
    parse_result[3] = "&".join(filter(lambda s: s, [parse_result[3], params_string]))
    return urlparse.urlunsplit(tuple(parse_result))


app = Flask(__name__)
app.url_map.strict_slashes = False

if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-shortlinks")


def lookup(path):
    with connect_db() as db:
        target = db(
            "SELECT url, creator, secure FROM shortlinks WHERE shortlink=%s AND course=%s",
            [path, get_course()],
        ).fetchone()
        if target:
            target = list(target)
            target[2] = AccessRestriction(target[2])
    return target or (None, None, None)


def is_authorized(secure: AccessRestriction):
    if secure == AccessRestriction.ALL:
        return True
    elif secure == AccessRestriction.STAFF:
        return is_staff(get_course())
    elif secure == AccessRestriction.STUDENT:
        return is_enrolled(get_course())
    else:
        raise Exception(f"{secure} is not a valid AccessRestriction")


@app.route("/<path>/")
def handler(path):
    url, creator, secure = lookup(path)
    if not url:
        return error("Target not found!")
    if not is_authorized(secure):
        return login()
    return redirect(add_url_params(url, request.query_string.decode("utf-8")))


@app.route("/preview/<path>/")
def preview(path):
    url, creator, secure = lookup(path)
    if url is None:
        return html("No such link exists.")
    if not is_authorized(secure):
        return login()
    return html(
        'Points to <a href="{0}">{0}</a> by {1}'.format(
            add_url_params(url, request.query_string.decode("utf-8")), creator
        )
    )


@app.route("/")
def index():
    if not is_staff(get_course()):
        return login()
    with connect_db() as db:
        sources = db(
            "SELECT url, sheet, secure FROM sources WHERE course=%s", [get_course()]
        ).fetchall()

    insert_fields = f"""<input placeholder="Spreadsheet URL" name="url"></input>
        <input placeholder="Sheet Name" name="sheet"></input>
        <select name="secure">
            <option value="{AccessRestriction.ALL.value}">Public</option>
            <option value="{AccessRestriction.STAFF.value}">Staff Only</option>
            <option value="{AccessRestriction.STUDENT.value}">Students and Staff</option>
        </select>"""

    sources = "<br/>".join(
        make_row(
            f'<a href="{url}">{url}</a> {sheet} (Secure: {AccessRestriction(secure).name})'
            f'<input name="url" type="hidden" value="{url}"></input>'
            f'<input name="sheet" type="hidden" value="{sheet}"></input>',
            url_for("remove_source"),
        )
        for url, sheet, secure in sources
    )

    return html(
        f"""
    <h2>Course: <code>{get_course()}</code></h2>
    Each spreadsheet should be shared with the 61A service account
    <a href="mailto:secure-links@ok-server.iam.gserviceaccount.com">
        secure-links@ok-server.iam.gserviceaccount.com</a>.
    They should have three columns with the headers: "URL", "Shortlink", and "Creator".
    <p>
    Visit <a href="{url_for("refresh")}">{url_for("refresh")}</a> (no auth required) 
    after adding a link to synchronize with the spreadsheets.

    <h3>Sources</h3>
    {sources}
    <h3>Add Sources</h3>
    {make_row(insert_fields, url_for("add_source"), "Add")}
    """
    )


@app.route("/add_source", methods=["POST"])
def add_source():
    if not is_staff(get_course()):
        return login()

    url = request.form["url"]
    sheet = request.form["sheet"]
    secure = int(request.form.get("secure"))

    with connect_db() as db:
        db(
            "INSERT INTO sources VALUES (%s, %s, %s, %s)",
            [url, sheet, secure, get_course()],
        )

    return redirect(url_for("index"))


@app.route("/remove_source", methods=["POST"])
def remove_source():
    if not is_staff(get_course()):
        return login()

    url = request.form["url"]
    sheet = request.form["sheet"]

    with connect_db() as db:
        db(
            "DELETE FROM sources WHERE url=%s AND sheet=%s AND course=%s",
            [url, sheet, get_course()],
        )

    return redirect(url_for("index"))


@app.route("/_refresh/")
def refresh():
    data = []
    links = set()
    with connect_db() as db:
        sheets = db(
            "SELECT url, sheet, secure FROM sources WHERE course=(%s)", [get_course()]
        ).fetchall()
    for url, sheet, secure in sheets:
        try:
            csvr = read_spreadsheet(url=url, sheet_name=sheet)
        except:
            return error(f"Failed to read spreadsheet {url} (Sheet: {sheet})")
        headers = [x.lower() for x in csvr[0]]
        for row in csvr[1:]:
            row = row + [""] * 5
            shortlink = row[headers.index("shortlink")]
            if shortlink in links:
                return error(f"Duplicate shortlink `{shortlink}` found, aborting.")
            links.add(shortlink)
            url = row[headers.index("url")]
            creator = row[headers.index("creator")]
            data.append([shortlink, url, creator, secure, get_course()])
    with connect_db() as db:
        db("DELETE FROM shortlinks WHERE course=%s", [get_course()])
        db(
            "INSERT INTO shortlinks (shortlink, url, creator, secure, course) VALUES (%s, %s, %s, %s, %s)",
            data,
        )
    return html("Links updated")


if __name__ == "__main__":
    app.run(debug=True)
