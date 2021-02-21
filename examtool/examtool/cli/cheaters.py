import json
import os
from collections import defaultdict

import click

from examtool.api.database import get_roster
from examtool.api.substitution_finder import find_unexpected_words
from examtool.cli.utils import exam_name_option, hidden_target_folder_option


@click.command()
@exam_name_option
@hidden_target_folder_option
def cheaters(exam, target):
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
                    logs[email].append(
                        {**record["snapshot"], "timestamp": record["timestamp"]}
                    )
                    logs[email].append(
                        {**record["history"], "timestamp": record["timestamp"]}
                    )
    logs = list(logs.items())
    find_unexpected_words(exam, logs)
