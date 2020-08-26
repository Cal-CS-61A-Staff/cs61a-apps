from flask import Flask

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


@app.route("/")
def index():
    return "Hello, world!"


if __name__ == "__main__":
    app.run(debug=True)
