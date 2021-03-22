from examtool.api.extract_questions import extract_questions


def get_question_substitutions(original_questions, scrambled_questions, question_id):
    original_question = original_questions[question_id]
    substitutions = {}
    for original, replacement in (
        scrambled_questions[question_id].get("substitutions", {}).items()
    ):
        if original in original_question["text"]:
            substitutions[original] = replacement
    return substitutions


def get_all_substitutions(original_exam, scrambled_exam):
    assert (
        original_exam is not scrambled_exam
    ), "You must make a copy of the original before scrambling it"
    original_questions = {q["id"]: q for q in extract_questions(original_exam)}
    scrambled_questions = {q["id"]: q for q in extract_questions(scrambled_exam)}
    question_substitutions = {}
    for question_id in scrambled_questions:
        question_substitutions[question_id] = get_question_substitutions(
            original_questions, scrambled_questions, question_id
        )
    return question_substitutions
