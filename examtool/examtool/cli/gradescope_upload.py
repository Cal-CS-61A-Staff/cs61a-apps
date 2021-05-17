"""
Developed by Data 8 course staff - all credit goes to them!
"""
import os

import click
import requests
import tqdm

from examtool.cli.utils import exam_name_option, hidden_target_folder_option
from examtool.api.gradescope_upload import APIClient


@click.command()
@click.option("--course", prompt=True, help="The Gradescope course ID.")
@click.option("--assignment", prompt=True, help="The Gradescope assignment ID.")
@click.option("--email", prompt=True, help="Your Gradescope email address.")
@click.option(
    "--password", prompt=True, hide_input=True, help="Your Gradescope account password."
)
@click.option(
    "--keep-grades/--overwrite-grades",
    help="Whether reuploaded PDFs should keep the student's existing grades, or reset them.",
    default=False,
)
@exam_name_option
@hidden_target_folder_option
def gradescope_upload(course, assignment, email, password, exam, target, keep_grades):
    """
    Upload exported exam PDFs to Gradescope.
    Gradescope assignment URLs look like

    ```
    https://www.gradescope.com/courses/<COURSE>/assignments/<ASSIGNMENT>/grade
    ```

    <COURSE> and <ASSIGNMENT> are the relevant numbers to be passed in. Your email and password
    will not be stored on the server after this command completes. Specify `target` only if you have
    downloaded your PDFs to somewhere other than the default.

    You can upload multiple exams to the same assignment as long as they have the same underlying JSON
    (i.e. alternate exams).
    """
    target = target or "out/export/" + exam

    client = APIClient()
    client.log_in(email, password)

    for file_name in tqdm.tqdm(os.listdir(target)):
        if "@" not in file_name:
            continue
        student_email = file_name[:-4]
        # print("Uploading:", file_name)
        client.upload_submission(
            course,
            assignment,
            student_email,
            os.path.join(target, file_name),
            replace=keep_grades,
        )


if __name__ == "__main__":
    gradescope_upload()
