from random import choice
from typing import List

from flask import Flask, redirect, request
from werkzeug.utils import escape

from common.db import connect_db
from common.html import html, make_row
from common.oauth_client import create_oauth_client, is_staff, login
from common.rpc.auth import read_spreadsheet
from common.rpc.hinting import (
    Messages,
    check_hints_available,
    get_hints,
    get_wwpd_hints,
)
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

    data = {}
    for key in ["assignment", "question", "suite", "case", "prompt", "output"]:
        if key in request.args:
            data[key] = request.args[key]
        else:
            data = {}
            break

    if data:
        question = "Question " + data["question"]
        output = data["output"] + f"\n Suite {data['suite']} Case {data['case']}"
        hints = hint_lookup(data["assignment"], question, data["prompt"], output)
        hint_rows = [
            f"<p>Hint: {escape(hint)}"
            + (f" (Prompt: {escape(prompt)})" if prompt else "")
            for hint, prompt in hints
        ]
        hint_html = f"""
        <h3>Hint Output</h3>
        {"".join(hint_rows) if hints else "None"}
        """
    else:
        hint_html = ""

    def g(key):
        return escape(data.get(key, ""))

    with connect_db() as db:
        assignments = db("SELECT assignment FROM sources").fetchall()

    return html(
        f"""
    <h3>Sources</h3>
    {sources}
    <h3>Add Sources</h3>
    {make_row(insert_fields, url_for("add_source"), "Add")}
    <h3>Test Hints</h3>
    <form action="/" method="GET">
        <p>
        Assignment:
        <select name="assignment">
        {''.join(f'<option>{assignment[0]}</option>' for assignment in assignments)}
        </select>
        <p>
        Question: <input name="question" value="{g('question')}"> </input>
        <p>
        Suite: <input name="suite" value="{g('suite')}"></input>
        <p>
        Case: <input name="case" value="{g('case')}"></input>
        <p>
        Prompt: <br />
        <textarea name="prompt">{g('prompt')}</textarea>
        <p>
        Student Output: <br />
        <textarea name="output">{g('output')}</textarea>
        <p>
        <button type="submit">Get Hints!</button>
    </form>
    {hint_html}
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
    with connect_db() as db:
        source = db(
            "SELECT url, sheet FROM sources WHERE assignment=(%s)", [assignment]
        ).fetchone()

    if source:
        return source
    return None


def load_hint_source(assignment: str, *, _cache={}, skip_cache=False):
    if assignment in _cache and not skip_cache:
        return _cache[assignment]
    source = get_hint_source(assignment)
    if source is None:
        return []
    url, sheet_name = source
    _cache[assignment] = read_spreadsheet(url=url, sheet_name=sheet_name)
    return _cache[assignment]


def hint_lookup(
    assignment: str, target_question: str, target_prompt: str, student_response: str
):
    return [
        (hint, prompt)
        for question, prompt, suite, case, needle, hint, followup in load_hint_source(
            assignment, skip_cache=True
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


@check_hints_available.bind(app)
def check_hints_available(*, assignment: str):
    with connect_db() as db:
        exists = db(
            "SELECT COUNT(*) FROM sources WHERE assignment=(%s)", [assignment]
        ).fetchone()
    return bool(exists)


if __name__ == "__main__":
    app.run(debug=True)
