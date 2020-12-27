from flask import jsonify, redirect, render_template, send_from_directory
from werkzeug.exceptions import NotFound

from common.url_for import url_for
from constants import (
    COOKIE_SHORTLINK_REDIRECT,
    NOT_AUTHORIZED,
    NOT_FOUND,
    NOT_LOGGED_IN,
    STATIC_FOLDER,
)
from named_shortlinks import attempt_named_shortlinks
from shortlink_generator import attempt_generated_shortlink
from shortlink_paths import attempt_shortlink_paths


def create_shortlink_handler(app):
    def load_shortlink_file(path):
        return (
            attempt_named_shortlinks(path)
            or attempt_shortlink_paths(path)
            or attempt_generated_shortlink(path, app)
        )

    @app.route("/<path:path>")
    def load_file(path):
        try:
            out = send_from_directory(STATIC_FOLDER, path.replace("//", "/"))
        except NotFound:
            pass
        else:
            return out

        raw = load_shortlink_file(path)

        if raw is NOT_LOGGED_IN:
            response = redirect(url_for("login"))
            response.set_cookie(COOKIE_SHORTLINK_REDIRECT, value=path)
            return response
        elif raw is NOT_AUTHORIZED:
            return "This file is only visible to staff."

        if raw is NOT_FOUND:
            return "File not found", 404

        data = {
            "fileName": raw["full_name"],
            "data": raw["data"],
            "shareRef": raw["share_ref"],
        }

        return render_template("index.html", initData={"loadFile": data})

    @app.route("/<path>/raw")
    def get_raw(path):
        return jsonify(load_shortlink_file(path))

    app.load_file = load_file
