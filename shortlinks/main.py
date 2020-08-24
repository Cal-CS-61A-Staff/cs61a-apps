from flask import Flask, redirect, request

import urllib.parse as urlparse

from common.rpc.auth import read_spreadsheet


def add_url_params(url, params_string):
    parse_result = list(urlparse.urlsplit(url))
    parse_result[3] = "&".join(filter(lambda s: s, [parse_result[3], params_string]))
    return urlparse.urlunsplit(tuple(parse_result))


app = Flask(__name__)

links, author = {}, {}

DOC_URL = "https://docs.google.com/spreadsheets/d/1mc4ygwGMLVtyL3cdAcYe5T9TsAXuKxnzKUe9-mlSgGQ/edit"
SHEETS = ["Sheet1"]


@app.route("/<path>/")
def handler(path):
    if not links:
        refresh()
    if path in links and links[path]:
        return redirect(
            add_url_params(links[path], request.query_string.decode("utf-8"))
        )
    return base()


@app.route("/preview/<path>/")
def preview(path):
    if not links:
        refresh()
    if path not in links:
        return "No such link exists."
    return 'Points to <a href="{0}">{0}</a> by {1}'.format(
        add_url_params(links[path], request.query_string.decode("utf-8")), author[path]
    )


@app.route("/")
def base():
    return redirect("https://cs61a.org")


@app.route("/_refresh/")
def refresh():
    links.clear()
    author.clear()
    for sheet_name in SHEETS:
        csvr = read_spreadsheet(url=DOC_URL, sheet_name=sheet_name)
        headers = [x.lower() for x in csvr[0]]
        for row in csvr[1:]:
            row = row + [""] * 5
            shortlink = row[headers.index("shortlink")]
            url = row[headers.index("url")]
            creator = row[headers.index("creator")]
            links[shortlink] = url
            author[shortlink] = creator
    return "Links updated"


if __name__ == "__main__":
    app.run()
