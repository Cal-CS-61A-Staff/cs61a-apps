import json

from examtool.api.database import get_exam, get_roster
from examtool.api.extract_questions import extract_questions
from examtool.api.scramble import scramble
from google.cloud import firestore
import warnings

warnings.filterwarnings(
    "ignore", "Your application has authenticated using end user credentials"
)


db = firestore.Client()
exams = [x.id for x in db.collection("exams").stream()]

for exam in exams:
    print("checking", exam)
    exam_json = json.dumps(get_exam(exam=exam))
    roster = get_roster(exam=exam)

    flagged = set()

    for email, _ in roster:
        template_questions = extract_questions(json.loads(exam_json))
        student_questions = list(
            extract_questions(scramble(email, json.loads(exam_json), keep_data=True))
        )
        student_question_lookup = {q["id"]: q for q in student_questions}
        for question in template_questions:
            if question["id"] not in student_question_lookup:
                continue
            if question["type"] not in ["multiple_choice", "select_all"]:
                continue
            if question["id"] in flagged:
                continue

            for i, option in enumerate(question["options"]):
                option["index"] = i

            s = lambda options: sorted(options, key=lambda q: q["text"])

            for a, b in zip(
                s(question["options"]),
                s(student_question_lookup[question["id"]]["options"]),
            ):
                if a["index"] != b.get("index", a["index"]):
                    flagged.add(question["id"])
                    continue

    if flagged:
        print(exam, flagged)
