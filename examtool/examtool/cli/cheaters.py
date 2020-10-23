import json
import os

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
    logs = []
    for email, deadline in get_roster(exam=exam):
        with open(os.path.join(target, email)) as f:
            logs.append([email, json.load(f)])
    find_unexpected_words(exam, logs)
