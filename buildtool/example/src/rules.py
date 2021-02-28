from buildtool import callback

ENV = dict(PATH=["@//env/bin/", "/bin"])


def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build", env=ENV)
        raw_deps = ctx.input(sh=f"gcc {ctx.relative(src)} -MM", env=ENV)
        deps = raw_deps.strip().split(" ")[1:]
        ctx.add_deps(deps)
        ctx.sh(f"gcc {ctx.relative(src)} -c -o {ctx.relative(out)}", env=ENV)

    return callback(
        name=name,
        impl=impl,
        out=out,
    )
