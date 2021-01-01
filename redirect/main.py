from flask import Flask, redirect, request

app = Flask(__name__)


LOOKUP = {
    "tutor": "http://pythontutor.com/composingprograms.html",
    "book": "https://composingprograms.com",
    "python": "https://code.cs61a.org/python",
    "scheme": "https://code.cs61a.org/scheme",
    "sql": "https://code.cs61a.org/sql",
    "ok-help": "https://ok-help.cs61a.org",
}


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
    if path:
        return redirect(f"{lookup(hostname)}/{path}")
    else:
        return redirect(lookup(hostname))


if __name__ == "__main__":
    app.run()
