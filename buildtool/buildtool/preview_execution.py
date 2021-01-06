import hashlib
from typing import Callable, Union

from cache import make_cache_fetcher
from context import MemorizeContext
from monitoring import log
from utils import CacheMiss, HashState, MissingDependency
from state import BuildState, Rule


class PreviewContext(MemorizeContext):
    def __init__(
        self,
        repo_root: str,
        cwd: str,
        hashstate: HashState,
        dep_fetcher: Callable[[str], str],
        cache_fetcher: Callable[[str, str], str],
    ):
        super().__init__(repo_root, cwd, hashstate)

        self.dep_fetcher = dep_fetcher
        self.cache_fetcher = cache_fetcher

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            return self.dep_fetcher(self.absolute(file))
        else:
            return self.cache_fetcher(
                self.hashstate.state(),
                hashlib.md5(sh.encode("utf-8")).hexdigest(),
            )


def make_dep_fetcher(build_state: BuildState):
    def dep_fetcher(input_path, *, flags="r") -> Union[str, bytes]:
        try:
            if input_path not in build_state.source_files:
                rule = build_state.target_rule_lookup.lookup(build_state, input_path)
                # this input may be stale / unbuilt
                # if so, do not read it, but instead throw MissingDependency
                if rule not in build_state.ready:
                    raise MissingDependency(input_path)
                # so it's already ready for use!

            with open(input_path, flags) as f:
                return f.read()
        except FileNotFoundError:
            raise MissingDependency(input_path)

    return dep_fetcher


def get_deps(build_state: BuildState, rule: Rule):
    """
    Use static dependencies and caches to try and identify as *many*
    needed dependencies as possible, without *any* spurious dependencies.
    """
    hashstate = HashState()
    cache_fetcher = make_cache_fetcher(build_state.cache_directory)
    dep_fetcher = make_dep_fetcher(build_state)

    log(f"Looking for static dependencies of {rule}")
    for dep in rule.deps:
        if dep not in build_state.source_files:
            if (
                build_state.target_rule_lookup.lookup(build_state, dep)
                not in build_state.ready
            ):
                log(f"Static dependency {dep} of {rule} is not ready, skipping impl")
                # static deps are not yet ready
                break
        if dep.startswith(":"):
            continue
        hashstate.update(dep.encode("utf-8"))
        try:
            hashstate.update(dep_fetcher(dep, flags="rb"))
        except MissingDependency:
            # get static deps before running the impl!
            # this means that a source file is *missing*, but the error will be thrown in enqueue_deps
            break
    else:
        ctx = PreviewContext(
            build_state.repo_root,
            rule.location,
            hashstate,
            dep_fetcher,
            cache_fetcher,
        )
        ok = False
        try:
            log(f"Running impl of {rule} to discover dynamic dependencies")
            rule.impl(ctx)
            log(f"Impl of {rule} completed with discovered deps: {ctx.inputs}")
            ok = True
        except CacheMiss:
            log(f"Cache miss while running impl of {rule}")
            pass  # stops context execution
        except MissingDependency as e:
            log(f"Dependencies {e.paths} were unavailable while running impl of {rule}")
            pass  # dep already added to ctx.inputs
        # if `ok`, hash loaded dynamic dependencies
        if ok:
            log(
                f"Runtime dependencies resolved for {rule}, now checking dynamic dependencies"
            )
            for input_path in ctx.inputs:
                hashstate.update(input_path.encode("utf-8"))
                try:
                    data = dep_fetcher(input_path, flags="rb")
                except MissingDependency as e:
                    # this dependency was not needed for deps calculation
                    # but is not verified to be up-to-date
                    ok = False
                    log(
                        f"Dynamic dependencies {e.paths} were not needed for the impl, but are not up to date"
                    )
                    break
                else:
                    hashstate.update(data)
        return (
            hashstate.state() if ok else None,
            ctx.inputs + rule.deps,
        )
    return None, rule.deps
