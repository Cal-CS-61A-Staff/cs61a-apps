def make_row(content, target, action="Remove"):
    return f"""<p>
        <form style="display: inline" action="{target}" method="post">
            {content}
            <input type="submit" value="{action}">
        </form>
    </p>"""
