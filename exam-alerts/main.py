import time
from collections import defaultdict
from os import getenv

from flask import jsonify, abort
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

from api import (
    get_canonical_question_name,
    get_student_data,
    get_student_question_name,
    is_admin,
    clear_collection,
    get_announcements,
    get_email_from_secret,
    generate_audio,
)

# this can be public
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import scramble
from examtool_web_common.safe_firestore import SafeFirestore

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


def group_messages(message_list):
    students = defaultdict(list)
    messages = {}
    for message in message_list:
        if "reply_to" not in message:
            message = {**message, "responses": []}
            students[message["email"]].append(message)
            messages[message["id"]] = message
    for message in message_list:
        if "reply_to" in message:
            messages[message["reply_to"]]["responses"].append(message)
    for message in messages.values():
        message["responses"].sort(key=lambda response: response["timestamp"])
    return students


def index(request):
    try:
        if getenv("ENV") == "dev":
            update_cache()

        db = SafeFirestore()

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

        exam = request.json["exam"]
        course = exam.split("-")[0]

        student_reply = False

        if request.path.endswith("ask_question"):
            email = get_email(request)
            student_question_name = request.json["question"]
            message = request.json["message"]

            student_data = get_student_data(db, email, exam)

            if student_question_name is not None:
                canonical_question_name = get_canonical_question_name(
                    student_data, student_question_name
                )
                if canonical_question_name is None:
                    return abort(400)
            else:
                canonical_question_name = None

            db.collection("exam-alerts").document(exam).collection(
                "messages"
            ).document().set(
                dict(
                    question=canonical_question_name,
                    message=message,
                    email=email,
                    timestamp=time.time(),
                )
            )
            student_reply = True

        if request.path.endswith("fetch_data") or student_reply:
            received_audio = request.json.get("receivedAudio")
            email = get_email(request)
            exam_data = db.collection("exam-alerts").document(exam).get().to_dict()
            student_data = get_student_data(db, email, exam)
            announcements = list(
                db.collection("exam-alerts")
                .document(exam)
                .collection("announcements")
                .stream()
            )
            messages = [
                {**message.to_dict(), "id": message.id}
                for message in (
                    db.collection("exam-alerts")
                    .document(exam)
                    .collection("messages")
                    .stream()
                )
                if message.to_dict()["email"] == email
            ]

            messages = group_messages(messages)[email]

            for message in messages:
                if message["question"] is not None:
                    message["question"] = get_student_question_name(
                        student_data, message["question"]
                    )

            return jsonify(
                {
                    "success": True,
                    "exam_type": "ok-exam",
                    "enableClarifications": exam_data.get(
                        "enable_clarifications", False
                    ),
                    "startTime": student_data["start_time"],
                    "endTime": student_data["end_time"],
                    "timestamp": time.time(),
                    "questions": [
                        question["student_question_name"]
                        for question in student_data["questions"]
                    ]
                    if time.time() > student_data["start_time"]
                    else [],
                    "announcements": get_announcements(
                        student_data,
                        announcements,
                        messages,
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
                    "messages": sorted(
                        [
                            {
                                "id": message["id"],
                                "message": message["message"],
                                "time": message["timestamp"],
                                "question": message["question"] or "Overall Exam",
                                "responses": message["responses"],
                            }
                            for message in messages
                        ],
                        key=lambda message: message["time"],
                        reverse=True,
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
        elif request.path.endswith("send_response"):
            message_id = request.json["id"]
            reply = request.json["reply"]
            message = (
                db.collection("exam-alerts")
                .document(exam)
                .collection("messages")
                .document(message_id)
                .get()
            )
            ref = (
                db.collection("exam-alerts")
                .document(exam)
                .collection("messages")
                .document()
            )
            ref.set(
                {
                    "timestamp": time.time(),
                    "email": message.to_dict()["email"],
                    "reply_to": message.id,
                    "message": reply,
                }
            )
            audio = generate_audio(
                reply, prefix="A staff member sent the following reply: "
            )
            db.collection("exam-alerts").document(exam).collection(
                "announcement_audio"
            ).document(ref.id).set({"audio": audio})
        elif request.path.endswith("get_question"):
            question_title = request.json["id"]
            student = request.json["student"]
            student_data = get_student_data(db, student, exam)
            question_title = get_student_question_name(student_data, question_title)
            exam = db.collection("exams").document(exam).get().to_dict()
            questions = extract_questions(scramble(student, exam), include_groups=True)
            for question in questions:
                if get_name(question).strip() == question_title.strip():
                    return jsonify({"success": True, "question": question})
            abort(400)
        else:
            abort(404)

        # (almost) all staff endpoints return an updated state
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
        messages = sorted(
            [
                {
                    "email": email,
                    "messages": sorted(
                        messages, key=lambda x: x["timestamp"], reverse=True
                    ),
                }
                for email, messages in group_messages(
                    [
                        {**message.to_dict(), "id": message.id}
                        for message in db.collection("exam-alerts")
                        .document(exam)
                        .collection("messages")
                        .stream()
                    ]
                ).items()
            ],
            key=lambda x: (
                all(len(message["responses"]) > 0 for message in x["messages"]),
                -x["messages"][-1]["timestamp"],
                x["email"],
            ),
        )

        return jsonify(
            {
                "success": True,
                "exam": exam_data,
                "announcements": announcements,
                "messages": messages,
            }
        )

    except Exception as e:
        if getenv("ENV") == "dev":
            raise
        print(e)
        print(dict(request.json))
        return jsonify({"success": False})
