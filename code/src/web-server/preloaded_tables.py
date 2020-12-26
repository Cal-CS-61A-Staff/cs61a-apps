import re
from base64 import b64encode, b64decode

import requests
from flask import jsonify

from common.db import connect_db
from common.rpc.auth import read_spreadsheet
from constants import CSV_ROOT


def create_preloaded_tables(app):
    @app.route("/api/preloaded_tables", methods=["POST"])
    def preloaded_tables():
        try:
            with connect_db() as db:
                return jsonify(
                    {
                        "success": True,
                        "data": b64decode(
                            db("SELECT data FROM preloaded_tables").fetchone()[0]
                        ).decode("utf-8"),
                    }
                )
        except Exception as e:
            print(e)
            return jsonify({"success": False, "data": ""})


def setup_preloaded_tables():
    # refresh SQL preloaded tables
    parsed = iter(read_spreadsheet(url=CSV_ROOT, sheet_name="Preloaded SQL Tables"))
    next(parsed)  # discard headers
    init_sql = []
    for line in parsed:
        url, *_ = line
        resp = requests.get(url)
        if resp.status_code == 200:
            init_sql.append(resp.text)
    with connect_db() as db:
        joined_sql = "\n\n".join(init_sql)
        joined_sql = re.sub(
            r"create\s+table(?!\s+if\b)",
            "CREATE TABLE IF NOT EXISTS ",
            joined_sql,
            flags=re.IGNORECASE,
        )
        encoded = b64encode(bytes(joined_sql, "utf-8"))
        db("DROP TABLE IF EXISTS preloaded_tables")
        db("CREATE TABLE preloaded_tables (data LONGBLOB)")
        db("INSERT INTO preloaded_tables VALUES (%s)", [encoded])
