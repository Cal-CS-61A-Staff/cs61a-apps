def make_row(content, target, action="Remove"):
    return f"""<form style="display: inline" action="{target}" method="post">
            {content}
            <input type="submit" value="{action}">
    </form>"""
