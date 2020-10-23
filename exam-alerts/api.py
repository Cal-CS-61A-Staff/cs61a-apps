import base64
import time
from os import getenv
from typing import TYPE_CHECKING
from google.cloud import texttospeech

import requests
from flask import abort

if TYPE_CHECKING:
    from google.cloud import firestore

BATCH_SIZE = 400
assert BATCH_SIZE < 500


def get_email_from_secret(secret):
    ret = requests.get("https://okpy.org/api/v3/user/", params={"access_token": secret})
    if ret.status_code != 200:
        abort(401)
    return ret.json()["data"]["email"]


def is_admin(email, course):
    if getenv("ENV") == "dev":
        return True
    return requests.post(
        "https://auth.apps.cs61a.org/admins/is_admin",
        json={
            "client_name": getenv("AUTH_CLIENT_NAME"),
            "secret": getenv("AUTH_CLIENT_SECRET"),
            "email": email,
            "course": course,
        },
    ).json()


def clear_collection(db: "firestore.Client", ref):
    batch = db.batch()
    cnt = 0
    for document in ref.stream():
        batch.delete(document.reference)
        cnt += 1
        if cnt > BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()


def process_ok_exam_upload(db: "firestore.Client", data, secret):
    """
    data: {
        "exam_name": string,
        "students": [
            {
                "email": string,
                "questions": [
                    {
                        "student_question_name": string,
                        "canonical_question_name": string,
                        "start_time": int,
                        "end_time": int,
                    }
                ],
                "start_time": int,
                "end_time": int,
            }
        ]
        "questions": [
            {
                "canonical_question_name": string,
            }
        ],
    }
    """
    course = data["exam_name"].split("-")[0]
    email = get_email_from_secret(secret)
    if not is_admin(email, course):
        abort(403)
    db.collection("exam-alerts").document(data["exam_name"]).set(
        {"questions": data["questions"]}
    )
    ref = (
        db.collection("exam-alerts").document(data["exam_name"]).collection("students")
    )
    clear_collection(db, ref)

    batch = db.batch()
    cnt = 0
    for student in data["students"]:
        doc_ref = ref.document(student["email"])
        batch.set(doc_ref, student)
        cnt += 1
        if cnt > BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()

    ref = db.collection("exam-alerts").document("all")
    exam_list_data = ref.get().to_dict()
    if data["exam_name"] not in exam_list_data["exam-list"]:
        exam_list_data["exam-list"].append(data["exam_name"])
    ref.set(exam_list_data)


def get_announcements(student_data, announcements, received_audio, get_audio):
    """
    Announcements are of the form
    {
        type: "scheduled" | "immediate",
        canonical_question_name: string,
        offset: int,
        base: "start" | "end",
        message: string,
        spoken_message: ?string
    }
    Immediate announcements only need a message. If no question name is provided, the announcement will be
    made relative to the exam start/end, otherwise it will be relative to the question
    when that question starts / ends.
    """
    to_send = []
    request_time = time.time()

    if request_time > student_data["end_time"] + 45 * 60:
        return []

    for announcement in announcements:
        announcement_id, announcement = announcement.id, announcement.to_dict()

        def include_it(time):
            to_send.append(
                {
                    "id": announcement_id,
                    "time": time,
                    "message": announcement["message"],
                    "question": announcement.get("question", "Overall Exam"),
                }
            )
            if received_audio is not None and announcement_id not in received_audio:
                to_send[-1]["audio"] = get_audio(announcement_id)

        question_name = announcement.get("canonical_question_name")
        if question_name:
            for question in student_data["questions"]:
                if question["canonical_question_name"].strip() == question_name.strip():
                    event = question
                    announcement["question"] = question["student_question_name"]
                    break
            else:
                # student did not receive this question
                continue
        else:
            event = student_data

        if announcement["type"] == "immediate":
            include_it(announcement["timestamp"])
        elif announcement["type"] == "scheduled":
            threshold = (
                event["start_time"]
                if announcement["base"] == "start"
                else event["end_time"]
            )
            threshold += int(announcement["offset"])

            if request_time >= threshold:
                include_it(threshold)

    to_send.sort(key=lambda x: x["time"])
    to_send.reverse()
    return to_send


def generate_audio(message):
    message = "Attention students. " + message

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput({"text": message})
    voice = texttospeech.VoiceSelectionParams(
        {
            "name": "en-US-Wavenet-B",
            "language_code": "en-US",
        }
    )
    audio_config = texttospeech.AudioConfig(
        {"audio_encoding": texttospeech.AudioEncoding.MP3}
    )

    audio = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    ).audio_content

    audio = base64.b64encode(audio).decode("ascii")

    return audio
