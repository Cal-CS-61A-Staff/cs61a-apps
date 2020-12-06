from random import choice
from string import ascii_lowercase

from flask import Flask, abort, redirect, request

from common.db import connect_db
from common.oauth_client import create_oauth_client, is_staff
from common.rpc.paste import paste_text
from common.rpc.secrets import validates_master_secret
from common.url_for import url_for

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


create_oauth_client(app, "61a-paste")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS pastes (
    name varchar(128),
    data LONGBLOB,
    private boolean
);"""
    )


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    return f"""
    <h1>61A Paste</h1>
    Paste text here: 
    <br/><p>
    <form action="{url_for("submit")}" method="POST">
    <textarea name="data" rows="30" cols="50" name="comment" ></textarea>
    </p>
    <input type="submit"></input>
    </form>
    """


@app.route("/save", methods=["POST"])
def submit():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    data = request.form["data"]
    return redirect(url_for("load_formatted", name=paste_worker(data)))


@app.route("/<string:name>")
def load_formatted(name):
    out = load(name)
    if isinstance(out, str):
        return "<code>" + load(name) + "</code>"
    else:
        return out


@app.route("/<string:name>/raw")
def load_raw(name):
    return load(name)


def load(name, skip_auth=False):
    with connect_db() as db:
        data = db(
            "SELECT data FROM pastes WHERE name=%s AND private=FALSE",
            [name],
        ).fetchone()
        if data:
            return data[0]
    if not skip_auth and not is_staff("cs61a"):
        return redirect(url_for("login"))
    with connect_db() as db:
        data = db(
            "SELECT data FROM pastes WHERE name=%s",
            [name],
        ).fetchone()
        if data:
            return data[0]
        else:
            abort(404)


@paste_text.bind(app)
@validates_master_secret
def paste_text(app, is_staging, data: str, name: str = None, is_private: bool = False):
    return paste_worker(data, name, is_private)


def paste_worker(data: str, name: str = None, is_private: bool = False):
    if name is None:
        name = "".join(choice(ascii_lowercase) for _ in range(12))
    with connect_db() as db:
        db("DELETE FROM pastes WHERE name=%s", [name])
        db(
            "INSERT INTO pastes (name, data, private) VALUES (%s, %s, %s)",
            [name, data, is_private],
        )
    return name


def get_paste(app, is_staging, name: str):
    return load(name, skip_auth=True)


if __name__ == "__main__":
    app.run(debug=True)
