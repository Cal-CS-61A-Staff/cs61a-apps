import click

from examtool.cli.utils import exam_name_option, hidden_output_folder_option
import examtool.api.download


@click.command()
@exam_name_option
@click.option(
    "--name-question",
    default=None,
    help="The ID of the question for the student's name.",
)
@click.option(
    "--sid-question", default=None, help="The ID of the question for the student's SID."
)
@click.option(
    "--compact/--expanded",
    default=False,
    help="Combine questions on the same page to save space.",
)
@click.option(
    "--with-substitutions/--without-substitutions",
    default=False,
    help="Include keyword substitutions in exported question bodies.",
)
@hidden_output_folder_option
def download(exam, out, name_question, sid_question, compact, with_substitutions):
    """
    Download student submissions for an exam.
    Exams are downloaded as PDFs into a target folder - specify `out` to redirect the folder.
    An `OUTLINE.pdf` is also generated for Gradescope, as is a `summary.csv` for analytics or autograding.
    """
    (
        exam_json,
        template_questions,
        email_to_data_map,
        total,
    ) = examtool.api.download.download(exam)
    examtool.api.download.export(
        template_questions,
        email_to_data_map,
        total,
        exam,
        out,
        name_question,
        sid_question,
        compact,
        substitute_in_question_text=with_substitutions,
    )


if __name__ == "__main__":
    download()
