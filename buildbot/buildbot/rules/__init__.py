from typing import Optional, Sequence, Union

__all__ = ["declare_bash_rule"]

global callback


def declare_bash_rule(
    *,
    name: Optional[str] = None,
    deps: Sequence[str] = (),
    action: Optional[str] = None,
    outputs: Union[str, Sequence[str]] = (),
):
    def impl(ctx):
        if action:
            ctx.sh(action)

    callback(
        name=name,
        deps=deps,
        action=impl,
        outputs=outputs,
    )
