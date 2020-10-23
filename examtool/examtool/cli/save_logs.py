import json
import os
import pathlib

import click

from examtool.api.database import get_roster, get_logs
from examtool.cli.utils import exam_name_option, hidden_output_folder_option


@click.command()
@exam_name_option
@hidden_output_folder_option
def save_logs(exam, out):
    """
    Save the full submission log for later analysis.
    Note that this command is slow.
    To view a single log entry, run `examtool log`.
    """
    out = out or "out/logs/" + exam

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    roster = get_roster(exam=exam)
    for i, (email, deadline) in enumerate(roster):
        print(email)
        logs = get_logs(exam=exam, email=email)
        with open(os.path.join(out, email), "w") as f:
            json.dump(logs, f)
