import json
import time
from os import getenv

import requests
from google.auth.transport.requests import Request
from cryptography.fernet import Fernet
from flask import jsonify, abort
from google.oauth2 import id_token
from google.cloud.exceptions import NotFound

from examtool.api.scramble import scramble

from examtool_web_common.safe_firestore import SafeFirestore

# this can be public

CLIENT_ID = "713452892775-59gliacuhbfho8qvn4ctngtp3858fgf9.apps.googleusercontent.com"

DEV_EMAIL = getenv("DEV_EMAIL", "exam-test@berkeley.edu")

if getenv("ENV") == "dev":
    import importlib.util
    import sys
    from os.path import abspath

    for name in ["api", "main"]:
        spec = importlib.util.spec_from_file_location(
            name, abspath("../exam-alerts/{}.py".format(name))
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["alerts" if name == "main" else name] = module
        spec.loader.exec_module(module)


def update_cache():
    global main_html, main_js
    with open("static/index.html") as f:
        main_html = f.read()

        if getenv("ENV") == "dev":
            main_html = main_html.replace("production.min", "development")

    with open("static/main.js") as f:
        main_js = f.read()


update_cache()


def get_email(request):
    if getenv("ENV") == "dev":
        return request.json.get("loginas") or DEV_EMAIL, "loginas" in request.json

    token = request.json["token"]

    # validate token
    id_info = id_token.verify_oauth2_token(token, Request(), CLIENT_ID)

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError("Wrong issuer.")

    email = id_info["email"]

    if "loginas" in request.json:
        exam = request.json["exam"]
        course = exam.split("-")[0]
        is_admin = requests.post(
            "https://auth.cs61a.org/admins/is_admin",
            json={
                "secret": getenv("AUTH_CLIENT_SECRET"),
                "email": email,
                "course": course,
            },
        ).json()
        if is_admin is not True:
            raise PermissionError("Only admins can login as a student")
        return request.json["loginas"], True

    return email, False


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

    abort(401)


def index(request):
    try:
        if getenv("ENV") == "dev":
            update_cache()

        db = SafeFirestore()

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
            email, is_admin = get_email(request)
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
            if deadline + 120 < time.time() and not is_admin:
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
            email, is_admin = get_email(request)

            db.collection(exam).document(email).collection("log").document().set(
                {"timestamp": time.time(), "sentTime": sent_time, question_id: value}
            )

            deadline = get_deadline(exam, email, db)

            if deadline + 120 < time.time() and not is_admin:
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

        if request.path.endswith("backup_all"):
            exam = request.json["exam"]
            email, is_admin = get_email(request)
            history = request.json["history"]
            snapshot = request.json["snapshot"]
            db.collection(exam).document(email).collection("history").document().set(
                {"timestamp": time.time(), "history": history, "snapshot": snapshot}
            )
            return jsonify({"success": True})

        if getenv("ENV") == "dev" and "alerts" in request.path:
            from alerts import index as alerts_index

            return alerts_index(request)

    except Exception as e:
        if getenv("ENV") == "dev":
            raise
        print(e)
        print(dict(request.json))
        return jsonify({"success": False})

    return request.path
