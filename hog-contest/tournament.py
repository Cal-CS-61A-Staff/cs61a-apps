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
    """
    RANKINGS and WINRATES are nonlocal variables

    Connect to the database. Fetch all name and hash pairs from the CACHED_STRATEGIES
    table (Call this hash_lookup). Fetch all winrates from CACHED_WINRATES table (call
    this db_winrates).

    Create a nested defaultdict for the winrate and a defaultdict for num rates.

    Create a 2d array from the data in hash loopup, where each data point is a [name, hash]
    pair and call this new data structure ACTIVE_TEAMS.

    Iterate through db_winrates and add the data into the nested WINRATE_DICT
    (data: h0, h1, rate) such that it follows the following convention:
    - WINRATE_DICT[h0][h1] = winrate
    - WINRATE_DICT[h1][h0] = 1 - winrate
    - WINRATE_DICT[h0][h0] = 0.5
    - WINRATE_DICT[h1][h1] = 0.5

    Have two teams play against each other. If the winrate of team0 agains team1 is
    greater that THRESHOLD, then add 1 win to the num_teams dict for team0.

    Construct a new array for teams data consisting of [team name decoded, number of wins, and the hash].

    Sort the teams by number of wins, and construct a ranking.

    Create a 2-d Matrix of WINRATES of each team playing each other.

    :return: None
    """
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
    """
    Assigns rankings to the teams based on their winrates. If teams are tied,
    they will be assigned the same ranking as each other.

    :param teams: A list of teams, where each element is a list containing a team's name
        and winrate (among potentially other data). This list is already sorted by num wins in descending order.
    :type teams: list

    :return: List of teams with their rank, name, and number of wins, in ascending order of rank.

    """
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
    """
    We get each task from the queue. Score the strategies.
    Store the score in the OUT dictionary.
    Finish the task.
    If the size of our queue is a factor of LOG_MOD, then we log the number of matches completed.

    :param t_id: Id number
    :type t_id: int

    :param q: Queue of tasks
    :type q: Queue

    :param out: data structure of the storing the score between strategies.
    :type out: dictionary

    :param goal: Size of the queue of tasks. AKA Number of tasks.
    :type goal: int

    :return: None
    """
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
    """
    Return the hash of the strat, and load the strategy from json.

    :param strat: data structure containing data pertaining to the strategy.
    :type strat: dictionary

    :return: tuple of hash and the strategy loaded from json.
    """
    return strat["hash"], json.loads(strat["strategy"])


@only_once
def run_tournament():
    """
    Connects to database, and fetches data from CACHED_STRATEGIES and CACHED_WINRATES.
    Stores the current time as START_TIME.

    Store the data from CACHED_WINRATES in a dictionary called WINRATES.

    Create a QUEUE for tasks.

    Iterate through entry0, entry1 in the Cartesian product of ALL_STRATEGIES and
    ALL_STRATEGIES. If hash of entry0 is greater than or equal to the hash of entry1 move
    onto the next entry pair. If the tuple of the hashes of entry0 and entry1 are in the
    WINRATES dictionary, then add 1 to the NUM_DONE variable, and move onto the next entry pair.
    If neither of the former two cases are true, then call unwrap on both of the entries and put
    the output of both calls in a list and put this list in the tasks queue.

    Create a dictionary called OUT, and a list called THREADS.

    Create a THREAD where the target=worker, and pass in the arguments T_ID, the queue of TASKS,
    the OUT dictionary, and SIZE of the TASKS queue.
    Start each process. Then append to the THREADS list.

    Join the TASKS structure.

    Add end-of-queue markers to the TASKS structure.

    Store the newly computed winrates into the CACHED_WINRATES data table.

    Update the LAST_UPDATED time with the START_TIME. Call
    the POST_TOURNAMENT function.

    """
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
