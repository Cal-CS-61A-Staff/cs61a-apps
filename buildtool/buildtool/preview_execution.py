from typing import Callable, Union

from cache import make_cache_fetcher
from context import Env, MemorizeContext
from fs_utils import hash_file
from monitoring import log
from state import BuildState, Rule
from utils import CacheMiss, MissingDependency
from common.hash_utils import HashState


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

    def input(self, *, file: str = None, sh: str = None, env: Env = None):
        state = self.hashstate.state()
        super().input(file=file, sh=sh, env=env)
        if file is not None:
            return self.dep_fetcher(self.absolute(file))
        else:
            return self.cache_fetcher(state, HashState().record(sh, env).state())


def make_dep_fetcher(build_state: BuildState):
    def dep_fetcher(input_path, *, get_hash=False) -> Union[str, bytes]:
        try:
            if input_path not in build_state.source_files:
                rule = build_state.target_rule_lookup.lookup(build_state, input_path)
                # this input may be stale / unbuilt
                # if so, do not read it, but instead throw MissingDependency
                if rule not in build_state.ready:
                    raise MissingDependency(input_path)
                # so it's already ready for use!

            if get_hash:
                return hash_file(input_path)
            else:
                with open(input_path) as f:
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
    cache_fetcher, _ = make_cache_fetcher(build_state.cache_directory)
    dep_fetcher = make_dep_fetcher(build_state)

    ctx = PreviewContext(
        build_state.repo_root,
        rule.location,
        hashstate,
        dep_fetcher,
        cache_fetcher,
    )

    log(f"Looking for static dependencies of {rule}")
    for dep in rule.deps:
        if dep not in build_state.source_files:
            dep_rule = build_state.target_rule_lookup.lookup(build_state, dep)
            if dep_rule not in build_state.ready:
                log(
                    f"Static dependency {dep} of {dep_rule} is not ready, skipping impl"
                )
                # static deps are not yet ready
                break
            ctx.deps[dep] = dep_rule.provided_value
            if dep.startswith(":"):
                setattr(ctx.deps, dep[1:], dep_rule.provided_value)
                continue
        hashstate.update(dep.encode("utf-8"))
        try:
            hashstate.update(dep_fetcher(dep, get_hash=True))
        except MissingDependency:
            # get static deps before running the impl!
            # this means that a source file is *missing*, but the error will be thrown in enqueue_deps
            break
    else:
        ok = False
        try:
            log(f"Running impl of {rule} to discover dynamic dependencies")
            rule.provided_value = rule.impl(ctx)
            log(f"Impl of {rule} completed with discovered deps: {ctx.inputs}")
            for out in rule.outputs:
                # needed so that if we ask for another output, we don't panic if it's not in the cache
                hashstate.record(out)
            ok = True
        except CacheMiss:
            log(f"Cache miss while running impl of {rule}")
            pass  # stops context execution
        except MissingDependency as e:
            log(f"Dependencies {e.paths} were unavailable while running impl of {rule}")
            pass  # dep already added to ctx.inputs
        except Exception as e:
            print(
                "Error occurred during PreviewExecution. This may be normal, if a cached file that has not "
                "yet been reported / processed has been changed. However, it may also be an internal error, so "
                "it is being logged here. If it is an internal error, please contact the maintainer."
            )
            print(repr(e))
        # if `ok`, hash loaded dynamic dependencies
        if ok:
            log(
                f"Runtime dependencies resolved for {rule}, now checking dynamic dependencies"
            )
            for input_path in ctx.inputs:
                if input_path.startswith(":"):
                    input_dep = build_state.target_rule_lookup.try_lookup(input_path)
                    if input_dep is None or input_dep not in build_state.ready:
                        ok = False
                        log(f"Dynamic rule dependency {input_path} is not yet ready")
                        break
                else:
                    hashstate.update(input_path.encode("utf-8"))
                    try:
                        data = dep_fetcher(input_path, get_hash=True)
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
            ctx.uses_dynamic_inputs,
        )
    return None, rule.deps, None
