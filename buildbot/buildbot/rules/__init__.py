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
        out=outputs,
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
        config_ = ctx.relative(config)
        source_ = ctx.relative(source)
        template_ = ctx.relative(template)
        destination_ = ctx.relative(destination)

        make_dependency = ctx.relative("//src/make_dependency.py")

        deps = ctx.input(
            sh=f"python3 {make_dependency} {source_} {destination_} --mode deps"
        ).split()

        ctx.add_deps(deps)

        assets = (
            ctx.input(
                sh=f"python3 {make_dependency} {source_} {destination_} --mode assets"
            )
            .strip()
            .split()
        )

        for asset_spec in assets:
            asset, asset_destination = asset_spec.split()
            ctx.add_dep(asset)

        ctx.sh(f"templar -c {config_} -s {source_} -t {template_} -d {destination_}")

    templates = [
        *callback.glob("web/templates/*"),
        *callback.glob("main/templates/*"),
    ]

    callback(
        name=name,
        deps=[config, "//src/make_dependency.py", source, *templates],
        impl=impl,
        out=destination,
    )
