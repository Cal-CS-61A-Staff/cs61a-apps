from random import choice
from string import ascii_lowercase

from flask import Flask, Response, abort, redirect, request, escape

from common.db import connect_db
from common.html import html
from common.oauth_client import create_oauth_client, is_staff, login
from common.rpc.paste import get_paste, paste_text
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
        return login()
    return html(
        f"""
    Paste text here: 
    <br/><p>
    <form action="{url_for("submit")}" method="POST">
    <textarea name="data" rows="30" cols="50" name="comment" ></textarea>
    </p>
    <input type="submit"></input>
    </form>
    """
    )


@app.route("/save", methods=["POST"])
def submit():
    if not is_staff("cs61a"):
        return login()
    data = request.form["data"]
    return redirect(url_for("load_formatted", name=paste_worker(data)))


@app.route("/<string:name>")
def load_formatted(name):
    out = load(name)
    if isinstance(out, str):
        return html(
            f"""<body style="max-width: calc(100% - 10em)">
                <h1>61A Paste</h1>
                <pre>{escape(out)}</pre>
                <a href=\"{url_for('load_raw', name=name)}\">(raw)</a>
            </body>"""
        )
    else:
        return out


@app.route("/<string:name>/raw")
def load_raw(name):
    return Response(load(name), mimetype="text")


def load(name, skip_auth=False):
    """Loads the paste text for given name

    :param name: name associated with the paste text
    :type name: str
    :param skip_auth: a flag to skip the authentication for the user;
        ``False`` by default
    :type skip_auth: bool

    :return: a string representing the paste text for this user
    """
    out = None
    with connect_db() as db:
        data = db(
            "SELECT data FROM pastes WHERE name=%s AND private=FALSE",
            [name],
        ).fetchone()
        if data:
            out = data[0]
    if out is None:
        if not skip_auth and not is_staff("cs61a"):
            return login()
        with connect_db() as db:
            data = db(
                "SELECT data FROM pastes WHERE name=%s",
                [name],
            ).fetchone()
            if data:
                out = data[0]
    if out is None:
        abort(404)
    elif isinstance(out, bytes):
        return out.decode("utf-8")
    else:
        return out


@paste_text.bind(app)
@validates_master_secret
def paste_text(app, is_staging, data: str, name: str = None, is_private: bool = False):
    return paste_worker(data, name, is_private)


def paste_worker(data: str, name: str = None, is_private: bool = False):
    """Creates and saves a new entry in the pastes table representing the given
    paste data. If name is not provided, generates a random string as name.

    :param data: the paste text
    :type data: str
    :param name: name of the given user; ``None`` by default
    :type name: str
    :param is_private: a flag determining whether or not this data is private;
        ``False`` by default
    :type is_private: bool

    :return: string representing the name
    """
    if name is None:
        name = "".join(choice(ascii_lowercase) for _ in range(24))
    with connect_db() as db:
        db("DELETE FROM pastes WHERE name=%s", [name])
        db(
            "INSERT INTO pastes (name, data, private) VALUES (%s, %s, %s)",
            [name, data, is_private],
        )
    return name


@get_paste.bind(app)
@validates_master_secret
def get_paste(app, is_staging, name: str):
    return load(name, skip_auth=True)


if __name__ == "__main__":
    app.run(debug=True)
