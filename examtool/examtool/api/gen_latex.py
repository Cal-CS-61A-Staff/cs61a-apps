import os
import sys
import subprocess
import re
import subprocess
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from examtool.api.scramble import latex_escape
from examtool.api.watermarks import create_watermark
from examtool.api.utils import rel_open


def generate(exam, *, include_watermark):
    out = []

    def write(x, *, newline=True):
        out.append(x)
        if newline:
            out.append("\n")

    def write_group(group, is_public):
        if is_public:
            if group["points"] is not None:
                write(rf"{{\bf\item ({group['points']} points)\quad}}")
            else:
                write(r"\item[]", newline=False)
        else:
            if group["points"] is not None:
                write(fr"\q{{{group['points']}}}")
            else:
                write(r"\item", newline=False)
        write(r"{ \bf " + latex_escape(group["name"]) + "}")
        write("\n")
        write(group["tex"])
        write(r"\begin{enumerate}[font=\bfseries]")
        for element in group["elements"]:
            if element["type"] == "group":
                write_group(element, False)
            else:
                write_question(element)
        write(r"\end{enumerate}")
        write(r"\clearpage")

    def write_question(question):
        write(r"\filbreak")
        if question["points"] is not None:
            write(fr"\subq{{{question['points']}}}")
        else:
            write(r"\item \, \hspace{-1em} \, ")
        write(question["tex"])
        solution = question.get("solution", defaultdict())
        if solution.get("solution"):
            write(r"\setlength{\fboxsep}{1em}")
            if "verbatim" in solution["solution"]["tex"]:
                write(
                    r"\catcode`_ 12\relax\n\begin{Verbatim}[frame=single,formatcom=\color{blue},rulecolor=\color{black},xleftmargin=1em,xrightmargin=1em]\n"
                )
                write(
                    solution["solution"]["tex"]
                    .replace("\\begin{verbatim}", "")
                    .replace("\\end{verbatim}", "")
                    .strip()
                )
                write(r"\end{Verbatim}\n\catcode`_ 8\relax")
            else:
                write(r"\fbox{\parbox{0.8\textwidth}{\solution{")
                write(solution["solution"]["tex"])
                write(r"}}}")
        elif question["type"] in ["short_answer", "short_code_answer"]:
            write(r"\framebox[0.8\textwidth][c]{\parbox[c][30px]{0.5\textwidth}{}}")
        elif question["type"] in ["long_answer", "long_code_answer"]:
            write(
                rf"\framebox[0.8\textwidth][c]{{\parbox[c][{30 * (question['options'])}px]{{0.5\textwidth}}{{}}}}"
            )

        correct = solution.get("options", [])

        if question["type"] in ["select_all"]:
            write(r"\begin{options}")
            for option in question["options"]:
                if option["text"] in correct:
                    write(r"\option[\moqs] " + option["tex"])
                else:
                    write(r"\option[\moqb] " + option["tex"])
            write(r"\end{options}")
        if question["type"] in ["multiple_choice"]:
            write(r"\begin{choices}")
            for option in question["options"]:
                if option["text"] in correct:
                    write(r"\option[\mcqs] " + option["tex"])
                else:
                    write(r"\option[\mcqb] " + option["tex"])
            write(r"\end{choices}")
        if solution.get("note"):
            write(r"\\\\ \note{")
            write(solution["note"]["tex"])
            write(r"}")
        write(r"\vspace{10px}")

    if include_watermark:
        write(r"\let\Watermarks=1")

    with rel_open("tex/prefix.tex") as f:
        write(f.read())
    for i, group in enumerate(
        ([exam["public"]] if exam["public"] else []) + exam["groups"]
    ):
        is_public = bool(i == 0 and exam["public"])
        write_group(group, is_public)

    with rel_open("tex/suffix.tex") as f:
        write(f.read())

    return "".join(out)


@contextmanager
def render_latex(
    exam,
    subs=None,
    *,
    do_twice=False,
    path="temp",
    outname="out",
    suppress_output=False,
    return_out_path=False,
):
    include_watermark = exam.get("watermark") and "value" in exam["watermark"]
    watermark_name = outname + "_watermark"
    watermark_svg = watermark_name + ".svg"
    watermark_pdf = watermark_name + ".pdf"

    latex = generate(exam, include_watermark=include_watermark)
    latex = re.sub(
        r"\\includegraphics(\[.*\])?{(http.*/(.+))}",
        r"\\immediate\\write18{wget -N \2}\n\\includegraphics\1{\3}",
        latex,
    )
    if subs:
        for k, v in subs.items():
            latex = latex.replace(f"<{k.upper()}>", v)
    if include_watermark:
        latex = latex.replace("EXAMTOOL_WATERMARK_PDF_PATH", watermark_pdf)
    if not os.path.exists(path):
        Path(path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(path, outname + ".tex"), "w+") as f:
        f.write(latex)

    if include_watermark:
        with open(os.path.join(path, watermark_svg), "w+") as f:
            f.write(
                create_watermark(
                    exam["watermark"]["value"],
                    brightness=exam["watermark"]["brightness"],
                )
            )
        subprocess.run(
            [
                "inkscape",
                "-D",
                "-z", 
                f"--file={watermark_svg}",
                f"--export-pdf={watermark_pdf}",
            ],
            stdout=subprocess.DEVNULL if suppress_output else sys.stdout,
            stderr=subprocess.DEVNULL if suppress_output else sys.stderr,
            cwd=path,
        )

    def compile():
        subprocess.run(
            [
                "pdflatex",
                "--shell-escape",
                "-interaction=nonstopmode",
                f"{outname}.tex",
            ],
            stdout=subprocess.DEVNULL if suppress_output else sys.stdout,
            stderr=subprocess.DEVNULL if suppress_output else sys.stderr,
            cwd=path,
        )

    compile()
    if do_twice:
        compile()

    out_path = os.path.join(path, outname + ".pdf")
    if return_out_path:
        yield out_path
    else:
        with open(out_path, "rb") as f:
            # os.chdir(old)
            yield f.read()
