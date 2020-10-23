import json
import time
from os import getenv

from cryptography.fernet import Fernet
from flask import jsonify, abort
from google.cloud import firestore
from google.oauth2 import id_token
from google.auth.transport import requests
from google.cloud.exceptions import NotFound

from examtool.api.scramble import scramble

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
    id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError("Wrong issuer.")

    return id_info["email"]


def get_exam_dict(exam, db):
    return db.collection("exams").document(exam).get().to_dict()


def get_deadline(exam, email, db):
    ref = db.collection("roster").document(exam).collection("deadline").document(email)
    try:
        data = ref.get().to_dict()
        if data:
            return data["deadline"]
    except NotFound:
        pass

    if not email.endswith("@berkeley.edu"):
        abort(401)
    exam_data = get_exam_dict(exam, db)
    if exam_data.get("default_deadline"):
        # log unexpected access
        ref = (
            db.collection("roster")
            .document(exam)
            .collection("unexpected_access_log")
            .document()
        )
        ref.set(
            {
                "timestamp": time.time(),
                "email": email,
            }
        )
        return exam_data["default_deadline"]
    else:
        abort(401)


def index(request):
    try:
        if getenv("ENV") == "dev":
            update_cache()

        db = firestore.Client()

        if request.path.endswith("main.js"):
            return main_js

        if request.path.endswith("list_exams"):
            return jsonify(
                db.collection("exams").document("all").get().to_dict()["exam-list"]
            )

        if request.path == "/" or request.json is None:
            return main_html

        if request.path.endswith("get_exam"):
            exam = request.json["exam"]
            email = get_email(request)
            ref = db.collection(exam).document(email)
            try:
                answers = ref.get().to_dict() or {}
            except NotFound:
                answers = {}

            deadline = get_deadline(exam, email, db)

            exam_data = get_exam_dict(exam, db)
            exam_data = scramble(
                email,
                exam_data,
            )

            # 120 second grace period in case of network latency or something
            if deadline + 120 < time.time():
                abort(401)
                return

            return jsonify(
                {
                    "success": True,
                    "exam": exam,
                    "publicGroup": exam_data["public"],
                    "privateGroups": (
                        Fernet(exam_data["secret"])
                        .encrypt_at_time(
                            json.dumps(exam_data["groups"]).encode("ascii"), 0
                        )
                        .decode("ascii")
                    ),
                    "answers": answers,
                    "deadline": deadline,
                    "timestamp": time.time(),
                }
            )

        if request.path.endswith("submit_question"):
            exam = request.json["exam"]
            question_id = request.json["id"]
            value = request.json["value"]
            sent_time = request.json.get("sentTime", 0)
            email = get_email(request)

            db.collection(exam).document(email).collection("log").document().set(
                {"timestamp": time.time(), "sentTime": sent_time, question_id: value}
            )

            deadline = get_deadline(exam, email, db)

            if deadline + 120 < time.time():
                abort(401)
                return

            recency_ref = (
                db.collection(exam)
                .document(email)
                .collection("recency")
                .document(question_id)
            )
            try:
                recency = recency_ref.get().to_dict() or {}
            except NotFound:
                recency = {}

            recent_time = recency.get("sentTime", -1)
            if recent_time - 300 <= sent_time <= recent_time:
                # the current request was delayed and is now out of date
                abort(409)
                return

            recency_ref.set({"sentTime": sent_time})

            db.collection(exam).document(email).set({question_id: value}, merge=True)
            return jsonify({"success": True})

        if getenv("ENV") == "dev" and request.path.endswith("alerts/fetch_data"):
            return jsonify(
                {
                    "success": True,
                    "announcements": [
                        {
                            "id": "SNlddetyVazQiMYaNL2w",
                            "message": "this is cool",
                            "question": "1.2.",
                            "time": 0,
                        }
                    ]
                    * 100,
                }
            )

    except:
        print(dict(request.json))
        return jsonify({"success": False})

    return request.path
