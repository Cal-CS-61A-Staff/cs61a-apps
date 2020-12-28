import csv
import datetime
import json
import os
import re

import braceexpand
import requests
from flask import request, jsonify

from common.db import connect_db
from common.rpc.auth import read_spreadsheet
from constants import CSV_ROOT
from oauth_utils import get_user_data


CACHE = {}


def setup_ok_server_interface():
    CACHE.clear()
    parsed = iter(read_spreadsheet(url=CSV_ROOT, sheet_name="OK Config Paths"))
    _, _, _, _, semester = next(parsed)
    lookups = []
    for line in parsed:
        pattern, template, *_ = line
        lookups.append([pattern, template])
    with connect_db() as db:
        db("DROP TABLE IF EXISTS ok_lookups")
        db("CREATE TABLE ok_lookups (email varchar(128), template varchar(128))")
        db("INSERT INTO ok_lookups VALUES (%s, %s)", lookups)

        db("DROP TABLE IF EXISTS ok_data")
        db("CREATE TABLE ok_data (name varchar(128), value varchar(128))")
        db("INSERT INTO ok_data VALUES (%s, %s)", ["semester", semester])


def create_ok_server_interface(app):
    def get_target_urls(assignment):
        with connect_db() as db:
            lookups = db("SELECT * FROM ok_lookups").fetchall()
        for pattern, template in lookups:
            if pattern in assignment:
                url = template.format(assignment=assignment)
                raw = retrieve(url)
                if not raw.ok:
                    continue
                data = json.loads(raw.text)
                files = set()
                files.update(data["src"])
                for filename in data["tests"]:
                    filename = filename.split(":")[0]
                    filename = re.sub(r"\[([0-9])-([0-9])\]", r"{\1..\2}", filename)
                    files.update(braceexpand.braceexpand(filename))
                return os.path.dirname(url), files

    def retrieve(url):
        if url not in CACHE:
            CACHE[url] = requests.get(url)
        return CACHE[url]

    def get_semester():
        with connect_db() as db:
            return db(
                "SELECT value FROM ok_data WHERE name=%s", ["semester"]
            ).fetchone()[0]

    @app.route("/api/get_backups", methods=["POST"])
    def get_backups():
        assignment = request.form["assignment"]
        email = get_user_data(app)["email"]
        resp = app.remote.get(
            "assignment/cal/cs61a/{}/{}/export/{}?limit=1".format(
                get_semester(), assignment, email
            )
        ).data
        if not resp["data"]["backups"]:
            resp["data"]["backups"].append(
                {
                    "messages": [
                        {
                            "created": datetime.datetime.now().isoformat(),
                            "kind": "file_contents",
                            "contents": {},
                        }
                    ]
                }
            )
        contents = next(
            message
            for message in resp["data"]["backups"][0]["messages"]
            if message["kind"] == "file_contents"
        )["contents"]

        dirname, files = get_target_urls(assignment)
        for file in files:
            if file not in contents:
                contents[file] = retrieve(os.path.join(dirname, file)).text

        return jsonify(resp)

    @app.route("/api/list_assignments", methods=["POST"])
    def list_assignments():
        return jsonify(
            app.remote.get(
                "course/cal/cs61a/{}/assignments".format(get_semester())
            ).data
        )

    @app.route("/api/save_backup", methods=["POST"])
    def save_backup():
        file_name = request.form["file"]
        file_content = request.form["content"]
        assignment = request.form["assignment"]

        email = get_user_data(app)["email"]
        endpoint = "cal/cs61a/{}/{}".format(get_semester(), assignment)

        ret = app.remote.get(
            "assignment/{}/export/{}?limit=1".format(endpoint, email)
        ).data

        backups = ret["data"]["backups"]

        files = {file_name: file_content}

        if len(backups) > 0:
            assert len(backups) == 1
            messages = backups[0]["messages"]
            for message in messages:
                if message["kind"] == "file_contents":
                    for name, content in message["contents"].items():
                        if name == "submit":
                            continue
                        if name in files:
                            continue
                        files[name] = content

        ret = app.remote.post(
            "backups/",
            data={
                "assignment": endpoint,
                "submit": False,
                "messages": {"file_contents": files},
            },
            format="json",
        ).data

        return jsonify({"success": ret["message"] == "success"})
