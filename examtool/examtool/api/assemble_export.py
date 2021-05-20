from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from tqdm import tqdm

from examtool.api.extract_questions import get_name
from examtool.api.grade import grade


@dataclass(frozen=True)
class AssembledExam:
    exam: str
    email: str
    name: str
    sid: str
    questions: List[Question]


@dataclass(frozen=True)
class Question:
    name: str
    prompt: Text
    autograde_output: str


@dataclass(frozen=True)
class OptionQuestion(Question):
    options: List[Text]
    selected: List[Text]


@dataclass(frozen=True)
class Text:
    text: str
    tex: str
    html: str

    def __init__(self, element):
        for k in ["text", "tex", "html"]:
            object.__setattr__(self, k, element[k])


@dataclass(frozen=True)
class TextQuestion(Question):
    response: str
    height: int


def assemble_exam(
    exam: str,
    email: Optional[str],
    response: Dict[str, Union[str, List[str]]],
    template_questions: List[Dict],
    student_questions: List[Dict],
    name_question: str,
    sid_question: str,
    dispatch,
    substitute_in_question_text: bool = False,
):
    questions = []

    exam = AssembledExam(
        exam=exam,
        email=email,
        name=response.get(name_question, "NO NAME"),
        sid=response.get(sid_question, "NO SID"),
        questions=questions,
    )

    student_question_lookup = {q["id"]: q for q in student_questions}

    for question in template_questions:
        question_name = get_name(question)

        if substitute_in_question_text:
            question_text = Text(student_question_lookup.get(question["id"], question))
        else:
            question_text = Text(question)

        autograde_output = (
            grade(
                email,
                student_question_lookup[question["id"]],
                response,
                dispatch,
            )
            if question["id"] in response and question["id"] in student_question_lookup
            else "STUDENT LEFT QUESTION BLANK"
            if question["id"] in student_question_lookup
            else "STUDENT DID NOT RECEIVE QUESTION"
        )

        if question.get("type") in ["multiple_choice", "select_all"]:
            selected_options = response.get(question["id"], [])
            if question.get("type") == "multiple_choice" and not isinstance(
                selected_options, list
            ):
                selected_options = [selected_options]

            available_options = [Text(option) for option in question["options"]]
            if question["id"] not in student_question_lookup:
                student_options = available_options
            else:
                student_options = [
                    option["text"]
                    for option in sorted(
                        student_question_lookup[question["id"]]["options"],
                        key=lambda option: option.get("index", ""),
                    )
                ]

            assert len(available_options) == len(student_options)

            assembled_question = OptionQuestion(
                name=question_name,
                prompt=question_text,
                options=available_options,
                selected=(
                    [
                        option
                        for i, option in enumerate(available_options)
                        if student_options[i] in selected_options
                    ]
                ),
                autograde_output=autograde_output,
            )

        else:
            assembled_question = TextQuestion(
                name=question_name,
                prompt=question_text,
                autograde_output=autograde_output,
                response=response.get(question["id"], "").replace("\t", " " * 4),
                height=question.get("options") or 1
                if question["type"].startswith("long")
                else 1,
            )

        questions.append(assembled_question)

    return exam


def export(
    template_questions,
    student_responses,
    exam,
    name_question,
    sid_question,
    *,
    dispatch=None,
    include_outline=True,
    substitute_in_question_text=False,
):
    assembles = {}

    if include_outline:
        assembles["OUTLINE"] = assemble_exam(
            exam,
            None,
            {},
            template_questions,
            template_questions,
            name_question,
            sid_question,
            dispatch,
        )

    for email, data in tqdm(student_responses.items(), desc="Assembling", unit="Exam"):
        assembles[email] = assemble_exam(
            exam,
            email,
            data.get("responses"),
            template_questions,
            data.get("student_questions"),
            name_question,
            sid_question,
            dispatch,
            substitute_in_question_text=substitute_in_question_text,
        )

    return assembles
