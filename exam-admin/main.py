from os import getenv

from flask import jsonify, abort
from google.auth.transport import requests as g_requests
from google.cloud import firestore
from google.oauth2 import id_token

from api import handle_api_call, is_admin

from examtool.api.database import valid

# this can be public
CLIENT_ID = "713452892775-59gliacuhbfho8qvn4ctngtp3858fgf9.apps.googleusercontent.com"

DEV_EMAIL = getenv("DEV_EMAIL", "exam-test@berkeley.edu")


def update_cache():
    global main_html, main_js
    with open("static/index.html") as f:
        main_html = f.read()

    with open("static/main.js") as f:
        main_js = f.read()


update_cache()


def get_email(request):
    if getenv("ENV") == "dev":
        return DEV_EMAIL

    token = request.json["token"]

    # validate token
    id_info = id_token.verify_oauth2_token(token, g_requests.Request(), CLIENT_ID)

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError("Wrong issuer.")

    return id_info["email"]


def index(request):
    try:
        if getenv("ENV") == "dev":
            update_cache()

        db = firestore.Client()

        if request.path.endswith("main.js"):
            return main_js

        if request.path == "/" or request.path == "/admin/":
            return main_html

        if request.path.endswith("is_valid"):
            return jsonify(
                {"success": is_admin(get_email(request), request.json["course"])}
            )

        if "api" in request.path:
            method = request.path.split("/")[-1]
            return handle_api_call(method, request.json)

        if not is_admin(get_email(request), request.json["course"]):
            abort(401)

        course = request.json["course"]

        if request.path.endswith("list_exams"):
            exams = db.collection("exams").document("all").get().to_dict()["exam-list"]
            return jsonify([exam for exam in exams if exam.startswith(course + "-")])

        if request.path.endswith("get_exam"):
            exam = request.json["exam"]
            if not exam.startswith(course):
                abort(401)
            exam_json = db.collection("exams").document(valid(exam)).get().to_dict()
            secret = exam_json.pop("secret")
            return jsonify(
                {
                    "exam": exam_json,
                    "secret": secret[:-1],
                }
            )

    except:
        return jsonify({"success": False})

    return request.path
