from html import escape

import pdfkit as pdfkit

from examtool.api.assemble_export import AssembledExam, OptionQuestion, TextQuestion


def render_html_exam(assembled_exam: AssembledExam):
    blocks = []

    def out(text):
        blocks.append(text)

    def user_out(text):
        out(escape(text))

    for question in assembled_exam.questions:
        out("<h3>Question</h3>")
        out(question.question.html)
        out("<h2>Answer</h2>")

        if isinstance(question, OptionQuestion):
            for option in question.options:
                checked = "checked" * (option in question.selected)
                out(
                    f"""
                    <div>
                        <label>
                        <input type="checkbox" {checked}></input>
                        {option.html}
                        </html>
                    </div>
                """
                )
        elif isinstance(question, TextQuestion):
            out("<code>")
            user_out(question.response)
            out("</code>")
        else:
            assert False, f"Unknown question type {type(question)}"

        out("<h2>Autograder</h2>")
        out("<code>")
        user_out(question.autograde_output)
        out("</code>")

    def export(target):
        pdfkit.from_string("".join(blocks), target, options={"log-level": "none"})

    return export
