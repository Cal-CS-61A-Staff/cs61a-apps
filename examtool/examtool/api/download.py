import json

from tqdm import tqdm

from examtool.api.database import get_exam, get_roster, get_submissions
from examtool.api.extract_questions import extract_questions
from examtool.api.scramble import scramble

from examtool.api.assemble_export import AssembledExam
from examtool.api.render_html_export import render_html_exam

from PyPDF2 import PdfFileReader


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


def get_question_to_page_mapping(
    assembled_exam: AssembledExam
):
    orig_questions = assembled_exam.questions.copy()
    assembled_exam.questions = []
    pages = []
    temp_file = "temp/qtpm_temp.pdf"
    for q in tqdm(
        orig_questions,
        desc="Getting question page numbers",
        unit="Question",
        dynamic_ncols=True,
    ):
        assembled_exam.questions.append(q)
        export = render_html_exam(assembled_exam)
        export(temp_file)
        with open(temp_file, "rb") as pdf_file:
            pdf_reader = PdfFileReader(pdf_file)
            pages.append(pdf_reader.numPages)
    # for i, q in enumerate(assembled_exam.questions):
    #     print(f"[{i}] pg: {pages[i]} - {q['id']}")
    # import ipdb; ipdb.set_trace()
    return pages
