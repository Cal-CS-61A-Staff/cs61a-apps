from typing import Callable, Dict

from cache import make_cache_load
from common.hash_utils import HashState
from context import Env, MemorizeContext
from fs_utils import hash_file
from monitoring import log
from state import BuildState, Rule
from utils import CacheMiss, MissingDependency


class PreviewContext(MemorizeContext):
    def __init__(
        self,
        cwd: str,
        macros: Dict[str, Callable],
        hashstate: HashState,
        dep_fetcher: Callable[[str], Rule],
        cache_fetcher: Callable[[str, str], str],
    ):
        super().__init__(cwd, macros, hashstate, dep_fetcher)
        self.cache_fetcher = cache_fetcher

    def input(self, sh: str = None, *, env: Env = None):
        state = self.hashstate.state()
        super().input(sh, env=env)
        return self.cache_fetcher(state, HashState().record(sh, env).state())


def make_dep_fetcher(build_state: BuildState):
    def dep_fetcher(input_path, type: str = "rule"):
        try:
            rule = None
            if input_path not in build_state.source_files:
                rule = build_state.target_rule_lookup.lookup(build_state, input_path)
                # this input may be stale / unbuilt
                # if so, do not read it, but instead throw MissingDependency
                if rule not in build_state.ready:
                    raise MissingDependency(input_path)
                # so it's already ready for use!

            if type == "hash":
                return hash_file(input_path)
            elif type == "rule":
                return rule
            else:
                raise Exception(f"Unknown dep type {type}")
        except FileNotFoundError:
            raise MissingDependency(input_path)

    return dep_fetcher


def get_deps(build_state: BuildState, rule: Rule, *, skip_cache_key: bool):
    """
    Use static dependencies and caches to try and identify as *many*
    needed dependencies as possible, without *any* spurious dependencies.
    """
    hashstate = HashState()
    cache_load_string, _ = make_cache_load(build_state.cache_directory)
    dep_fetcher = make_dep_fetcher(build_state)

    ctx = PreviewContext(
        rule.location,
        build_state.macros,
        hashstate,
        dep_fetcher,
        cache_load_string,
    )

    ok = False
    provided_value = None
    try:
        log(f"Running impl of {rule} to discover dependencies")
        if not skip_cache_key:
            for out in rule.outputs:
                # needed so that if we ask for another output, we don't panic if it's not in the cache
                hashstate.record(out)
        provided_value = rule.impl(ctx)
        log(f"Impl of {rule} completed with deps: {ctx.inputs}")
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
        if not ctx.uses_dynamic_inputs:
            raise
    # if `ok`, hash loaded dynamic dependencies
    if ok:
        log(f"Inputs and dependencies resolved for {rule}")
        for input_path in ctx.inputs:
            if input_path.startswith(":"):
                input_dep = build_state.target_rule_lookup.try_lookup(input_path)
                if input_dep is None or input_dep not in build_state.ready:
                    ok = False
                    log(
                        f"Rule dependency {input_path} is not yet ready (or does not exist)"
                    )
                    break
            else:
                if not skip_cache_key:
                    hashstate.update(input_path.encode("utf-8"))
                try:
                    data = dep_fetcher(input_path, "rule" if skip_cache_key else "hash")
                except MissingDependency as e:
                    # this dependency was not needed for deps calculation
                    # but is not verified to be up-to-date
                    ok = False
                    log(
                        f"Dependencies {e.paths} were not needed for the impl, but are not up to date"
                    )
                    break
                else:
                    if not skip_cache_key:
                        hashstate.update(data)
        hashstate.record("done")

    return (
        hashstate.state() if ok else None,
        provided_value,
        ctx.inputs,
        ctx.deferred_inputs,
        ctx.uses_dynamic_inputs,
    )
