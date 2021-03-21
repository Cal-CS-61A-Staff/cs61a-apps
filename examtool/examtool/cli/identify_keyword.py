import click

from examtool.api.substitution_finder import find_keyword
from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--keyword",
    prompt=True,
    help="The keyword you wish to identify.",
)
def identify_keyword(exam, keyword):
    """
    Identify the student from a keyword present in their exam.
    """
    find_keyword(exam, keyword)
