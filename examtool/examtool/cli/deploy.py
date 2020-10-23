import csv
from json import dumps, loads

import click
from cryptography.fernet import Fernet

from examtool.api.convert import rand_id
from examtool.api.database import process_ok_exam_upload, set_exam, get_exam, set_roster
from examtool.api.extract_questions import extract_questions
from examtool.api.scramble import is_compressible_group, scramble
from examtool.cli.utils import exam_name_option


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
    "--default-deadline",
    prompt=True,
    default=0,
    type=int,
    help="Specify if you want unregistered students to be able to take the exam, with this as the default deadline.",
)
def deploy(exam, json, roster, start_time, default_deadline):
    """
    Deploy an exam to the website. You must specify an exam JSON and associated roster CSV.
    You can deploy the JSON multiple times and the password will remain unchanged.
    """
    json = json.read()
    roster = csv.reader(roster, delimiter=",")

    exam_content = loads(json)

    exam_content["default_deadline"] = default_deadline
    exam_content["secret"] = Fernet.generate_key().decode("utf-8")

    try:
        exam_content["secret"] = get_exam(exam=exam)["secret"]
    except:
        pass

    set_exam(exam=exam, json=exam_content)

    next(roster)  # ditch headers
    roster = list(roster)
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
    json = dumps(exam_content)  # re-serialize with group IDs

    students = [
        {
            "email": email,
            "questions": [
                {
                    "start_time": start_time,
                    "end_time": int(deadline),
                    "student_question_name": get_name(element),
                    "canonical_question_name": elements[element["id"]],
                }
                for element in list(
                    extract_questions(scramble(email, loads(json)), include_groups=True)
                )
            ],
            "start_time": start_time,
            "end_time": int(deadline),
        }
        for email, deadline in roster
    ]

    print("Updating announcements roster with {} students...".format(len(students)))

    for i in range(0, len(students), 100):
        print(
            "Uploading from student #{} to #{}".format(i, min(i + 100, len(students)))
        )
        process_ok_exam_upload(
            exam=exam,
            data={
                "students": students[i : i + 100],
                "questions": [
                    {"canonical_question_name": name} for name in elements.values()
                ],
            },
            clear=i == 0,
        )

    print("Announcements deployed to https://announcements.cs61a.org")


def get_name(element):
    if "name" in element:
        return f"{element['index']} {element['name']}"
    else:
        return element["index"]


if __name__ == "__main__":
    deploy()
