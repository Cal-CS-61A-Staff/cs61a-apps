from typing import Optional, Sequence, Union

__all__ = ["declare_bash_rule"]

global callback


def _inject_callback(injected_callback):
    global callback
    callback = injected_callback


def declare_bash_rule(
    *,
    name: Optional[str] = None,
    deps: Sequence[str] = (),
    action: Optional[str] = None,
    outputs: Union[str, Sequence[str]] = (),
):
    callback(
        name=name,
        deps=deps,
        action=lambda ctx: (ctx.sh(action) if action else None),
        outputs=outputs,
    )
