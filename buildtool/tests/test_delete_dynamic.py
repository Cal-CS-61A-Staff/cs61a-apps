from harness import AddDep, Environment, Input, Sh, create_test_env


def test_deleting_dynamic_deps(snapshot):
    with create_test_env(snapshot) as env:
        env: Environment

        env.annotate("Create two files: f1 and f2")
        env.annotate("Initially, f1 will dynamically depend on f2")
        f1 = env.new_file()
        f2 = env.new_file()
        rule = env.declare_rule(
            AddDep(f1),
            input_action := Input([f1, f2], [AddDep(f2)]),
            shell_action := Sh([f1, f2]),
        )
        env.build(rule)

        env.annotate(
            "We then modify f1 so it no longer depends on f2, and also delete f2 altogether"
        )
        env.update_file(f1)
        env.delete_file(f2)
        input_action.update_result([f1], [])
        shell_action.update_result([f1])

        env.annotate(
            "Now, when we build the rule, the cached input will try to look up f2, but will fail to do so."
        )
        env.annotate(
            "However, this error should be caught and ignored, because dynamic deps are not guaranteed to be correct"
        )
        env.build(rule)
