import sys, hashlib

from flask import Flask, abort, request, redirect
from typing import List, Tuple

from common.oauth_client import create_oauth_client, is_staff
from common.jobs import job
from common.db import connect_db
from common.url_for import url_for
from common.html import html, make_row

from auth import authenticate, update_storage
from datetime import datetime

app = Flask(__name__)
create_oauth_client(app, "grade-display-exports", return_response=update_storage)

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS gscope (
    name varchar(128),
    gs_code varchar(128)
)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS adjustments (
    hashed text,
    url text,
    sheet text
)"""
    )


@app.route("/")
def index():
    auth_result = authenticate(app)
    if auth_result == "Authorized!":
        auth_result = html(auth_result)
    return auth_result


@app.route("/config")
def config():
    auth_result = authenticate(app)
    if not (isinstance(auth_result, str) and auth_result == "Authorized!"):
        return auth_result

    with connect_db() as db:
        gscope: List[Tuple[str, str]] = db(
            "SELECT name, gs_code FROM gscope",
            [],
        ).fetchall()
        adjustments: List[Tuple[str, str, str]] = db(
            "SELECT hashed, url, sheet FROM adjustments",
            [],
        ).fetchall()

    return html(
        """
    <h1>Grade Display Config</h1>
    <p>
        Add a Gradescope assignment:
        """
        + make_row(
            """<input name="name" placeholder="Shortname (no spaces!)" />
            <input name="gs_code" placeholder="Gradescope code" />
        """,
            url_for("create_assign"),
            "Submit",
        )
        + """
    </p>
    <p>
        Add an adjustments sheet:
        """
        + make_row(
            """<input name="url" placeholder="Full URL" />
            <input name="sheet" placeholder="Sheet Name" />
        """,
            url_for("add_adjustments"),
            "Submit",
        )
        + """
    </p>
    """
        + "".join(
            "<p>" + make_row(f"{name} ({gs_code})", url_for("delete_assign", name=name))
            for name, gs_code in gscope
        )
        + "".join(
            "<p>"
            + make_row(
                f"Adjustments: {url} ({sheet})",
                url_for("delete_adjustments", hashed=hashed),
            )
            for hashed, url, sheet in adjustments
        )
    )


@app.route("/create_assign", methods=["POST"])
def create_assign():
    if not is_staff("cs61a"):
        return redirect(url_for("config"))

    name = request.form["name"]
    gs_code = request.form["gs_code"]
    with connect_db() as db:
        existing = db("SELECT * FROM gscope WHERE name=%s", [name]).fetchall()
        if existing:
            abort(409)
        db(
            "INSERT INTO gscope (name, gs_code) VALUES (%s, %s)",
            [name, gs_code],
        )
    return redirect(url_for("config"))


@app.route("/add_adjustments", methods=["POST"])
def add_adjustments():
    if not is_staff("cs61a"):
        return redirect(url_for("config"))

    url = request.form["url"]
    sheet = request.form["sheet"]
    hashed = hashlib.sha512(url.encode("utf-8") + sheet.encode("utf-8")).hexdigest()
    with connect_db() as db:
        db(
            "INSERT INTO adjustments (hashed, url, sheet) VALUES (%s, %s, %s)",
            [hashed, url, sheet],
        )
    return redirect(url_for("config"))


@app.route("/delete_assign/<name>", methods=["POST"])
def delete_assign(name):
    if not is_staff("cs61a"):
        return redirect(url_for("config"))
    with connect_db() as db:
        db("DELETE FROM gscope WHERE name=%s", [name])
    return redirect(url_for("config"))


@app.route("/delete_adjustments/<hashed>", methods=["POST"])
def delete_adjustments(hashed):
    if not is_staff("cs61a"):
        return redirect(url_for("config"))
    with connect_db() as db:
        db("DELETE FROM adjustments WHERE hashed=%s", [hashed])
    return redirect(url_for("config"))


@job(app, "update_grades")
@app.route("/update_grades")
def run():
    from update_job import update  # fresh import to ensure up-to-date data from db

    start = datetime.now()
    print(f"Grade update triggered at {str(start)}.", file=sys.stderr)
    update()
    end = datetime.now()
    print(f"Grade update completed at {str(end)}.", file=sys.stderr)
    return f"Done. Took {str((end - start).total_seconds())} seconds."


if __name__ == "__main__":
    app.run(debug=True)
