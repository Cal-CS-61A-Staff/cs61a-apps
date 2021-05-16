import base64
import hashlib
import json

from werkzeug.exceptions import abort

from common.db import connect_db
from runner import GOAL_SCORE, MAX_ROLLS


def validate_strat(received_strat):
    """This function validates that the strategy inputted gives out a number of
    rolls for each pair of score values that is within the acceptable range of
    rolls. It then returns the strategy.

    :param received_strat: the strategy that was submitted by a student
    :type received_strat: dict

    :return: list of lists with the strategy's number of rolls for given scores
    """
    extracted_strat = []
    for i in range(GOAL_SCORE):
        extracted_strat.append([])
        for j in range(GOAL_SCORE):
            try:
                val = int(received_strat[i][j])
            except ValueError:
                abort(
                    400,
                    "Your strategy returns for inputs ({}, {}), which is not an integer.".format(
                        i, j, received_strat[i][j]
                    ),
                )
                return
            if not (0 <= val <= MAX_ROLLS):
                abort(
                    400,
                    "Your strategy rolls {} dice for inputs ({}, {}), which is not a valid roll.".format(
                        i, j, val
                    ),
                )
            extracted_strat[-1].append(val)
    return extracted_strat


def record_strat(name, group, received_strat):
    """This function takes in a submitted strategy and validates it, then
    encodes it in JSON format along with the name, a hash of the strategy, and
    the email of one of the users in the group, and stores it on the CS61A
    database.

    :param name: the name of the strategy provided
    :type name: str
    :param group: the group of students submitting the strategy
    :type group: list
    :param received_strat: the strategy that was submitted, which will be
    evaluated and stored on the database
    :type received_strat: dict

    :return: the hash of the received strategy
    """
    if not isinstance(name, str):
        abort(400, "Name is not a string!")
    name = base64.encodebytes(bytes(name, "utf-8"))
    if len(name) >= 1024:
        abort(400, "Strategy name is too long!")
    name = name.decode("utf-8")
    extracted_strat = validate_strat(received_strat)
    # extracted_strat probably OK
    email = group[0]
    encoded_strat = json.dumps(extracted_strat)
    hashed = hashlib.md5(bytes(encoded_strat, "utf-8")).hexdigest()

    # time to load it into the database
    with connect_db() as db:
        dupes = db(
            "SELECT email FROM cached_strategies WHERE name = (%s)", [name]
        ).fetchall()
        for dupe in dupes:
            if dupe["email"] not in group:
                abort(
                    409,
                    "Another strategy has already been submitted with the same name.",
                )
        for member in group:
            db("DELETE FROM cached_strategies WHERE email=(%s)", [member])
        db(
            "INSERT INTO cached_strategies VALUES (%s, %s, %s, %s)",
            [email, name, hashed, encoded_strat],
        )

    return hashed
