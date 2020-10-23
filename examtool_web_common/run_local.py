import os
import sys

from flask import Flask, request

sys.path.append(os.path.abspath("."))

from main import index

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def main(path="/"):
    return index(request)


if __name__ == "__main__":
    app.run()
