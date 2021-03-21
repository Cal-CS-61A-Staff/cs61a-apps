from os import getenv

from examtool.api.server_delegate import server_only
from examtool.api.utils import as_list

if getenv("ENV") == "SERVER":
    from examtool_web_common.safe_firestore import SafeFirestore
    from google.cloud.exceptions import NotFound

BATCH_SIZE = 400
assert BATCH_SIZE < 500


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


@server_only
def get_exam(*, exam):
    try:
        db = SafeFirestore()
        out = db.collection("exams").document(exam).get().to_dict()
        if "secret" in out and isinstance(out["secret"], bytes):
            out["secret"] = out["secret"].decode("utf-8")
        return out
    except NotFound:
        raise KeyError


@server_only
def set_exam(*, exam, json):
    db = SafeFirestore()
    db.collection("exams").document(exam).set(json)

    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam not in data["exam-list"]:
        data["exam-list"].append(exam)
    ref.set(data)


@server_only
@as_list
def get_roster(*, exam, include_no_watermark=False):
    db = SafeFirestore()
    for student in (
        db.collection("roster").document(exam).collection("deadline").stream()
    ):
        if include_no_watermark:
            yield (
                student.id,
                student.to_dict()["deadline"],
                student.to_dict().get("no_watermark", False),
            )
        else:
            yield student.id, student.to_dict()["deadline"]


@server_only
def set_roster(*, exam, roster):
    db = SafeFirestore()

    ref = db.collection("roster").document(exam).collection("deadline")
    emails = []

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
    for email, deadline, *rest in roster:
        assert len(rest) <= 1
        doc_ref = ref.document(email)
        batch.set(
            doc_ref,
            {
                "deadline": int(deadline),
                "no_watermark": bool(int(rest[0]) if rest else False),
            },
        )
        emails.append(email)
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()

    ref = db.collection("roster").document(exam)
    data = {"all_students": emails}
    ref.set(data)


@server_only
@as_list
def get_submissions(*, exam):
    db = SafeFirestore()

    for ref in db.collection(exam).stream():
        yield ref.id, ref.to_dict()


@server_only
@as_list
def get_logs(*, exam, email):
    db = SafeFirestore()

    for ref in db.collection(exam).document(email).collection("log").stream():
        yield ref.to_dict()


@server_only
@as_list
def get_full_logs(*, exam, email):
    db = SafeFirestore()

    for ref in db.collection(exam).document(email).collection("history").stream():
        yield ref.to_dict()


@server_only
def process_ok_exam_upload(*, exam, data, enable_clarifications=False, clear=True):
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
    db = SafeFirestore()

    db.collection("exam-alerts").document(exam).set(
        {"questions": data["questions"], "enable_clarifications": enable_clarifications}
    )
    ref = db.collection("exam-alerts").document(exam).collection("students")
    if clear:
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
    if exam not in exam_list_data["exam-list"]:
        exam_list_data["exam-list"].append(exam)
    ref.set(exam_list_data)
