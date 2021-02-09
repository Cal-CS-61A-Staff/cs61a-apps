from random import choice
from typing import List

from flask import Flask, redirect, request

from common.db import connect_db
from common.html import html, make_row
from common.oauth_client import create_oauth_client, is_staff, login
from common.rpc.auth import read_spreadsheet
from common.rpc.hinting import Messages, get_hints, get_wwpd_hints
from common.rpc.utils import cached
from common.url_for import url_for

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS sources (
    assignment varchar(512),
    url varchar(512),
    sheet varchar(512)
)"""
    )

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-hinting")


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()

    with connect_db() as db:
        sources = db(
            "SELECT assignment, url, sheet FROM sources",
        ).fetchall()

    insert_fields = f"""
        <input placeholder="Assignment" name="assignment"></input>
        <input placeholder="Spreadsheet URL" name="url"></input>
        <input placeholder="Sheet Name" name="sheet"></input>
        """

    sources = "<br/>".join(
        make_row(
            f'{assignment}: <a href="{url}">{url}</a> {sheet}'
            f'<input name="assignment" type="hidden" value="{assignment}"></input>'
            f'<input name="sheet" type="hidden" value="{sheet}"></input>',
            url_for("remove_source"),
        )
        for assignment, url, sheet in sources
    )

    return html(
        f"""
    <h3>Sources</h3>
    {sources}
    <h3>Add Sources</h3>
    {make_row(insert_fields, url_for("add_source"), "Add")}
    """
    )


@app.route("/add_source", methods=["POST"])
def add_source():
    if not is_staff("cs61a"):
        return login()

    assignment = request.form["assignment"]
    url = request.form["url"]
    sheet = request.form["sheet"]

    with connect_db() as db:
        db(
            "DELETE FROM sources WHERE assignment=%s",
            [assignment],
        )
        db(
            "INSERT INTO sources VALUES (%s, %s, %s)",
            [assignment, url, sheet],
        )

    return redirect(url_for("index"))


@app.route("/remove_source", methods=["POST"])
def remove_source():
    if not is_staff("cs61a"):
        return login()

    assignment = request.form["assignment"]

    with connect_db() as db:
        db(
            "DELETE FROM sources WHERE assignment=%s",
            [assignment],
        )

    return redirect(url_for("index"))


def get_hint_source(assignment: str):
    return (
        "https://docs.google.com/spreadsheets/d/1jjX1Zpak-pHKu-MuHKXd7y2ynWiTNkPfcStBDgX66l8/edit#gid=0",
        "Sheet1",
    )


@cached()
def load_hint_source(*, assignment: str):
    source = get_hint_source(assignment)
    if source is None:
        return []
    url, sheet_name = source
    return read_spreadsheet(url=url, sheet_name=sheet_name)


def hint_lookup(
    assignment: str, target_question: str, target_prompt: str, student_response: str
):
    return [
        (hint, prompt)
        for question, prompt, suite, case, needle, hint, followup in load_hint_source(
            assignment=assignment
        )
        if question in target_question
        and prompt in target_prompt
        and suite in student_response
        and case in student_response
        and needle in student_response
    ]


@get_wwpd_hints.bind(app)
def get_wwpd_hints(*, unlock_id: str, selected_options: List[str]):
    assignment, question, prompt = unlock_id.split("\n")
    return dict(
        hints=[
            hint
            for hint, followup in hint_lookup(
                assignment, question, prompt, "\n".join(selected_options)
            )
        ]
    )


@get_hints.bind(app)
def get_hints(*, assignment: str, test: str, messages: Messages, user: str):
    for question, results in messages.get("grading", {}).items():
        if question == messages["hinting"]["question"]["name"]:
            failed_outputs = results.get("failed_outputs", [])
            break
    else:
        failed_outputs = []

    PS1 = ">>> "
    PS2 = "... "
    prompt = []
    rest = []
    for line in "\n".join(failed_outputs).split("\n"):
        if line.startswith(PS1):
            prompt = [line[len(PS1) :]]
            rest = []
        elif line.startswith(PS2):
            prompt.append(line[len(PS2) :])
        else:
            rest.append(line)

    hints = hint_lookup(assignment, test, "\n".join(prompt), "\n".join(rest))

    if hints:
        message, post_prompt = choice(hints)
        return dict(message=message, post_prompt=post_prompt)
    else:
        return {}


if __name__ == "__main__":
    app.run(debug=True)
