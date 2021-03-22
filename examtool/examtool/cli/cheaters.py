import csv
import json
import os
from collections import defaultdict
from dataclasses import asdict

import click

from examtool.api.database import get_roster
from examtool.api.substitution_finder import find_unexpected_words
from examtool.cli.utils import exam_name_option, hidden_target_folder_option


@click.command()
@exam_name_option
@hidden_target_folder_option
@click.option(
    "--out",
    type=click.File("w"),
    default=None,
    help="Output a CSV containing the list of cheaters",
)
def cheaters(exam, target, out):
    """
    Identify potential instances of cheating.
    """
    if not target:
        target = "out/logs/" + exam
    logs = defaultdict(list)
    for email, deadline in get_roster(exam=exam):
        short_target = os.path.join(target, email)
        full_target = os.path.join(target, "full", email)
        if os.path.exists(short_target):
            with open(short_target) as f:
                logs[email].extend(json.load(f))
        if os.path.exists(full_target):
            with open(full_target) as f:
                data = json.load(f)
                for record in data:
                    if "snapshot" not in record:
                        print(email, record)
                    else:
                        logs[email].append(
                            {**record["snapshot"], "timestamp": record["timestamp"]}
                        )
                        logs[email].append(
                            {**record["history"], "timestamp": record["timestamp"]}
                        )
    logs = list(logs.items())
    suspects = find_unexpected_words(exam, logs)
    if out:
        if suspects:
            writer = csv.writer(out)
            keys = asdict(suspects[0])
            writer.writerow(list(keys))
            for suspect in suspects:
                writer.writerow(asdict(suspect).values())
                suspect.explain()
    else:
        for suspect in suspects:
            suspect.explain()
