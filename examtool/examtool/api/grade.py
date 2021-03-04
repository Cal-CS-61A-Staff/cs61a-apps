def boolstring(bool):
    return "Matches solution." if bool else "May not match solution."


def grade(email, question, responses, dispatch=None):
    if dispatch:
        if dispatch(email, question):
            return dispatch(email, question)(responses)
    response = responses.get(question["id"])
    if "solution" not in question:
        return "Instant autograder unavailable."

    if response is None:
        return boolstring(False)

    if question["type"] == "multiple_choice":
        return boolstring(response in question["solution"]["options"])
    elif question["type"] == "select_all":
        if question["solution"].get("options"):
            return boolstring(
                sorted(response) == sorted(question["solution"]["options"])
            )
    else:
        if question["solution"].get("solution"):
            return boolstring(response == question["solution"]["solution"]["text"])

    return "Instant autograder unavailable."
