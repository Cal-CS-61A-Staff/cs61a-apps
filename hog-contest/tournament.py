import base64
import json
import queue
from collections import defaultdict
from datetime import datetime
from itertools import product
from threading import Thread

from pytz import timezone

from common.db import connect_db
from logger import log
from runner import score
from thread_utils import only_once

NUM_WORKERS = 4
LOG_MOD = 1

THRESHOLD = 0.500001

last_updated = "the end of the tournament."  # "unknown"


def post_tournament():
    log("Updating website...")
    global ranking, winrates

    with connect_db() as db:
        hash_lookup = db("SELECT name, hash FROM cached_strategies").fetchall()
        db_winrates = db(
            "SELECT hash_0, hash_1, winrate FROM cached_winrates"
        ).fetchall()

        winrate_dict = defaultdict(lambda: defaultdict(float))
        num_wins = defaultdict(int)

        active_teams = []
        for name, hash in hash_lookup:
            active_teams.append([name, hash])

        for hash_0, hash_1, winrate in db_winrates:
            winrate_dict[hash_0][hash_1] = winrate
            winrate_dict[hash_1][hash_0] = 1 - winrate
            winrate_dict[hash_0][hash_0] = 0.5
            winrate_dict[hash_1][hash_1] = 0.5

        for team_0, hash_0 in active_teams:
            for team_1, hash_1 in active_teams:
                if winrate_dict[hash_0][hash_1] > THRESHOLD:
                    num_wins[team_0] += 1

        teams = []
        for name, hash in hash_lookup:
            teams.append([base64.b64decode(name).decode("utf-8"), num_wins[name], hash])

        teams.sort(key=lambda x: x[1], reverse=True)

        ranking = build_ranking(teams)

        winrates = []
        for _, _, hash_0 in teams:
            winrates.append([])
            for _, _, hash_1 in teams:
                winrates[-1].append(winrate_dict[hash_0][hash_1])


def build_ranking(teams):
    out = []
    prev_wins = float("inf")
    curr_rank = -1
    cnt = 0
    for name, wins, *_ in teams:
        cnt += 1
        if wins < prev_wins:
            curr_rank += cnt
            prev_wins = wins
            cnt = 0
        out.append([curr_rank, name, wins])
    return out


def worker(t_id, q, out, goal):
    while True:
        task = q.get()
        if task is None:
            break
        hash_0, strat_0, hash_1, strat_1 = task
        log("Thread {}: Matching {} vs {}".format(t_id, hash_0, hash_1))
        out[hash_0, hash_1] = score(strat_0, strat_1)
        log("Thread {} finished match.".format(t_id))
        q.task_done()
        if q.qsize() % LOG_MOD == 0:
            log("{} / {} matches complete".format(goal - q.qsize(), goal))


def unwrap(strat):
    return strat["hash"], json.loads(strat["strategy"])


@only_once
def run_tournament():
    global last_updated
    with connect_db() as db:
        all_strategies = db("SELECT hash, strategy FROM cached_strategies").fetchall()
        cached_winrates = db(
            "SELECT hash_0, hash_1, winrate FROM cached_winrates"
        ).fetchall()

    start_time = datetime.now().astimezone(timezone("US/Pacific"))
    log("Starting tournament with frozen copy of strategies...")

    winrates = {}
    for hash_0, hash_1, winrate in cached_winrates:
        winrates[hash_0, hash_1] = winrate

    tasks = queue.Queue()

    num_done = 0

    for entry_0, entry_1 in product(all_strategies, all_strategies):
        if entry_0["hash"] >= entry_1["hash"]:
            continue
        if (entry_0["hash"], entry_1["hash"]) in winrates:
            num_done += 1
            continue

        tasks.put([*unwrap(entry_0), *unwrap(entry_1)])

    num_todo = tasks.qsize()
    log(
        "{} matches recovered from cache, {} to be recomputed".format(
            num_done, num_todo
        )
    )

    out = {}  # access is thread-safe since we're always writing to diff. keys

    threads = []

    for i in range(NUM_WORKERS):
        t = Thread(target=worker, args=(i, tasks, out, num_todo))
        log("Starting thread {}...".format(i))
        t.start()
        threads.append(t)

    tasks.join()

    log("Tournament finished, storing results...")

    for i in range(NUM_WORKERS):
        tasks.put(None)

    with connect_db() as db:
        for (hash_0, hash_1), winrate in out.items():
            db(
                "INSERT INTO cached_winrates VALUES (%s, %s, %s)",
                [hash_0, hash_1, winrate],
            )

    last_updated = start_time
    post_tournament()
    log("Website updated")


post_tournament()
