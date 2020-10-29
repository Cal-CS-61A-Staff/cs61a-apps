import base64
import time
from os import getenv
from google.cloud import texttospeech

import requests
from flask import abort

from examtool.api.utils import rand_id
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import is_compressible_group, scramble

BATCH_SIZE = 400
assert BATCH_SIZE < 500


def get_email_from_secret(secret):
    ret = requests.get("https://okpy.org/api/v3/user/", params={"access_token": secret})
    if ret.status_code != 200:
        abort(401)
    return ret.json()["data"]["email"]


def get_student_data(db, student, exam):
    student_data = (
        db.collection("exam-alerts")
        .document(exam)
        .collection("students")
        .document(student)
        .get()
        .to_dict()
    )
    exam = db.collection("exams").document(exam).get().to_dict()
    student_data["questions"] = get_student_question_mapping(student, exam)
    return student_data


def get_student_question_mapping(student, exam):
    elements = list(extract_questions(exam, include_groups=True))
    for element in elements:
        element["id"] = element.get("id", rand_id())  # add IDs to groups
    elements = {
        element["id"]: get_name(element)
        for element in elements
        if element["type"] != "group" or not is_compressible_group(element)
    }
    return [
        {
            "student_question_name": get_name(element),
            "canonical_question_name": elements[element["id"]],
        }
        for element in list(
            extract_questions(scramble(student, exam), include_groups=True)
        )
    ]


def get_student_question_name(student_data, canonical_question_name):
    for question in student_data["questions"]:
        if (
            question["canonical_question_name"].strip()
            == canonical_question_name.strip()
        ):
            return question["student_question_name"]


def get_canonical_question_name(student_data, student_question_name):
    for question in student_data["questions"]:
        if question["student_question_name"].strip() == student_question_name.strip():
            return question["canonical_question_name"]


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


def clear_collection(db, ref):
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


def get_announcements(student_data, announcements, messages, received_audio, get_audio):
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
                    "private": False,
                }
            )
            if received_audio is not None and announcement_id not in received_audio:
                to_send[-1]["audio"] = get_audio(announcement_id)

        question_name = announcement.get("canonical_question_name")
        if question_name:
            student_question_name = get_student_question_name(
                student_data, question_name
            )
            if student_question_name is not None:
                announcement["question"] = student_question_name
            else:
                # student did not receive this question
                continue

        if announcement["type"] == "immediate":
            include_it(announcement["timestamp"])
        elif announcement["type"] == "scheduled":
            threshold = (
                student_data["start_time"]
                if announcement["base"] == "start"
                else student_data["end_time"]
            )
            threshold += int(announcement["offset"])

            if request_time >= threshold:
                include_it(threshold)

    for message in messages:
        for response in message["responses"]:
            to_send.append(
                {
                    "id": response["id"],
                    "time": response["timestamp"],
                    "message": response["message"],
                    "question": message["question"] or "Overall Exam",
                    "private": True,
                }
            )
            if received_audio is not None and response["id"] not in received_audio:
                to_send[-1]["audio"] = get_audio(response["id"])

    to_send.sort(key=lambda x: x["time"])
    to_send.reverse()
    return to_send


def generate_audio(message, prefix="Attention students. "):
    message = prefix + message

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
