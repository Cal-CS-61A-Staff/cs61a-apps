import time
from os import getenv

from flask import jsonify, abort
from google.cloud import firestore
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

from api import (
    process_ok_exam_upload,
    is_admin,
    clear_collection,
    get_announcements,
    get_email_from_secret,
    generate_audio,
)

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

        if request.path.endswith("list_exams"):
            return jsonify(
                db.collection("exam-alerts")
                .document("all")
                .get()
                .to_dict()["exam-list"]
            )

        if request.path == "/" or request.json is None:
            return main_html

        if request.path.endswith("upload_ok_exam"):
            process_ok_exam_upload(db, request.json["data"], request.json["secret"])
            return jsonify({"success": True})

        exam = request.json["exam"]
        course = exam.split("-")[0]

        if request.path.endswith("fetch_data"):
            received_audio = request.json.get("receivedAudio")
            email = get_email(request)
            student_data = (
                db.collection("exam-alerts")
                .document(exam)
                .collection("students")
                .document(email)
                .get()
                .to_dict()
            )
            announcements = list(
                db.collection("exam-alerts")
                .document(exam)
                .collection("announcements")
                .stream()
            )
            return jsonify(
                {
                    "success": True,
                    "exam_type": "ok-exam",
                    "questions": [],
                    "startTime": student_data["start_time"],
                    "endTime": student_data["end_time"],
                    # "questions": [
                    #     {
                    #         "questionName": question["student_question_name"],
                    #         "startTime": question["start_time"],
                    #         "endTime": question["end_time"],
                    #     }
                    #     for question in student_data["questions"]
                    # ],
                    "announcements": get_announcements(
                        student_data,
                        announcements,
                        received_audio,
                        lambda x: (
                            db.collection("exam-alerts")
                            .document(exam)
                            .collection("announcement_audio")
                            .document(x)
                            .get()
                            .to_dict()
                            or {}
                        ).get("audio"),
                    ),
                }
            )

        # only staff endpoints from here onwards
        email = (
            get_email_from_secret(request.json["secret"])
            if "secret" in request.json
            else get_email(request)
        )
        if not is_admin(email, course):
            abort(401)

        if request.path.endswith("fetch_staff_data"):
            pass
        elif request.path.endswith("add_announcement"):
            announcement = request.json["announcement"]
            announcement["timestamp"] = time.time()
            ref = (
                db.collection("exam-alerts")
                .document(exam)
                .collection("announcements")
                .document()
            )
            ref.set(announcement)
            spoken_message = announcement.get("spoken_message", announcement["message"])

            if spoken_message:
                audio = generate_audio(spoken_message)
                db.collection("exam-alerts").document(exam).collection(
                    "announcement_audio"
                ).document(ref.id).set({"audio": audio})

        elif request.path.endswith("clear_announcements"):
            clear_collection(
                db,
                db.collection("exam-alerts").document(exam).collection("announcements"),
            )
            clear_collection(
                db,
                db.collection("exam-alerts")
                .document(exam)
                .collection("announcement_audio"),
            )
        elif request.path.endswith("delete_announcement"):
            target = request.json["id"]
            db.collection("exam-alerts").document(exam).collection(
                "announcements"
            ).document(target).delete()
        else:
            abort(404)

        # all staff endpoints return an updated state
        exam_data = db.collection("exam-alerts").document(exam).get().to_dict()
        announcements = sorted(
            (
                {"id": announcement.id, **announcement.to_dict()}
                for announcement in db.collection("exam-alerts")
                .document(exam)
                .collection("announcements")
                .stream()
            ),
            key=lambda announcement: announcement["timestamp"],
            reverse=True,
        )
        return jsonify(
            {"success": True, "exam": exam_data, "announcements": announcements}
        )

    except Exception as e:
        if getenv("ENV") == "dev":
            raise
        print(e)
        print(dict(request.json))
        return jsonify({"success": False})
