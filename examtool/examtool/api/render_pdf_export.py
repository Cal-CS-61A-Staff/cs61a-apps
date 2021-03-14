from fpdf import FPDF

from examtool.api.assemble_export import AssembledExam, OptionQuestion, TextQuestion


def render_pdf_exam(assembled_exam: AssembledExam):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Courier", size=16)
    pdf.multi_cell(200, 20, txt=assembled_exam.exam, align="L")
    pdf.multi_cell(
        200,
        20,
        txt=assembled_exam.name.encode("latin-1", "replace").decode("latin-1"),
        align="L",
    )
    pdf.multi_cell(
        200,
        20,
        txt=assembled_exam.sid.encode("latin-1", "replace").decode("latin-1"),
        align="L",
    )

    pdf.set_font("Courier", size=9)

    def out(text):
        pdf.multi_cell(
            200,
            5,
            txt=text.encode("latin-1", "replace").decode("latin-1"),
            align="L",
        )

    for question in assembled_exam.questions:
        pdf.add_page()
        out("\nQUESTION")
        for line in question.prompt.text.split("\n"):
            out(line)

        out("\nANSWER")

        if isinstance(question, OptionQuestion):
            for option in question.options:
                if option in question.selected:
                    out("[X] " + option.text)
                else:
                    out("[ ] " + option.text)
        elif isinstance(question, TextQuestion):
            for line in question.response.split("\n"):
                out(line)
        else:
            assert False, f"Unknown question type {type(question)}"

        out("\nAUTOGRADER")
        out(question.autograde_output)

    return pdf
