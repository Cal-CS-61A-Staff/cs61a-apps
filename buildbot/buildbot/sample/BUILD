from rules import *


declare_bash_rule(
    deps=["cat.py"],
    cmd="mkdir temp && cat cat.py > temp/out_0.py",
    outputs="temp/out_0.py",
)


for i in range(1, 1000):
    declare_bash_rule(
        name=f"hw_{i}",
        deps=[f"temp/out_{i//2}.py"],
        cmd=f"cat temp/out_{i//2}.py > temp/out_{i}.py",
        outputs=f"temp/out_{i}.py",
    )

declare_bash_rule(
    name=f"all",
    deps=[f"temp/out_{i}.py" for i in range(1000)],
)
