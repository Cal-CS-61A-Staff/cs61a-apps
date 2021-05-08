import json
import os
from datetime import datetime, timedelta
from json import JSONDecodeError

from flask import Flask, abort, jsonify, render_template, request
from pytz import timezone

import tournament
from common.course_config import get_endpoint
from common.db import connect_db
from contest_utils.oauth import get_group
from contest_utils.rate_limiting import ratelimited
from logger import get_log, log
from process_input import record_strat
from tournament import build_ranking, run_tournament

app = Flask(__name__)

ASSIGNMENT = "proj01contest"

with connect_db() as db:
    db("CREATE TABLE IF NOT EXISTS accesses (email VARCHAR(128), last_access INTEGER)")
    db(
        """CREATE TABLE IF NOT EXISTS cached_strategies (
            email VARCHAR(128), name VARCHAR(1024), hash VARCHAR(128), strategy LONGBLOB
        )"""
    )
    db(
        "CREATE TABLE IF NOT EXISTS cached_winrates (hash_0 VARCHAR(128), hash_1 VARCHAR(128), winrate DOUBLE)"
    )


def expand_semester(short_form: str):
    """
    Takes in a semester name in condensed notation (eg. sp21, fa20, su18) and expands it into
    a full version (eg. Spring 21, Fall 20, Summer 18).

    :param short_form: condensed notation for a semester
    :type short_form: str
    
    :return: expanded notation for semester (str)

    """
    return "{} 20{}".format(
        {"sp": "Spring", "su": "Summer", "fa": "Fall"}[short_form[:2]], short_form[2:]
    )


def semester_key(short_form):
    """
    Construct a key from the SHORT_FORM of the semester
    
    :param short_form: condensed notation for a semester
    :type short_form: str
    
    :return: double representing a key value for the semester SHORT_FORM
    """
    return int(short_form[2:]) + 0.2 * {"sp": 1, "su": 2, "fa": 3}[short_form[:2]]


@app.route("/")
def index():
    links = sorted(
        (
            [x.split(".")[0], expand_semester(x.split(".")[0])]
            for x in os.listdir("data/leaderboards")
        ),
        key=lambda x: semester_key(x[0]),
    )

    return render_template(
        "hog-template.html",
        timestamp=tournament.last_updated,
        ranking=tournament.ranking,
        team_list=[x[1] for x in tournament.ranking],
        winrate_mat=tournament.winrates,
        links=links,
    )


@app.route("/winners")
def winners():
    with open("data/winners.json") as f:
        old_winners = json.load(f)
    past_winners = []
    for semester, winners in old_winners.items():
        past_winners.append([expand_semester(semester), winners, semester])
    past_winners.sort(key=lambda x: -semester_key(x[2]))
    return render_template("hog-winners.html", past_winners=past_winners)


@app.route("/old_results/<semester>/")
def old_results(semester):
    for datafile in os.listdir("data/leaderboards"):
        if datafile == semester + ".json":
            break
    else:
        abort(404)
        return

    with open(os.path.join("data/leaderboards", datafile)) as f:
        data = json.load(f)

    winrate_mat, teams = data["winrate_mat"], data["teams"]

    teams = [
        (team, sum(score > tournament.THRESHOLD for score in team_scores))
        for team, team_scores in zip(teams, winrate_mat)
    ]

    ranking = build_ranking(teams)

    return render_template(
        "hog-template.html",
        timestamp="the end of the tournament.",
        ranking=ranking,
        team_list=[x[1] for x in ranking],
        winrate_mat=winrate_mat,
        suffix="({})".format(expand_semester(semester)),
    )


@app.route("/log")
def test():
    return "<pre>{}</pre>".format(get_log())


@app.route("/api/submit_strategy", methods=["POST"])
@ratelimited(timedelta(minutes=1))
def submit_strategy():
    curr_time = datetime.now().astimezone(timezone("US/Pacific"))
    end_time = datetime(2021, 2, 23, 23, 59, 0, tzinfo=timezone("US/Pacific"))
    if curr_time > end_time:
        abort(423, "The competition has ended.")
    try:
        strat = json.loads(request.form["strat"])
    except JSONDecodeError:
        abort(400, "Received malformed JSON strategy")
    group = get_group(get_endpoint("cs61a") + f"/{ASSIGNMENT}")

    hashed = record_strat(request.form["name"], group, strat)
    run_tournament()
    log("New strategy received, tournament will restart after current match completes.")
    return jsonify({"success": True, "group": group, "hash": hashed})


log("Main thread starting. If this message is duplicated, something has gone wrong.")

tournament.post_tournament()


if __name__ == "__main__":
    app.run()
