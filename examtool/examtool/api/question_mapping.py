import os
import tempfile
import multiprocessing
import collections

from tqdm import tqdm
from math import floor, ceil

from pdfminer.layout import LAParams, LTTextBox, LTPage
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

from examtool.api.assemble_export import AssembledExam
from examtool.api.render_html_export import render_html_exam

from PyPDF2 import PdfFileReader


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
