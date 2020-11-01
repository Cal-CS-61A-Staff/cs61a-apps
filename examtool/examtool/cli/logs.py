import csv
from datetime import datetime

import click
import pytz

from examtool.api.database import get_logs
from examtool.cli.utils import exam_name_option


def time(timestamp):
    return (
        datetime.utcfromtimestamp(timestamp)
        .replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("America/Los_Angeles"))
    )


@click.command()
@click.option("--email", default=None, help="A student's target email address.")
@click.option("--roster", default=None, type=click.File("r"), help="A roster CSV.")
@exam_name_option
def logs(email, exam, roster):
    """
    Export the submission history.
    Specify `email` to target a particular student,
    or specify `roster` to target all students listed in a particular roster CSV.
    """
    if roster:
        roster = csv.reader(roster, delimiter=",")
        next(roster)
        emails = [x[0] for x in roster if x[1]]
    else:
        emails = [email]

    all_students = []

    for email in emails:
        print(email)
        times = []
        for record in get_logs(exam=exam, email=email):
            ref = time(record.pop("timestamp"))
            times.append([ref, next(iter(record.keys())), next(iter(record.values()))])
        print(
            "\n".join(str(x) + " " + str(y) + " " + str(z) for x, y, z in sorted(times))
        )

    all_students.sort(key=lambda x: x[0])

    print("\n".join(str(x) + " " + str(y) for x, y in all_students))


if __name__ == "__main__":
    logs()
