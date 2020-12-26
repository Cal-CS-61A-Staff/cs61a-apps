def check_auth(app):
    data = get_user_data(app)
    for participation in data["participations"]:
        if participation["course"]["offering"].startswith(
            "cal/cs61a"
        ) and participation["role"] in ["staff", "instructor", "grader"]:
            return True
    return False


def get_user_data(app):
    ret = app.remote.get("user")
    return ret.data["data"]
