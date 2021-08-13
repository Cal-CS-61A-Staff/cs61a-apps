from os.path import basename

rules = load("rules.py")

all_rules = []

for src in find("*.c"):
    name = basename(src)[:-2]
    all_rules.append(rules.declare(name=name, src=src, out=f"../build/{name}.out"))

callback(
    name="all_examples",
    deps=all_rules,
)
