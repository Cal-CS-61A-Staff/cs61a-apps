from harness import AddDep, Environment, Input, Sh, create_test_env


def test_modifying_dynamic_deps(snapshot):
    with create_test_env(snapshot) as env:
        env: Environment

        env.annotate("Create two files: f1 and f2. ")
        env.annotate(
            "We explicitly depend on f1, but rely on an Input() to depend on f2 based on f1"
        )
        f1 = env.new_file()
        f2 = env.new_file()
        rule = env.declare_rule(
            AddDep(f1),
            input_action := Input([f1, f2], [AddDep(f2)]),
            shell_action := Sh([f1, f2]),
        )
        env.build(rule)

        env.annotate("We now modify f2 so we also depend on a new file f3")
        f3 = env.new_file()
        env.update_file(f2)
        input_action.update_result([f1, f2, f3], [AddDep(f2), AddDep(f3)])
        env.build(rule)
