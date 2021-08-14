from harness import AddDep, Environment, Sh, create_test_env


def test_simple(snapshot):
    with create_test_env(snapshot) as env:
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

        env.annotate(
            "Update RuleB to have a different shell command, so it needs to be rerun"
        )
        env.annotate("But RuleA doesn't need to rerun since it's unchanged")
        rule2.steps = [AddDep(rule1.output), Sh(inputs=[rule1.output])]
        env.build(rule2)

        env.annotate(
            "Now we modify f1 and the output f2, so both rules have to be rerun"
        )
        env.update_file(f1)
        sh1.update_result([f1])
        env.build(rule2)
