import csv
import json
import os
import pathlib

from fpdf import FPDF
from tqdm import tqdm

from examtool.api.database import get_exam, get_roster, get_submissions
from examtool.api.extract_questions import extract_questions
from examtool.api.grade import grade
from examtool.api.scramble import scramble


def write_exam(
    email,
    response,
    exam,
    template_questions,
    student_questions,
    name_question,
    sid_question,
    dispatch,
    out=None,
    substitute_in_question_text=False,
):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Courier", size=16)
    pdf.multi_cell(200, 20, txt=exam, align="L")
    pdf.multi_cell(
        200,
        20,
        txt=response.get(name_question, "NO NAME")
        .encode("latin-1", "replace")
        .decode("latin-1"),
        align="L",
    )
    pdf.multi_cell(
        200,
        20,
        txt=response.get(sid_question, "NO SID")
        .encode("latin-1", "replace")
        .decode("latin-1"),
        align="L",
    )

    pdf.set_font("Courier", size=9)

    if out is None:

        def out(text):
            pdf.multi_cell(
                200,
                5,
                txt=text.encode("latin-1", "replace")
                .decode("latin-1")
                .replace("\t", " " * 4),
                align="L",
            )

    student_question_lookup = {q["id"]: q for q in student_questions}

    for question in template_questions:
        pdf.add_page()
        out("\nQUESTION")
        if substitute_in_question_text:
            question_for_text = student_question_lookup.get(question["id"], question)
        else:
            question_for_text = question
        for line in question_for_text["text"].split("\n"):
            out(line)

        out("\nANSWER")

        if question.get("type") in ["multiple_choice", "select_all"]:
            selected_options = response.get(question["id"], [])
            if question.get("type") == "multiple_choice" and not isinstance(
                selected_options, list
            ):
                selected_options = [selected_options]
            available_options = sorted(
                [(i, option["text"]) for i, option in enumerate(question["options"])]
            )
            if question["id"] not in student_question_lookup:
                student_options = sorted(
                    [
                        (option.get("index", i), option["text"])
                        for i, option in enumerate(question["options"])
                    ]
                )
            else:
                student_options = sorted(
                    [
                        (option.get("index", i), option["text"])
                        for i, option in enumerate(
                            student_question_lookup[question["id"]]["options"]
                        )
                    ]
                )

            available_options = [
                (*available_option, option)
                for available_option, (j, option) in zip(
                    available_options, student_options
                )
            ]

            available_options.sort(key=lambda x: x[1])

            for i, template, option in available_options:
                if option in selected_options:
                    template = template
                    out("[X] " + template)
                else:
                    out("[ ] " + template)
        else:
            for line in response.get(question["id"], "").split("\n"):
                out(line)

        out("\nAUTOGRADER")
        if question["id"] in student_question_lookup and question["id"] in response:
            out(
                grade(
                    email, student_question_lookup[question["id"]], response, dispatch
                )
            )
        elif question["id"] not in student_question_lookup:
            out("STUDENT DID NOT RECEIVE QUESTION")
        else:
            out("")

    return pdf


def export(
    template_questions,
    student_responses,
    total,
    exam,
    out,
    name_question,
    sid_question,
    dispatch=None,
    include_outline=True,
    substitute_in_question_text=False,
):
    out = out or "out/export/" + exam
    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    if include_outline:
        pdf = write_exam(
            None,
            {},
            exam,
            template_questions,
            template_questions,
            name_question,
            sid_question,
            dispatch,
        )
        pdf.output(os.path.join(out, "OUTLINE.pdf"))

    for email, data in tqdm(
        student_responses.items(), desc="Exporting", unit="Exam", dynamic_ncols=True
    ):
        pdf = write_exam(
            email,
            data.get("responses"),
            exam,
            template_questions,
            data.get("student_questions"),
            name_question,
            sid_question,
            dispatch,
            substitute_in_question_text=substitute_in_question_text,
        )
        pdf.output(os.path.join(out, "{}.pdf".format(email)))

    with open(os.path.join(out, "summary.csv"), "w") as f:
        writer = csv.writer(f)
        for row in total:
            writer.writerow(row)


def download(exam, emails_to_download: [str] = None, debug: bool = False):
    exam_json = get_exam(exam=exam)
    exam_json.pop("secret")
    exam_json = json.dumps(exam_json)

    template_questions = list(extract_questions(json.loads(exam_json)))

    total = [
        ["Email"]
        + [question["text"] for question in extract_questions(json.loads(exam_json))]
    ]

    email_to_data_map = {}

    if emails_to_download is None:
        roster = get_roster(exam=exam)
        emails_to_download = [email for email, _ in roster]

    i = 1
    for email, response in tqdm(
        get_submissions(exam=exam), dynamic_ncols=True, desc="Downloading", unit="Exam"
    ):
        i += 1
        if emails_to_download is not None and email not in emails_to_download:
            continue

        if debug and 1 < len(response) < 10:
            tqdm.write(email, response)

        total.append([email])
        for question in template_questions:
            total[-1].append(response.get(question["id"], ""))

        student_questions = list(
            extract_questions(scramble(email, json.loads(exam_json), keep_data=True))
        )

        email_to_data_map[email] = {
            "student_questions": student_questions,
            "responses": response,
        }

    return json.loads(exam_json), template_questions, email_to_data_map, total
