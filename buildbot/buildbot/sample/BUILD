from rules import *

declare_bash_rule(
    name="hw2",
    deps=["out.py"],
    action="cat out.py > out2.py",
    outputs="out2.py",
)


declare_bash_rule(
    name="hw",
    deps=["cat.py"],
    action="cat cat.py > out.py",
    outputs="out.py",
)
