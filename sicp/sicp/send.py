from base64 import b64encode
from os.path import basename
from typing import List

import click
from click import Path

from common.rpc.mail import send_email


@click.command()
@click.option(
    "--sender",
    default="CS 61A Mailtool",
    help="The sender display name",
)
@click.option(
    "--sender-user",
    default="cs61a",
    help="The sender username",
)
@click.option(
    "--sender-domain",
    default="berkeley.edu",
    help="The sender domain",
)
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
def send(
    sender: str,
    sender_user: str,
    sender_domain: str,
    target: str,
    subject: str,
    body: str,
    attachments: List[str],
):
    """
    Send emails from eecs.berkeley.edu routed through a university mailserver.
    """
    loaded_attachments = {}

    for attachment in attachments:
        with open(attachment, "rb") as f:
            loaded_attachments[basename(attachment)] = b64encode(f.read()).decode(
                "ascii"
            )

    assert sender_domain.endswith("berkeley.edu")

    send_email(
        sender=f"{sender} <{sender_user}@{sender_domain}>",
        target=target,
        subject=subject,
        body=body,
        attachments=loaded_attachments,
        _impersonate="mail",
    )
