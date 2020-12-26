import csv

import requests

from common.db import connect_db
from common.rpc.auth import read_spreadsheet
from constants import CSV_ROOT, ServerFile


def attempt_named_shortlinks(path):
    with connect_db() as db:
        ret = db("SELECT * FROM links WHERE short_link=%s;", [path]).fetchone()
        if ret is not None:
            return ServerFile(
                ret[0], ret[1], ret[2], ret[3].decode(), None, ret[4]
            )._asdict()


def setup_named_shortlinks():
    parsed = iter(read_spreadsheet(url=CSV_ROOT, sheet_name="Shortlinks"))
    next(parsed)  # discard headers
    all_files = []
    for line in parsed:
        short_link, full_name, url, discoverable, *_ = line
        data = requests.get(url).text
        file = ServerFile(
            short_link, full_name, url, data, None, int(discoverable == "TRUE")
        )
        all_files.append(file)

    with connect_db() as db:
        db("DROP TABLE IF EXISTS links")
        db(
            """CREATE TABLE links (
    short_link varchar(128), 
    full_name varchar(128), 
    url varchar(1024), 
    data LONGBLOB, 
    discoverable BOOLEAN)"""
        )
        db(
            "INSERT INTO links VALUES (%s, %s, %s, %s, %s)",
            [[x[:4] + x[5:]] for x in all_files],
        )
