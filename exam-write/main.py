import json
import os

from flask import Flask, abort, send_from_directory, request, jsonify, make_response

from examtool.api.convert import convert_str
from examtool.api.scramble import scramble
from examtool.api.gen_latex import render_latex

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/convert", methods=["POST"])
def convert():
    text = request.json["text"]
    draft = request.json.get("draft", False)
    seed = request.json.get("seed", False)
    text = text.replace("\r", "")
    try:
        exam = json.loads(convert_str(text, draft=draft))
        if seed:
            exam = scramble(seed, exam)
        return jsonify({"success": True, "examJSON": json.dumps(exam)})
    except SyntaxError as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/render", methods=["POST"])
def render():
    abort(401)  # PDF compilation is unsafe
    exam = json.loads(request.form["exam"])
    with render_latex(exam) as pdf:
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=exam.pdf"
        return response


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
