from datetime import timedelta
from json import loads

from flask import Flask, abort, request

from common.db import connect_db
from common.oauth_client import create_oauth_client
from common.rpc.auth import get_endpoint
from contest_utils.oauth import get_group
from contest_utils.rate_limiting import ratelimited

NUM_DICE = 6
MAX_CAPTION_LEN = 100
ASSIGNMENT = "proj01gallery"

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


create_oauth_client(app, "61a-dice-gallery")

with connect_db() as db:
    db("CREATE TABLE IF NOT EXISTS accesses (email VARCHAR(128), last_access INTEGER)")
    db(
        """CREATE TABLE IF NOT EXISTS designs (
    email varchar(128),
    caption varchar(512),
    dice LONGBLOB,
    src LONGBLOB
);"""
    )


@app.after_request
def add_security_headers(resp):
    resp.headers["Content-Security-Policy"] = "default-src 'self'"
    return resp


@app.route("/api/submit_designs", methods=["POST"])
@ratelimited(timedelta(minutes=1))
def index():
    caption = str(request.form["caption"])
    if len(caption) > MAX_CAPTION_LEN:
        abort(
            413,
            f"Your caption is too long - it should be at most {MAX_CAPTION_LEN} characters.",
        )
    dice = loads(request.form["dice"])
    src = str(request.form["src"])
    dice_list = []
    for svg in dice:
        if not isinstance(svg, str):
            abort(401)
        dice_list.append(svg)
    del dice
    if len(dice_list) != NUM_DICE:
        abort(401)
    group = get_group(get_endpoint(course="cs61a") + "/" + ASSIGNMENT)
    with connect_db() as db:
        for member in group:
            db("DELETE FROM designs WHERE email=(%s)", [member])
        email = group[0]
        db(
            "INSERT INTO designs (email, caption, dice, src) VALUES (%s, %s, %s, %s)",
            [email, caption, dice_list, src],
        )

    return dict(success=True)


if __name__ == "__main__":
    app.run(debug=True)
