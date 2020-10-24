from os import getenv

from examtool.api.server_delegate import server_only
from examtool.api.utils import as_list

if getenv("ENV") == "SERVER":
    from google.cloud import firestore
    from google.cloud.exceptions import NotFound

BATCH_SIZE = 400
assert BATCH_SIZE < 500


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


def valid(id: str):
    if "/" in id or ".." in id:
        raise Exception("Invalid id!")
    return id


@server_only
def get_exam(*, exam):
    try:
        db = firestore.Client()
        out = db.collection("exams").document(valid(exam)).get().to_dict()
        if "secret" in out and isinstance(out["secret"], bytes):
            out["secret"] = out["secret"].decode("utf-8")
        return out
    except NotFound:
        raise KeyError


@server_only
def set_exam(*, exam, json):
    db = firestore.Client()
    db.collection("exams").document(valid(exam)).set(json)

    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam not in data["exam-list"]:
        data["exam-list"].append(exam)
    ref.set(data)


@server_only
@as_list
def get_roster(*, exam):
    db = firestore.Client()
    for student in (
        db.collection("roster").document(valid(exam)).collection("deadline").stream()
    ):
        yield student.id, student.to_dict()["deadline"]


@server_only
def set_roster(*, exam, roster):
    db = firestore.Client()

    ref = db.collection("roster").document(valid(exam)).collection("deadline")

    batch = db.batch()
    cnt = 0
    for document in ref.stream():
        batch.delete(document.reference)
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()

    batch = db.batch()
    cnt = 0
    for email, deadline in roster:
        doc_ref = ref.document(valid(email))
        batch.set(doc_ref, {"deadline": int(deadline)})
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()


@server_only
@as_list
def get_submissions(*, exam):
    db = firestore.Client()

    for ref in db.collection(valid(exam)).stream():
        yield ref.id, ref.to_dict()


@server_only
@as_list
def get_logs(*, exam, email):
    db = firestore.Client()

    for ref in (
        db.collection(valid(exam)).document(valid(email)).collection("log").stream()
    ):
        yield ref.to_dict()


@server_only
def process_ok_exam_upload(*, exam, data, clear=True):
    """
    data: {
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
    db = firestore.Client()

    db.collection("exam-alerts").document(valid(exam)).set(
        {"questions": data["questions"]}
    )
    ref = db.collection("exam-alerts").document(valid(exam)).collection("students")
    if clear:
        clear_collection(db, ref)

    batch = db.batch()
    cnt = 0
    for student in data["students"]:
        doc_ref = ref.document(valid(student["email"]))
        batch.set(doc_ref, student)
        cnt += 1
        if cnt > BATCH_SIZE:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()

    ref = db.collection("exam-alerts").document("all")
    exam_list_data = ref.get().to_dict()
    if exam not in exam_list_data["exam-list"]:
        exam_list_data["exam-list"].append(exam)
    ref.set(exam_list_data)
