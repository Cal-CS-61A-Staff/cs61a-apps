from flask import Flask, redirect, request

app = Flask(__name__)


LOOKUP = dict(
    tutor="http://pythontutor.com/composingprograms.html",  # deliberately http, it doesn't support https
    book="https://composingprograms.com",
    wiki="https://www.ocf.berkeley.edu/~shidi/cs61a/wiki",
    python="https://code.cs61a.org/python",
    scheme="https://code.cs61a.org/scheme",
    sql="https://code.cs61a.org/sql",
)


def lookup(hostname):
    if hostname in LOOKUP:
        return LOOKUP[hostname]
    prefix = hostname.split(".")[0]
    if prefix in LOOKUP:
        return LOOKUP[prefix]
    return f"https://inst.eecs.berkeley.edu/~cs61a/{prefix}"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    hostname = request.headers["HOST"]
    return redirect(f"{lookup(hostname)}/{path}")


if __name__ == "__main__":
    app.run()
