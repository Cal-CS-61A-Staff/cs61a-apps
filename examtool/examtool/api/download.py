import os
import json
import collections
import tempfile
import multiprocessing

from tqdm import tqdm
from pathlib import Path
from multiprocessing import Pool
from math import floor, ceil

from pdfminer.layout import LAParams, LTTextBox, LTPage
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

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


def _get_question_to_page_mapping_renderer(data):
    filename = "qtpm_temp.pdf"
    question_num, assembled_exam, tmpdirname, pages_dict = data
    tmp_assembled_exam = AssembledExam(
        assembled_exam.exam,
        assembled_exam.email,
        assembled_exam.name,
        assembled_exam.sid,
        assembled_exam.questions[
            : question_num + 1
        ],  # +1 is meant to include the current question.
    )
    temp_file = os.path.join(
        tmpdirname, multiprocessing.current_process().name + "_" + filename
    )
    export = render_html_exam(tmp_assembled_exam)
    export(temp_file)
    with open(temp_file, "rb") as pdf_file:
        pdf_reader = PdfFileReader(pdf_file)
        pages_dict[question_num] = pdf_reader.numPages


def fallback_get_question_to_page_mapping(
    assembled_exam: AssembledExam,
    num_threads: int = 16,
):
    pages_dict = {}
    with tempfile.TemporaryDirectory() as tmpdirname:
        num_questions = len(assembled_exam.questions)
        with multiprocessing.Manager() as manager:
            managed_pages_dict = manager.dict()
            with manager.Pool(num_threads) as p:
                list(
                    tqdm(
                        p.imap_unordered(
                            _get_question_to_page_mapping_renderer,
                            [
                                (i, assembled_exam, tmpdirname, managed_pages_dict)
                                for i in range(num_questions)
                            ],
                        ),
                        total=num_questions,
                        desc="Getting question page numbers",
                        unit="Question",
                    )
                )
            pages_dict = dict(managed_pages_dict)

    pages = list(collections.OrderedDict(sorted(pages_dict.items())).values())

    # for q in tqdm(
    #     assembled_exam.questions,
    #     desc="Getting question page numbers",
    #     unit="Question",
    #     dynamic_ncols=True,
    # ):
    #     questions.append(q)
    #     tmp_assembled_exam = AssembledExam(
    #         assembled_exam.exam,
    #         assembled_exam.email,
    #         assembled_exam.name,
    #         assembled_exam.sid,
    #         questions
    #     )
    #     export = render_html_exam(tmp_assembled_exam)
    #     export(temp_file)
    #     with open(temp_file, "rb") as pdf_file:
    #         pdf_reader = PdfFileReader(pdf_file)
    #         pages.append(pdf_reader.numPages)
    # for i, q in enumerate(assembled_exam.questions):
    #     print(f"[{i}] pg: {pages[i]}") # - {q['id']}")
    # import ipdb; ipdb.set_trace()
    return pages


def get_question_to_page_mapping(
    assembled_exam: AssembledExam,
    num_threads: int = 16,
):
    filename = "qtpm_temp.pdf"
    tmp_assembled_exam = AssembledExam(
        assembled_exam.exam,
        assembled_exam.email,
        assembled_exam.name,
        assembled_exam.sid,
        assembled_exam.questions,
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_file = os.path.join(tmpdirname, filename)
        export = render_html_exam(tmp_assembled_exam)
        export(temp_file)
        with open(temp_file, "rb") as fp:
            pdf_reader = PdfFileReader(fp)
            num_pages = pdf_reader.numPages
        with open(temp_file, "rb") as fp:
            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            pages = PDFPage.get_pages(fp)

            y_coord_map = []

            for page in tqdm(
                pages, desc="Extracting questions", unit="Page", total=num_pages
            ):
                interpreter.process_page(page)
                layout = device.get_result()
                local_y_coord_map = []
                for lobj in layout:
                    if isinstance(lobj, LTTextBox):
                        text = lobj.get_text()
                        if text == "STUDENT LEFT QUESTION BLANK\n":
                            x0, y0_orig, x1, y1_orig = lobj.bbox
                            y0 = round(
                                ((page.mediabox[3] - y1_orig) / layout.y1) * 100, 1
                            )
                            y1 = round(
                                ((page.mediabox[3] - y0_orig) / layout.y1) * 100, 1
                            )
                            local_y_coord_map.append((layout.pageid, y0, y1))
                prev = None
                for i, coord in enumerate(local_y_coord_map):
                    page, y0, y1 = coord
                    if prev is None:
                        y0 = 4
                    else:
                        y0 = ceil(prev[2]) + 1
                        # if i == len(local_y_coord_map) - 1:
                        #     y1 = 96
                    prev = coord
                    y_coord_map.append((page, y0, ceil(y1)))
    return y_coord_map
