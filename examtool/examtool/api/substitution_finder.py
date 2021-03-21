import json
from dataclasses import dataclass
from typing import Dict

from examtool.api.utils import dict_to_list
from tqdm import tqdm

from examtool.api.database import get_exam, get_roster
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import scramble, get_elements


@dataclass
class SuspectedCheating:
    question: str
    email: str
    base_keyword: str
    expected: str
    observed: str
    answer: str
    substitutions: Dict[str, str]

    def explain(self):
        print(
            f"In question {self.question}, student {self.email} used keyword {self.observed} for "
            f"{self.base_keyword}, when they should have used {self.expected}"
        )

        print(
            f"\tThey wrote `{' '.join(self.answer.split())}`. Their substitutions were: {self.substitutions}"
        )


def find_unexpected_words(exam, logs):
    data = get_exam(exam=exam)
    exam_json = json.dumps(data)
    original_questions = {q["id"]: q for q in extract_questions(json.loads(exam_json))}
    suspected_cheating = []
    for i, (email, log) in enumerate(tqdm(logs)):
        all_alternatives = get_substitutions(data)
        scrambled_questions = {
            q["id"]: q
            for q in extract_questions(
                scramble(email, json.loads(exam_json), keep_data=True), nest_all=True
            )
        }
        flagged_question_variants = set()
        for record in log:
            record.pop("timestamp")
            for question, answer in record.items():
                question = question.split("|")[0]
                if question not in all_alternatives:
                    continue

                student_substitutions = scrambled_questions[question]["substitutions"]

                for keyword in student_substitutions:
                    for variant in all_alternatives[question][keyword]:
                        if variant == student_substitutions[keyword]:
                            continue
                        if (question, keyword, variant) in flagged_question_variants:
                            continue
                        if variant in answer:
                            # check for false positives
                            if variant in scrambled_questions[question]["text"]:
                                continue

                            flagged_question_variants.add((question, keyword, variant))

                            suspected_cheating.append(
                                SuspectedCheating(
                                    get_name(original_questions[question]),
                                    email,
                                    keyword,
                                    student_substitutions[keyword],
                                    variant,
                                    answer,
                                    student_substitutions,
                                )
                            )

    return suspected_cheating


def find_keyword(exam, phrase):
    data = get_exam(exam=exam)
    exam_json = json.dumps(data)
    for email, _ in get_roster(exam=exam):
        scrambled = scramble(email, json.loads(exam_json))
        if phrase in json.dumps(scrambled):
            print(email)


def get_substitutions(exam):
    out = {}

    def process_element(element):
        substitutions = element.get("substitutions", {}).copy()
        for item in element.get("substitutions_match", []):
            for directive in item["directives"]:
                substitutions[directive] = item["replacements"]
        for blocks in element.get("substitution_groups", []):
            directives = blocks["directives"]
            replacements = dict_to_list(blocks["replacements"])
            for directive, directive_replacements in zip(
                directives, zip(*(dict_to_list(d) for d in replacements))
            ):
                substitutions[directive] = directive_replacements
        for key in element.get("substitution_ranges", {}):
            substitutions[key] = []  # hack to make RANGEs not crash
        return substitutions

    def process_group(group, substitutions):
        group_substitutions = process_element(group)
        for element in get_elements(group):
            if element.get("type") == "group":
                process_group(element, {**substitutions, **group_substitutions})
            else:
                process_question(element, {**substitutions, **group_substitutions})

    def process_question(question, substitutions):
        out[question["id"]] = {**substitutions, **process_element(question)}

    global_substitutions = process_element(exam)
    for group in exam["groups"]:
        process_group(group, global_substitutions)

    return out
