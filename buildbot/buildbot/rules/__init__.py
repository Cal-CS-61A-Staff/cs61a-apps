from typing import Optional, Sequence, Union

__all__ = ["declare_bash_rule", "declare_templar_rule"]

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


def declare_templar_rule(
    *,
    name: Optional[str] = None,
    config: str,
    source: str,
    template: str,
    destination: str,
):
    def impl(ctx):
        config_ = ctx.resolve(config)
        source_ = ctx.resolve(source)
        template_ = ctx.resolve(template)
        destination_ = ctx.resolve(destination)

        make_dependency = ctx.resolve("//src/make_dependency.py")

        deps = ctx.input(
            sh=f"python3 {make_dependency} {source_} {destination_} --mode deps"
        ).split()

        ctx.add_deps(deps)

        assets = ctx.input(
            sh=f"python3 {make_dependency} {source_} {destination_} --mode assets"
        ).split("\n")

        for asset_spec in assets:
            asset, asset_destination = asset_spec.split()
            ctx.add_dep(asset)

        ctx.sh(f"templar -c {config_} -s {source_} -t {template_} -d {destination_}")

    callback(
        name=name,
        deps=[config],
        impl=impl,
        out=destination,
    )
