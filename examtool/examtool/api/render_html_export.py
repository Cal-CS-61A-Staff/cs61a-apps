from contextlib import contextmanager
from html import escape

import pdfkit

from examtool.api.assemble_export import AssembledExam, OptionQuestion, TextQuestion
from examtool.api.utils import rel_path


def render_html_exam(assembled_exam: AssembledExam):
    blocks = []

    def out(text):
        blocks.append(text.replace("“", '"').replace("”", '"').replace("’", "'"))

    def user_out(text):
        out(escape(text))

    def tag(name):
        @contextmanager
        def with_tag(**attrs):
            out(f"<{name}")
            for k, v in attrs.items():
                if k == "className":
                    k = "class"
                if not v:
                    continue

                out(" ")
                out(k)
                out("=")
                out(repr(str(v)))
            out(">")
            yield
            out(f"</{name}>")

        return with_tag

    h3 = tag("h3")

    div = tag("div")
    label = tag("label")
    input = tag("input")
    pre = tag("pre")

    for question in assembled_exam.questions:
        with div(className="question"):
            with h3():
                out(question.name)

            with div(className="questionText"):
                out(question.prompt.html)

            with div(className="gradable"):
                with div(className="answer"):
                    if isinstance(question, OptionQuestion):
                        for option in question.options:
                            with div(className="checkbox"), label(), input(
                                type="checkbox", checked=option in question.selected
                            ):
                                out(option.html)

                    elif isinstance(question, TextQuestion):
                        with div(className="response"):
                            with pre(style=f"height: {question.height * 3}em"):
                                user_out(question.response)
                    else:
                        assert False, f"Unknown question type {type(question)}"

                with pre(className="autogradeOutput"):
                    user_out(question.autograde_output)

    def export(target):
        pdfkit.from_string(
            "".join(blocks),
            target,
            options={
                "log-level": "none",
                "disable-smart-shrinking": None,
                "zoom": 0.75,
            },
            css=rel_path("css/style.css"),
        )

    return export
