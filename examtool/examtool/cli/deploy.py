import csv
from json import loads

import click
from cryptography.fernet import Fernet

from examtool.api.utils import rand_id
from examtool.api.database import process_ok_exam_upload, set_exam, get_exam, set_roster
from examtool.api.extract_questions import extract_questions, get_name
from examtool.api.scramble import is_compressible_group
from examtool.cli.utils import exam_name_option, verify_roster


@click.command()
@exam_name_option
@click.option(
    "--json",
    prompt=True,
    type=click.File("r"),
    help="The exam JSON you wish to deploy.",
)
@click.option(
    "--roster",
    prompt=True,
    type=click.File("r"),
    help="The roster CSV you wish to deploy.",
)
@click.option(
    "--start-time",
    prompt=True,
    type=int,
    help="The unix timestamp corresponding to the start time of the exam.",
)
@click.option(
    "--enable-clarifications",
    prompt=True,
    default=True,
    type=bool,
    help="Let students send clarifications to staff from the exam itself.",
)
def deploy(exam, json, roster, start_time, enable_clarifications):
    """
    Deploy an exam to the website. You must specify an exam JSON and associated roster CSV.
    You can deploy the JSON multiple times and the password will remain unchanged.
    """
    json = json.read()
    roster = csv.reader(roster, delimiter=",")

    exam_content = loads(json)

    exam_content["default_deadline"] = 0
    exam_content["secret"] = Fernet.generate_key().decode("utf-8")

    try:
        old_secret = get_exam(exam=exam)["secret"]
        if old_secret:
            print("Reusing old secret...")
            exam_content["secret"] = old_secret
    except Exception:
        pass

    set_exam(exam=exam, json=exam_content)
    roster = list(roster)
    if not verify_roster(roster=roster):
        exit(1)
    roster = roster[1:]  # ditch headers
    set_roster(exam=exam, roster=roster)

    print("Exam uploaded with password:", exam_content["secret"][:-1])

    print("Exam deployed to https://exam.cs61a.org/{}".format(exam))

    print("Initializing announcements...")
    elements = list(extract_questions(exam_content, include_groups=True))
    for element in elements:
        element["id"] = element.get("id", rand_id())  # add IDs to groups
    elements = {
        element["id"]: get_name(element)
        for element in elements
        if element["type"] != "group" or not is_compressible_group(element)
    }

    students = [
        {
            "email": email,
            "start_time": start_time,
            "end_time": int(deadline),
            "no_watermark": bool(int(rest[0]) if rest else False),
        }
        for email, deadline, *rest in roster
    ]

    print("Updating announcements roster with {} students...".format(len(students)))

    process_ok_exam_upload(
        exam=exam,
        data={
            "students": students,
            "questions": [
                {"canonical_question_name": name} for name in elements.values()
            ],
        },
        clear=True,
        enable_clarifications=enable_clarifications,
    )

    print("Announcements deployed to https://announcements.cs61a.org")


if __name__ == "__main__":
    deploy()
