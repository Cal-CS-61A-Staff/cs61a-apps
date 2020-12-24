import json

from examtool.api.database import get_exam
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import scramble, get_elements


def find_unexpected_words(exam, logs):
    data = get_exam(exam=exam)
    exam_json = json.dumps(data)
    original_questions = {q["id"]: q for q in extract_questions(json.loads(exam_json))}
    for i, (email, log) in enumerate(logs):
        all_alternatives = get_substitutions(data)
        scrambled_questions = {
            q["id"]: q
            for q in extract_questions(
                scramble(email, json.loads(exam_json), keep_data=True), nest_all=True
            )
        }
        flagged_questions = set()
        for record in log:
            record.pop("timestamp")
            question = next(iter(record.keys()))
            answer = next(iter(record.values()))

            if question not in all_alternatives or question in flagged_questions:
                continue

            student_substitutions = scrambled_questions[question]["substitutions"]

            for keyword in student_substitutions:
                for variant in all_alternatives[question][keyword]:
                    if variant == student_substitutions[keyword]:
                        continue
                    if variant in answer:
                        # check for false positives
                        if variant in scrambled_questions[question]["text"]:
                            continue

                        flagged_questions.add(question)

                        print(
                            "In question {}, Student {} used keyword {} for {}, when they should have used {}".format(
                                get_name(original_questions[question]),
                                email,
                                variant,
                                keyword,
                                student_substitutions[keyword],
                            )
                        )

                        print(
                            "\tThey wrote `{}`. Their substitutions were: {}".format(
                                " ".join(answer.split()), student_substitutions
                            )
                        )


def get_substitutions(exam):
    out = {}

    def process_group(group, substitutions):
        group_substitutions = group["substitutions"]
        for element in get_elements(group):
            if element.get("type") == "group":
                process_group(element, {**substitutions, **group_substitutions})
            else:
                process_question(element, {**substitutions, **group_substitutions})

    def process_question(question, substitutions):
        out[question["id"]] = {**substitutions, **question["substitutions"]}

    global_substitutions = exam["substitutions"]
    for group in exam["groups"]:
        process_group(group, global_substitutions)

    return out
