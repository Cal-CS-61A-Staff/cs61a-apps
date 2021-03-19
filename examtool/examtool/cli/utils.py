import re

import click

from datetime import date, datetime
from collections import OrderedDict

exam_name_option = click.option(
    "--exam", prompt=True, default="cs61a-test-final", help="The exam name."
)
hidden_output_folder_option = click.option(
    "--out",
    default=None,
    help="Output folder. Leave as default for dependent commands to work.",
    type=click.Path(),
)
hidden_target_folder_option = click.option(
    "--target",
    default=None,
    help="Target folder for PDFs. Leave as default unless the source output folder is not the default.",
    type=click.Path(),
)


def verify_roster(*, roster):
    for i, row in enumerate(roster):
        j = len(row)
        if j != 2 and j != 3:
            print(
                f"ValueError: The roster must contain 2 or 3 columns: Email, Timestamp, Skip Watermarks [Optional]. "
                f"Found {j} item(s) on row {i + 1}: {row}"
            )
            return False
    return True


def prettify(course_code):
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course_code)
    return m and (m.group(1) + " " + m.group(2)).upper()


def determine_semester():
    sem_map = OrderedDict()
    sem_map["1/1"] = "Spring"
    sem_map["6/1"] = "Summer"
    sem_map["9/1"] = "Fall"
    today = date.today()

    def compare_date(DATE_TO_COMPARE):
        parsed = (
            datetime.strptime(DATE_TO_COMPARE, "%m/%d").date().replace(year=today.year)
        )
        return parsed > today

    sem = next(iter(sem_map))
    for DATE_TO_COMPARE, new_sem in sem_map.items():
        if compare_date(DATE_TO_COMPARE):
            break
        sem = new_sem
    return f"{sem} {today.year}"
