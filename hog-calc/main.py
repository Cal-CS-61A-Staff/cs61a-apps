import json
from datetime import timedelta

from flask import Flask, jsonify, request

from common.db import connect_db
from process_input import validate_strat
from rate_limiting import ratelimited
from runner import score

app = Flask(__name__)

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


@app.route("/api/compare_strategies", methods=["POST"])
@ratelimited(timedelta(minutes=1))
def compare_strategies():
    strat0 = json.loads(request.form["strat0"])
    strat1 = json.loads(request.form["strat1"])
    use_contest = bool(request.form.get("use_contest"))
    return jsonify(
        {
            "success": True,
            "win_rate": score(
                validate_strat(strat0),
                validate_strat(strat1),
                use_contest=use_contest,
            ),
        }
    )


if __name__ == "__main__":
    app.run()
