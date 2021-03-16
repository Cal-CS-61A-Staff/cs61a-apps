"""
Developed by ThaumicMekanism [Stephan K.] - all credit goes to him!
"""
import os
import json

import click

from examtool.cli.utils import hidden_target_folder_option
from examtool.api.gradescope_autograde import GradescopeGrader


@click.command()
@click.option(
    "--exam",
    default="cs61a-test-final",
    prompt=True,
    help="The list of exam names. If it is just one exam, just include one. Separate exams with commas: Eg 'cs61a-final-8am,cs61c-final-10am`",
)
@click.option(
    "--name-question",
    default=None,
    prompt=True,
    help="The ID of the question for the student's name.",
)
@click.option(
    "--sid-question",
    default=None,
    prompt=True,
    help="The ID of the question for the student's SID.",
)
@click.option("--course", prompt=True, help="The Gradescope course ID.")
@click.option(
    "--assignment",
    default=None,
    help="The Gradescope assignment ID. If this is left blank, this tool will create the Gradescope assignment.",
)
@click.option(
    "--assignment-title",
    default="Examtool Exam",
    help="The title you want the Gradescope assignment to have.",
)
@click.option("--email", help="Your Gradescope email address.")
@click.option("--password", hide_input=True, help="Your Gradescope account password.")
@click.option(
    "--token",
    "-t",
    default=None,
    help="The path to the token file holding your Gradescope credentials.",
    type=click.Path(),
)
@click.option(
    "--emails",
    default=None,
    help="This is a list of emails you want to autograde to the assignment. Separate emails with a comma. If left blank, it will include all emails from the exams. Selection occurres before mutation.",
)
@click.option(
    "--blacklist-emails",
    default=None,
    help="This is a list of emails you want the autograder to skip. Separate emails with a comma. If left blank, it will not blacklist any email. Blacklist occurres before mutation.",
)
@click.option(
    "--mutate-emails",
    default=None,
    help="This is a json dictionary which maps the email on examtool to the default email on gradescope ({str:str}). It will not mutate emails which are not in the list. If this is left blank, it will not mutate any emails.",
)
@click.option(
    "--question-numbers",
    default=None,
    help="This is a list of question numbers you want to autograde to the assignment (Numbers are defined by the Gradescope question number). Separate question numbers with a comma. If left blank, it will grade all questions from the exams.",
)
@click.option(
    "--blacklist-question-numbers",
    default=None,
    help="This is a list of question numbers you want the autograder to skip (Numbers are defined by the Gradescope question number). Separate question numbers with a comma. If left blank, it will not blacklist any questions.",
)
@click.option(
    "--create/--update",
    default=True,
    help="Create will generate the outline and set the grouping type, update will ",
)
@click.option(
    "--custom-grouper",
    default=None,
    help="This is the path to a python file which contains the dictionary named EXACTLY `examtool_custom_grouper_fns` mapping question IDs or question Gradescope numbers to a function which returns a QuestionGrouper type. See examtool.api.gradescope_autograde for details about that function.",
)
@click.option(
    "--jobs",
    "-j",
    default=10,
    type=int,
    help="This is the number of simultaneous questions currently being processed. Default: 10",
)
@click.option(
    "--sub-jobs",
    "-sj",
    default=10,
    type=int,
    help="This is the number of simultaneous jobs of a question currently being processed. Note this is per question. Default: 10",
)
@hidden_target_folder_option
def gradescope_autograde(
    exam,
    name_question,
    sid_question,
    course,
    assignment,
    assignment_title,
    email,
    password,
    token,
    emails,
    blacklist_emails,
    mutate_emails,
    question_numbers,
    blacklist_question_numbers,
    create,
    custom_grouper,
    jobs,
    sub_jobs,
    target,
):
    """
    Uploads and autogrades the given exam(s).
    """
    exam = [e.strip() for e in exam.split(",")]
    target = target or "out/export/" + exam[0]

    grouper_map = None
    if custom_grouper:
        if os.path.exists(custom_grouper):
            import importlib.util

            spec = importlib.util.spec_from_file_location("module.name", custom_grouper)
            cg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cg)
            grouper_map = cg.examtool_custom_grouper_fns

    grader = GradescopeGrader(
        email=email,
        password=password,
        gs_login_tokens_path=token,
        simultaneous_jobs=jobs,
        simultaneous_sub_jobs=sub_jobs,
    )

    email_mutation_list = None
    if mutate_emails:
        with open(mutate_emails, "r") as f:
            email_mutation_list = json.load(f)

    def extract_list(s):
        return [i.strip() for i in s.split(",")]

    if emails is not None:
        emails = extract_list(emails)
    if blacklist_emails is not None:
        blacklist_emails = extract_list(blacklist_emails)
    if question_numbers is not None:
        question_numbers = extract_list(question_numbers)
    if blacklist_question_numbers is not None:
        blacklist_question_numbers = extract_list(blacklist_question_numbers)
    if create or assignment is None:
        grader.main(
            exam,
            target,
            name_question,
            sid_question,
            course,
            gs_assignment_id=assignment,
            gs_assignment_title=assignment_title,
            emails=emails,
            blacklist_emails=blacklist_emails,
            email_mutation_list=email_mutation_list,
            question_numbers=question_numbers,
            blacklist_question_numbers=blacklist_question_numbers,
            custom_grouper_map=grouper_map,
        )
    else:
        grader.add_additional_exams(
            exam,
            target,
            name_question,
            sid_question,
            course,
            assignment,
            emails=emails,
            blacklist_emails=blacklist_emails,
            email_mutation_list=email_mutation_list,
            question_numbers=question_numbers,
            blacklist_question_numbers=blacklist_question_numbers,
            custom_grouper_map=grouper_map,
        )


if __name__ == "__main__":
    gradescope_autograde()
