import subprocess

GOAL_SCORE = 100

MAX_ROLLS = 10


def make_strat_str(strat_0, strat_1):
    """Takes in two separate strategies and converts them both into a string
    separating each num_roll of dice by a newline.

    :param strat_0: the first inputted strategy
    :type param1: list of lists
    :param param2: the second inputted strategy
    :type param2: list of lists

    :return: a string representing the number of dice rolls for each of the
    possible score values for both strategies, with each number separated by
    a newline
    """
    out = []
    for strat in [strat_0, strat_1]:
        for i in range(GOAL_SCORE):
            for j in range(GOAL_SCORE):
                out.append(str(strat[i][j]))
    return "\n".join(out)


def match(strat_0, strat_1, *, use_contest=True):
    p = subprocess.Popen(
        ["./bacon" if use_contest else "./bacon_proj"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    strat_str = make_strat_str(strat_0, strat_1)
    out, err = p.communicate(bytes(strat_str, "utf-8"))
    if err:
        raise Exception(err.decode("utf-8"))
    return float(out.decode("utf-8"))


def score(strat_0, strat_1, *, use_contest=True):
    return (
        1
        + match(strat_0, strat_1, use_contest=use_contest)
        - match(strat_1, strat_0, use_contest=use_contest)
    ) / 2
