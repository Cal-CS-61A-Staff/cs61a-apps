import subprocess

GOAL_SCORE = 100

MAX_ROLLS = 10


def make_strat_str(strat_0, strat_1):
    out = []
    for strat in [strat_0, strat_1]:
        for i in range(GOAL_SCORE):
            for j in range(GOAL_SCORE):
                out.append(str(strat[i][j]))
    return "\n".join(out)


def match(strat_0, strat_1):
    p = subprocess.Popen(
        ["./bacon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    strat_str = make_strat_str(strat_0, strat_1)
    out, err = p.communicate(bytes(strat_str, "utf-8"))
    if err:
        raise Exception(err.decode("utf-8"))
    return float(out.decode("utf-8"))


def score(strat_0, strat_1):
    return (1 + match(strat_0, strat_1) - match(strat_1, strat_0)) / 2


def compile():
    subprocess.run(["g++", "-std=c++17", "-O3", "main.cpp", "-Wall", "-o", "bacon"])
