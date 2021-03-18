import io
import signal
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, replace
from json import dump, dumps, load, loads
from textwrap import indent
from typing import Optional

import click

from examtool.api.database import get_exam, get_roster, get_submissions
from examtool.api.extract_questions import extract_questions
from examtool.api.scramble import scramble


@dataclass
class Test:
    stmt: str
    out: str = ""
    result: Optional[str] = None


doctests = dict(
    digit_replacer_iterative=[
        Test("is_div_three = lambda d: d % 3 == 0"),
        Test("lt_eight = lambda d: d < 8"),
        Test("always_six = lambda d: 6"),
        Test("floor_divide_five = lambda d: d // 5"),
        Test("digit_replacer(lambda _: True, always_six)(23096)", "66666"),
        Test("digit_replacer(is_div_three, floor_divide_five)(23096)", "20011"),
        Test("digit_replacer(lt_eight, always_six)(9064892)", "9666896"),
        Test("digit_replacer(lt_eight, always_six)(2)", "6"),
    ]
)

templates = dict(digit_replacer_iterative="""{SAKEBHLXNXOTVSAZTVFNYQQRGLCECPZY}""")


def depth(line):
    return len(line) - len(line.strip())


def indent_fixer(value):
    value = value.replace("\t", " " * 4)
    return value


def run(code, globs, *, is_stmt=False, only_err=False, timeout=2):
    did_timeout = False

    def timeout_handler(*_):
        nonlocal did_timeout
        did_timeout = True
        raise Exception("TIMEOUT")

    signal.signal(signal.SIGALRM, timeout_handler)
    err = None

    f = io.StringIO()
    with redirect_stdout(f):
        try:
            signal.alarm(timeout)
            if not is_stmt:
                try:
                    ret = eval(code, globs)
                    if ret is not None:
                        print(ret)
                except SyntaxError:
                    is_stmt = True
            if is_stmt:
                exec(code, globs)
        except Exception as e:
            print(e)
            err = str(e)

    signal.alarm(0)

    if did_timeout:
        print("Timeout")

    if only_err:
        return err

    return f.getvalue()


@click.command()
def autograde(fetch=True):
    EXAM = "cs61a-mt1-alt-7am"

    with open(f"{EXAM}_submissions.json", "w") as f:
        if fetch:
            submissions = {k: v for k, v in get_submissions(exam=EXAM)}
            dump(submissions, f)
        else:
            submissions = load(f)

    exam = get_exam(exam=EXAM)

    out = {None: {}}

    try:
        for email, _ in get_roster(exam=EXAM):
            submission = submissions.get(email, {})
            data = submission.copy()
            exam_copy = loads(dumps(exam))
            questions = {
                q["id"]: q
                for q in extract_questions(scramble(email, exam_copy, keep_data=True))
            }
            out[email] = {}
            for template_name, template in templates.items():
                alias_template_name = template_name
                for key, value in submission.items():
                    if key not in questions:
                        continue
                    if not isinstance(value, str):
                        continue
                    if key not in template:
                        continue
                    for original, replacement in questions[key][
                        "substitutions"
                    ].items():
                        template = template.replace(original, replacement)
                        alias_template_name = alias_template_name.replace(
                            original, replacement
                        )
                    value = indent_fixer(value)
                    for level in range(0, 12, 4):
                        data["_" * level + key] = indent(value, " " * level)
                soln = template.format_map(defaultdict(str, **data))
                globs = {}

                print("GRADING " + template_name)
                print(soln)

                status = run(soln, globs, is_stmt=True, only_err=True)

                tests = [replace(test) for test in doctests[template_name]]

                if status is None:
                    for test in tests:
                        result = run(test.stmt, globs).strip()
                        if result != test.out.strip():
                            test.result = f"FAILED: Expected {test.out}, got {result}"
                        else:
                            test.result = f"SUCCESS: Got {result}"

                print(status, tests)

                ag = "\n".join(
                    ">>> " + test.stmt + "\n" + test.result
                    if test.result is not None
                    else "DID NOT EXECUTE"
                    for test in tests
                )

                out[email][template_name] = ag
                out[None][template_name] = ag
                # input("continue?")

    finally:
        with open(f"doctests.json", "w+") as f:
            dump(out, f)
