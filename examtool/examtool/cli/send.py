import base64
import os

import click

from examtool.api.database import get_roster
from examtool.api.email import send_email_local, get_api_key
from examtool.cli.utils import hidden_target_folder_option, exam_name_option, prettify


@click.command()
@exam_name_option
@hidden_target_folder_option
@click.option("--email", help="The email address of a particular student.")
@click.option(
    "--subject",
    default="{course} Exam PDF",
    help="The email subject to use.",
    show_default=True,
)
@click.option(
    "--filename",
    default="Encrypted {course} Exam.pdf",
    help="The PDF filename to use.",
    show_default=True,
)
def send(exam, target, email, subject, filename):
    """
    Email an encrypted PDF to all students taking an exam. Specify `email` to email only a particular student.
    """
    if not target:
        target = "out/latex/" + exam

    course = prettify(exam.split("-")[0])

    filename = filename.format(course=course)
    subject = subject.format(course=course)
    body = (
        "Hello!\n\n"
        "You have an upcoming exam taking place on exam.cs61a.org. "
        "You should complete your exam on that website.\n\n"
        "Course: {course}\n"
        "Exam: {exam}\n\n"
        "However, if you encounter technical difficulties and are unable to do so, "
        "we have attached an encrypted PDF containing the same exam. "
        "You can then email your exam solutions to course staff before the deadline "
        "rather than submitting using exam.cs61a.org. "
        "To unlock the PDF, its password will be revealed on Piazza when the exam starts.\n\n"
        "Good luck, and remember to have fun!"
    ).format(course=course, exam=exam)

    roster = []
    if email:
        roster = [email]
    else:
        for email, deadline in get_roster(exam=exam):
            if deadline:
                roster.append(email)

    key = get_api_key(exam=exam)

    print(
        ("Subject: {subject}\n" "PDF filename: {filename}\n" "Body: {body}\n\n").format(
            body=body, filename=filename, subject=subject
        )
    )
    if (
        input(
            "Sending email to {} people - confirm? (y/N) ".format(len(roster))
        ).lower()
        != "y"
    ):
        exit(1)

    for email in roster:
        with open(
            os.path.join(
                target, "exam_" + email.replace("@", "_").replace(".", "_") + ".pdf"
            ),
            "rb",
        ) as f:
            pdf = base64.b64encode(f.read()).decode("ascii")
        data = {
            "from": {"email": "cs61a@berkeley.edu", "name": "CS 61A Exam Platform"},
            "personalizations": [{"to": [{"email": email}], "substitutions": {}}],
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
            "attachments": [
                {
                    "content": pdf,
                    "type": "application/pdf",
                    "filename": filename,
                    "disposition": "attachment",
                }
            ],
        }

        send_email_local(key, data)


if __name__ == "__main__":
    send()
