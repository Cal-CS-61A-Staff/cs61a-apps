from flask import current_app


def make_row(content, target, action="Remove"):
    return f"""<form style="display: inline" action="{target}" method="post">
            {content}
            <input type="submit" value="{action}">
    </form>"""


def html(out):
    # trivial changes to make things look less ugly
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
    report = f"<pre>{out}</pre>" if out else ""
    return html(
        f"<h2 style='color: red'>Something went wrong.</h2>{report} "
        f'If you are on 61A staff, visit <a href="https://logs.cs61a.org">logs.cs61a.org</a> '
        f"to see crash logs. Otherwise, please post in the EECS Crossroads Slack for help."
    )
