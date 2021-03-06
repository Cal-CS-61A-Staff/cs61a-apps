import os
import pathlib
from io import BytesIO
from json import dump, load

import click
from pikepdf import Pdf

from examtool.api.convert import convert, load_imports
from examtool.api.database import get_exam
from examtool.api.gen_latex import render_latex
from examtool.api.scramble import scramble
from examtool.api.utils import sanitize_email
from examtool.cli.utils import (
    determine_semester,
    exam_name_option,
    hidden_output_folder_option,
    prettify,
)


@click.command()
@exam_name_option
@click.option(
    "--json",
    default=None,
    type=click.File("r"),
    help="The exam JSON you wish to compile. Leave blank to compile the deployed exam.",
)
@click.option(
    "--md",
    default=None,
    type=click.File("r"),
    help="The exam Markdown you wish to compile. Leave blank to compile the deployed exam.",
)
@click.option(
    "--seed",
    default=None,
    help="Scrambles the exam based off of the seed (E.g. a student's email).",
)
@click.option("--subtitle", prompt=False, default="Sample Exam.")
@click.option(
    "--with-solutions/--without-solutions",
    default=True,
    help="Generates the exam with (default) or without solutions.",
)
@click.option(
    "--exam-type",
    default="Final Exam",
    help="The type of exam you are given. For example 'Final Exam' (default).",
)
@click.option(
    "--semester",
    default=determine_semester(),
    help=f"The semester of the exam. '{determine_semester()}' (default).",
)
@click.option(
    "--json-out",
    default=None,
    type=click.File("w"),
    help="Exports the JSON to the file specified.",
)
@click.option(
    "--merged-md",
    default=None,
    type=click.File("w"),
    help="Merges any imports into a single file.",
)
@click.option(
    "--draft/--normal",
    default=False,
    help="Generates a draft copy of the exam, which is faster but less accurate.",
)
@click.option(
    "--num-threads",
    default=16,
    type=int,
    help="The number of threads to process the JSON file.",
)
@click.option(
    "--require-explicit-ids",
    default=False,
    is_flag=True,
    help="Raises an error if an ID is not specified by a question in its config.",
)
@hidden_output_folder_option
def compile(
    exam,
    json,
    md,
    seed,
    subtitle,
    with_solutions,
    exam_type,
    semester,
    json_out,
    merged_md,
    draft,
    num_threads,
    require_explicit_ids,
    out,
):
    """
    Compile one PDF or JSON (from Markdown), unencrypted.
    The exam may be deployed or local (in Markdown or JSON).
    If a seed is specified, it will scramble the exam.
    """
    if not out:
        out = ""

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    if json:
        print("Loading exam...")
        exam_data = load(json)
    elif md:
        src = md.read()
        path = md.name
        if merged_md:
            buff = load_imports(src, path)
            merged_md.write("\n".join(buff.lines))
            return
        print("Compiling exam...")
        try:
            exam_data = convert(
                src,
                path=path,
                draft=draft,
                num_threads=num_threads,
                allow_random_ids=not require_explicit_ids,
            )
        except SyntaxError as e:
            print("SyntaxError:", e)
            print("Could not compile your exam!")
            return
    else:
        print("Fetching exam...")
        exam_data = get_exam(exam=exam)

    if seed:
        print("Scrambling exam...")
        exam_data = scramble(seed, exam_data, keep_data=with_solutions)

    def remove_solutions_from_groups(groups):
        for group in groups:
            # if isinstance(group, dict):
            group.pop("solution", None)
            if group.get("type") == "group":
                remove_solutions_from_groups(group.get("elements", []))

    if not seed and not with_solutions:
        print("Removing solutions...")
        groups = exam_data.get("groups", [])
        remove_solutions_from_groups(groups)

    if json_out:
        print("Dumping json...")
        dump(exam_data, json_out, indent=4, sort_keys=True)
        return

    print("Rendering exam...")
    settings = {
        "coursecode": prettify(exam.split("-")[0]),
        "description": subtitle,
        "examtype": exam_type,
        "semester": semester,
    }
    if seed:
        settings["emailaddress"] = sanitize_email(seed)
    with render_latex(
        exam_data,
        settings,
    ) as pdf:
        pdf = Pdf.open(BytesIO(pdf))
        pdf.save(os.path.join(out, exam + ".pdf"))
        pdf.close()


if __name__ == "__main__":
    compile()
