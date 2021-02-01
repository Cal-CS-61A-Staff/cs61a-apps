from datetime import timedelta
from json import dumps, loads
from random import shuffle
from time import time

from flask import Flask, Response, abort, render_template, request

from common.course_config import get_endpoint
from common.db import connect_db
from common.secrets import new_secret
from contest_utils.oauth import get_group
from contest_utils.rate_limiting import ratelimited

NUM_DICE = 6
MAX_CAPTION_LEN = 100
ASSIGNMENT = "proj01showcase"

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


with connect_db() as db:
    db("CREATE TABLE IF NOT EXISTS accesses (email VARCHAR(128), last_access INTEGER)")
    db(
        """CREATE TABLE IF NOT EXISTS designs (
    id varchar(128),
    created_time integer,
    email varchar(128),
    caption varchar(512),
    dice LONGBLOB,
    endpoint varchar(512)
);"""
    )


@app.route("/")
def index():
    with connect_db() as db:
        artworks = db(
            "SELECT id, caption FROM designs WHERE endpoint=(%s)",
            [get_endpoint("cs61a")],
        ).fetchall()
    shuffle(artworks)
    resp = Response(render_template("index.html", artworks=artworks))
    resp.cache_control.max_age = 0
    return resp


@app.route("/img")
def img():
    id = request.args["id"]
    index = int(request.args["index"])
    with connect_db() as db:
        caption, dice = db(
            "SELECT caption, dice FROM designs WHERE id=(%s)", [id]
        ).fetchone()
    dice = loads(dice)
    resp = Response(dice[index], mimetype="image/svg+xml")
    resp.headers["Content-Security-Policy"] = "default-src 'none'"
    if "script" in dice[index]:
        resp.headers["Content-Security-Policy-Observation"] = "Nice try"
    resp.cache_control.max_age = 3600
    return resp


@app.route("/api/submit_designs", methods=["POST"])
@ratelimited(timedelta(minutes=1))
def submit():
    caption = str(request.form["caption"])
    if len(caption) > MAX_CAPTION_LEN:
        abort(
            413,
            f"Your caption is too long - it should be at most {MAX_CAPTION_LEN} characters.",
        )
    dice = loads(request.form["dice"])
    dice_list = []
    for svg in dice:
        if not isinstance(svg, str):
            abort(401)
        dice_list.append(svg)
    del dice
    if len(dice_list) != NUM_DICE:
        abort(401)
    group = get_group(get_endpoint("cs61a") + "/" + ASSIGNMENT)
    with connect_db() as db:
        for member in group:
            db("DELETE FROM designs WHERE email=(%s)", [member])
        email = group[0]
        db(
            "INSERT INTO designs (id, created_time, email, caption, dice, endpoint) VALUES (%s, %s, %s, %s, %s, %s)",
            [
                new_secret(),
                int(time()),
                email,
                caption,
                dumps(dice_list),
                get_endpoint("cs61a"),
            ],
        )

    return dict(success=True, group=group)


if __name__ == "__main__":
    app.run(debug=True)
