import webbrowser

import click

from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--email", help="The email address of the student to impersonate.", prompt=True
)
def loginas(exam, email):
    """
    Login to examtool as a student.
    """
    webbrowser.open(f"https://exam.cs61a.org/{exam}#loginas={email}")


if __name__ == "__main__":
    loginas()
