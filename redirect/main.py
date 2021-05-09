from flask import Flask, redirect, request

app = Flask(__name__)


LOOKUP = {
    "tutor": "http://pythontutor.com/composingprograms.html",
    "book": "https://composingprograms.com",
    "python": "https://code.cs61a.org/python",
    "scheme": "https://code.cs61a.org/scheme",
    "sql": "https://code.cs61a.org/sql",
    "ok-help": "https://ok-help.cs61a.org",
    "ok": "https://okpy.org",
    "staging": "https://solutions.cs61a.org",
}


def lookup(hostname):
    """Gets the URL to redirect to based on a hostname.

    :param hostname: redirect link to check
    :type hostname: string

    :return: a string that represents the url to redirect to
    """
    if hostname in LOOKUP:
        return LOOKUP[hostname]
    prefix = hostname.split(".")[0]
    if prefix in LOOKUP:
        return LOOKUP[prefix]
    return f"https://inst.eecs.berkeley.edu/~cs61a/{prefix}"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    """Gets the URL to redirect to based on a path if it exists.

    :param path: path to return to, doesn't have to exist
    :type path: string
    
    :return: a string that represents the url to redirect to
    """
    hostname = request.headers["HOST"]
    if path:
        return redirect(f"{lookup(hostname)}/{path}")
    else:
        return redirect(lookup(hostname))


if __name__ == "__main__":
    app.run()
