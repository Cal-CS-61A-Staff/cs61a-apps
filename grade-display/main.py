import sys

from flask import Flask, abort, request, redirect
from typing import List, Tuple

from common.oauth_client import create_oauth_client, is_staff
from common.jobs import job
from common.db import connect_db
from common.url_for import url_for
from common.rpc.howamidoing import download_grades

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
        """CREATE TABLE IF NOT EXISTS acadh (
    url text,
    sheet text
)"""
    )


@app.route("/")
def index():
    return authenticate(app)


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
        acadh: List[Tuple[str, str]] = db(
            "SELECT url, sheet FROM acadh",
            [],
        ).fetchall()

    return (
        """
    <h1>Grade Display Config</h1>
    <p>
        Add a Gradescope assignment: 
        <form action="/create_assign" method="POST">
            <input name="name" placeholder="Shortname (no spaces!)" /> 
            <input name="gs_code" placeholder="Gradescope code" /> 
            <button type="submit">Submit</button>
        </form>
    </p>
    <p>
        Set the Academic Dishonesty Spreadsheet URL: 
        <form action="/set_acadh" method="POST">
            <input name="url" placeholder="Full URL" />
            <input name="sheet" placeholder="Sheet Name" />
            <button type="submit">Submit</button>
        </form>
    </p>
    """
        + "".join(
            f"""<p>
            <form 
                style="display: inline" 
                action="{url_for("delete_assign", name=name)}" 
                method="post"
            >
                {name} ({gs_code})
                <input type="submit" value="Remove">
        </form>"""
            for name, gs_code in gscope
        )
        + "".join(
            f"""<p>
            <form
                style="display: inline"
                action="{url_for("delete_acadh")}"
                method="post"
            >
                Academic Dishonesty Penalties: {url} ({sheet})
                <input type="submit" value="Remove">
        </form>"""
            for url, sheet in acadh
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


@app.route("/set_acadh", methods=["POST"])
def set_acadh():
    if not is_staff("cs61a"):
        return redirect(url_for("config"))

    url = request.form["url"]
    sheet = request.form["sheet"]
    with connect_db() as db:
        db("TRUNCATE TABLE acadh")
        db(
            "INSERT INTO acadh (url, sheet) VALUES (%s, %s)",
            [url, sheet],
        )
    return redirect(url_for("config"))


@app.route("/delete_assign/<name>", methods=["POST"])
def delete_assign(name):
    if not is_staff("cs61a"):
        return redirect(url_for("config"))
    with connect_db() as db:
        db("DELETE FROM gscope WHERE name=%s", [name])
    return redirect(url_for("config"))


@app.route("/delete_acadh", methods=["POST"])
def delete_acadh():
    if not is_staff("cs61a"):
        return redirect(url_for("config"))
    with connect_db() as db:
        db("TRUNCATE TABLE acadh")
    return redirect(url_for("config"))


@app.route("/export")
def export_grades():
    if not is_staff("cs61a"):
        return redirect(url_for("config"))
    return download_grades()


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
