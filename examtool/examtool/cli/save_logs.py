import json
import os
import pathlib

import click

from examtool.api.database import get_full_logs, get_roster, get_logs
from examtool.cli.utils import exam_name_option, hidden_output_folder_option


@click.command()
@exam_name_option
@hidden_output_folder_option
@click.option(
    "--full", default=False, is_flag=True, help="Get keylogging logs too, if available."
)
@click.option(
    "--fetch_all",
    default=False,
    is_flag=True,
    help="Re-download all logs.",
)
def save_logs(exam, out, full, fetch_all):
    """
    Save the full submission log for later analysis.
    Note that this command is slow.
    To view a single log entry, run `examtool log`.
    """
    out = out or "out/logs/" + exam
    full_out = os.path.join(out, "full")

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)
    pathlib.Path(full_out).mkdir(parents=True, exist_ok=True)

    roster = get_roster(exam=exam)
    for i, (email, deadline) in enumerate(roster):
        print(email)
        try:
            target = os.path.join(out, email)
            if os.path.exists(target) and not fetch_all:
                print("Skipping", email)
            else:
                print("Fetching short logs for", email)
                logs = get_logs(exam=exam, email=email)
                with open(target, "w") as f:
                    json.dump(logs, f)
            if full:
                target = os.path.join(full_out, email)
                if os.path.exists(target) and not fetch_all:
                    print("Skipping", email, "for full logs")
                else:
                    print("Fetching full logs for", email)
                    logs = get_full_logs(exam=exam, email=email)
                    with open(os.path.join(full_out, email), "w") as f:
                        json.dump(logs, f)
        except KeyboardInterrupt:
            raise
        except:
            print("Failure for email", email, "continuing...")
