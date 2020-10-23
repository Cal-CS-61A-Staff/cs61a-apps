import os
import re
from collections import defaultdict
from contextlib import contextmanager


def rel_open(path, *args, **kwargs):
    root = os.path.dirname(os.path.abspath(__file__))
    return open(os.path.join(root, path), *args, **kwargs)


def generate(exam):
    out = []
    write = out.append

    def write_group(group, is_public):
        if is_public:
            if group["points"] is not None:
                write(rf"{{\bf\item ({group['points']} points)\quad}}")
            else:
                write(r"\item[]")
        else:
            if group["points"] is not None:
                write(fr"\q{{{group['points']}}}")
            else:
                write(r"\item")
        write(r"{ \bf " + group["name"] + "}")
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

    with rel_open("tex/prefix.tex") as f:
        write(f.read())
    for i, group in enumerate(
        ([exam["public"]] if exam["public"] else []) + exam["groups"]
    ):
        is_public = bool(i == 0 and exam["public"])
        write_group(group, is_public)

    with rel_open("tex/suffix.tex") as f:
        write(f.read())

    return "\n".join(out)


@contextmanager
def render_latex(exam, subs=None, *, do_twice=False):
    latex = generate(exam)
    latex = re.sub(
        r"\\includegraphics(\[.*\])?{(http.*/(.+))}",
        r"\\immediate\\write18{wget -N \2}\n\\includegraphics\1{\3}",
        latex,
    )
    if subs:
        for k, v in subs.items():
            latex = latex.replace(f"<{k.upper()}>", v)
    if not os.path.exists("temp"):
        os.mkdir("temp")
    with open("temp/out.tex", "w+") as f:
        f.write(latex)
    old = os.getcwd()
    os.system("cd temp && pdflatex --shell-escape -interaction=nonstopmode out.tex")
    if do_twice:
        os.system("cd temp && pdflatex --shell-escape -interaction=nonstopmode out.tex")
    with open("temp/out.pdf", "rb") as f:
        os.chdir(old)
        yield f.read()
    # shutil.rmtree("temp")
