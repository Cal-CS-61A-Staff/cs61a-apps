import click

from examtool.api.database import get_exam
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import scramble
from examtool.api.substitutions import get_all_substitutions
from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option("--email", help="The target student's email address.")
@click.option(
    "--show-all",
    default=False,
    is_flag=True,
    help="Show all questions received, not just with substitutions.",
)
def substitutions(exam, email, show_all):
    """
    Show the substitutions a particular student received
    """
    original_exam = get_exam(exam=exam)
    exam = get_exam(exam=exam)
    exam = scramble(email, exam, keep_data=True)
    question_substitutions = get_all_substitutions(original_exam, exam)
    questions = extract_questions(exam)
    for question in questions:
        substitutions = question_substitutions[question["id"]]
        if substitutions or show_all:
            print(get_name(question), substitutions)
