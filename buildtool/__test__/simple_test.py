from __test__.harness import AddDep, Environment, Input, Sh, create_test_env


def simple_test():
    with create_test_env("simple_test") as env:
        env: Environment

        env.annotate("We have a source file f1")
        env.annotate("RuleA produces some output f2 from f1")

        f1 = env.new_file()
        rule1 = env.declare_rule(
            AddDep(f1),
            sh1 := Sh(inputs=[f1]),
        )
        f2 = rule1.output

        env.annotate("RuleB produces some further output f3 from f2")
        rule2 = env.declare_rule(
            AddDep(f2),
            sh2 := Sh(inputs=[f2]),
        )

        env.annotate(
            "Building RuleB requires f2 to be built from f1, then f3 to be built from f2"
        )
        env.build(rule2)

        env.annotate("We update file f1, but without affecting th output f2.")
        env.update_file(f1)

        env.annotate(
            "So we just need to rerun RuleA, and then can pull the output of RuleB from cache"
        )
        env.build(rule2)

        env.annotate(
            "However, this time we modify f1 in such a way that the output f2 is also modified."
        )
        env.update_file(f1)
        sh1.update_result([f1])

        env.annotate("So both RuleA and RuleB will need to be rerun")
        env.build(rule2)

        # update rule2 steps
        rule2.steps = [AddDep(rule1.output), Sh(inputs=[rule1.output])]


def modifying_dynamic_deps():
    with create_test_env("modifying_dynamic_deps") as env:
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


def deleting_dynamic_deps():
    with create_test_env("deleting_dynamic_deps") as env:
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
            "Now, when we build the rule, the cached input will try to look up f2, but will fail."
        )
        env.annotate(
            "However, this error should be caught and ignored, because dynamic deps are not guaranteed to be correct"
        )
        env.build(rule)


if __name__ == "__main__":
    # simple_test()
    # modifying_dynamic_deps()
    deleting_dynamic_deps()
