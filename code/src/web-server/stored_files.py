import requests
from flask import abort

from common.db import connect_db
from common.rpc.auth import read_spreadsheet
from constants import CSV_ROOT


def create_stored_files(app):
    @app.route("/api/load_file/<file_name>")
    def load_stored_file(file_name):
        with connect_db() as db:
            out = db(
                "SELECT * FROM stored_files WHERE file_name=%s;", [file_name]
            ).fetchone()
            if out:
                return out[1]
        abort(404)


def setup_stored_files():
    # refresh stored files
    parsed = iter(read_spreadsheet(url=CSV_ROOT, sheet_name="Saved Files"))
    next(parsed)  # discard headers
    stored_files = []
    for line in parsed:
        file_name, url, *_ = line
        data = requests.get(url).text
        stored_files.append([file_name, data])
    with connect_db() as db:
        db("DROP TABLE IF EXISTS stored_files")
        db("CREATE TABLE stored_files (file_name varchar(128), file_contents LONGBLOB)")
        db("INSERT INTO stored_files VALUES (%s, %s)", stored_files)
