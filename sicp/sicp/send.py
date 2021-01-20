from base64 import b64encode
from os.path import basename
from typing import List

import click
from click import Path

from common.rpc.mail import send_email


@click.command()
@click.option(
    "--target",
    help="The destination email address e.g. cs61a@berkeley.edu",
    prompt=True,
)
@click.option("--subject", help="The subject line of the message", prompt=True)
@click.option("--body", help="The contents of the message", prompt=True)
@click.option(
    "--attachment",
    "attachments",
    type=Path(exists=True, dir_okay=False),
    multiple=True,
    help="Files to attach to the email",
)
def send(target: str, subject: str, body: str, attachments: List[str]):
    """
    Send emails from cs61a@berkeley.edu routed through a university mailserver.
    """
    loaded_attachments = {}

    for attachment in attachments:
        with open(attachment, "rb") as f:
            loaded_attachments[basename(attachment)] = b64encode(f.read()).decode(
                "ascii"
            )

    send_email(
        target=target, subject=subject, body=body, attachments=loaded_attachments
    )
