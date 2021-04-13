from flask import current_app


def make_row(content, target, action="Remove"):
    """Create a form with value ``content`` that POSTs to ``target`` when the
    button labeled ``action`` is pressed.

    :param content: the body of the form
    :type content: str - HTML

    :param target: the URL to POST to
    :type target: str

    :param action: the label of the submit button
    :type action: str

    :return: a string representing the HTML form
    """
    return f"""<form style="display: inline" action="{target}" method="post">
            {content}
            <input type="submit" value="{action}">
    </form>"""


def html(out):
    """Adds some styling to the HTML body ``out``.

    Specifically, adds a header of the form "61A App Name" and prepends
    the SPCSS stylesheet (https://cdn.jsdelivr.net/npm/spcss@0.5.0).

    :param out: the original HTML
    :type out: str

    :return: a string representing the stylized HTML.
    """
    if "<h1>" not in out:
        if hasattr(current_app, "remote"):
            header = current_app.remote.consumer_key
            if header.startswith("61a-"):
                header = header[3:]
            header = header.replace("-", " ").title()
            out = f"<h1>61A {header}</h1>" + out
    return f"""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/spcss@0.5.0">
{out}
"""


def error(out):
    """Formats a page representing an error.

    Specifically, preformats the error message and adds a red header, with
    some instructions on who to contact for help.

    :param out: the error message
    :type out: str

    :return: a string representing the stylized HTML.
    """
    report = f"<pre>{out}</pre>" if out else ""
    return html(
        f"<h2 style='color: red'>Something went wrong.</h2>{report} "
        f'If you are on 61A staff, visit <a href="https://logs.cs61a.org">logs.cs61a.org</a> '
        f"to see crash logs. Otherwise, please post in the EECS Crossroads Slack for help."
    )
