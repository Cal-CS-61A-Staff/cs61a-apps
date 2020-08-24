from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("", "index.html")


@app.route("/t")
def time():
    return send_from_directory("", "t.html")


if __name__ == "__main__":
    app.run(debug=True)
