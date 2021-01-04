import rules
from rules import *


declare_bash_rule(
    deps=["cat.py"],
    cmd="mkdir temp && mkdir dog2 && cat cat.py > temp/out_0.py",
    outputs="temp/out_0.py",
)

declare_bash_rule(
    deps=["dependency_template"],
    cmd="mkdir temp && cp dependency_template temp/dependency_template",
    outputs="temp/dependency_template",
)


def declare_magic_bash_rule(i):
    def impl(ctx):
        template = ctx.input(sh="cat temp/dependency_template").strip()
        ctx.add_dep(template.format(i - 1))
        ctx.sh(f"cat temp/out_{i - 1}.py > temp/out_{i}.py        ")

    rules.callback(
        deps=["temp/dependency_template"],
        impl=impl,
        outputs=f"temp/out_{i}.py",
    )


for i in range(1, 1000):
    declare_magic_bash_rule(i)

declare_bash_rule(
    name=f"all",
    deps=[f"temp/out_{i}.py" for i in range(1, 2)],
)

# @nocommit have something that blocks rules with no outputs!
