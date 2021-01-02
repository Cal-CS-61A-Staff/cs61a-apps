from typing import Optional, Sequence, Union

__all__ = ["declare_bash_rule"]

global callback


def declare_bash_rule(
    *,
    name: Optional[str] = None,
    deps: Sequence[str] = (),
    cmd: Optional[str] = None,
    outputs: Union[str, Sequence[str]] = (),
):
    def impl(ctx):
        if cmd:
            ctx.sh(cmd)

    callback(
        name=name,
        deps=deps,
        impl=impl,
        outputs=outputs,
    )
