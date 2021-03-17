import doctest
import io
from collections import defaultdict
from contextlib import redirect_stdout
from json import dump, dumps, load, loads
from os import system
from textwrap import indent
from traceback import print_exc

from examtool.api.extract_questions import extract_questions

from examtool.api.scramble import scramble

from examtool.api.database import get_exam, get_roster, get_submissions

import click

templates = dict(
    digit_replacer_iterative='''
{SAKEBHLXNXOTVSAZTVFNYQQRGLCECPZY}

digit_replacer_iterative = digit_replacer

digit_replacer_iterative.__doc__ = """
    >>> is_div_three = lambda d: d % 3 == 0
    >>> lt_eight = lambda d: d < 8
    >>> always_six = lambda d: 6
    >>> floor_divide_five = lambda d: d // 5
    >>> digit_replacer(lambda _: True, always_six)(23096)
    66666
    >>> digit_replacer(is_div_three, floor_divide_five)(23096)
    20011
    >>> digit_replacer(lt_eight, always_six)(9064892)
    9666896
    >>> digit_replacer(lt_eight, always_six)(2)
    6
"""
    ''',
    digit_replacer_recursive='''
{MUIZUERIWRWAVYNDROYEPXSTLHPKPUFF}

digit_replacer_recursive = digit_replacer

digit_replacer_recursive.__doc__ = """
    >>> is_div_three = lambda d: d % 3 == 0
    >>> lt_eight = lambda d: d < 8
    >>> always_six = lambda d: 6
    >>> floor_divide_five = lambda d: d // 5
    >>> digit_replacer(lambda _: True, always_six)(23096)
    66666
    >>> digit_replacer(is_div_three, floor_divide_five)(23096)
    20011
    >>> digit_replacer(lt_eight, always_six)(9064892)
    9666896
    >>> digit_replacer(lt_eight, always_six)(2)
    6
"""
    ''',
    restrict_domain='''
def restrict_domain(f, low_d, high_d):
    """Returns a function that restricts the domain of F,
    a function that takes a single argument x.
    If x is not between LOW_D and HIGH_D (inclusive),
    it returns -Infinity, but otherwise returns F(x).

    >>> from math import sqrt
    >>> f = restrict_domain(sqrt, 1, 100)
    >>> f(25)
    5.0
    >>> f(-25)
    -inf
    >>> f(125)
    -inf
    >>> f(2.25)
    1.5
    >>> f(100)
    10.0
    """
    {AUNYWXTHKTPIYULGUQVTMMJCDIZFOKDC}
        {DDFDKNJWPPWCSUIVKVZKPWNMOWZFEHCZ}
            {RYCOJROYBYZVPWVCDPPXSGKILCYZHDVP}
        {ENWCLQWKMELKJFGFUOVEZNPLRMIOGLNM}
    return wrapper_method_name
''',
    restrict_range='''
def restrict_range(f, low_r, high_r):
    """Returns a function that restricts the range of F, a function
    that takes a single argument X. If the return value of F(X)
    is not between LOW_R and HIGH_R (inclusive), it returns -Infinity,
    but otherwise returns F(X).
    
    >>> cube = lambda x: x * x * x
    >>> f = restrict_range(cube, 1, 1000)
    >>> f(1)
    1
    >>> f(-5)
    -inf
    >>> f(5)
    125
    >>> f(10)
    1000
    >>> f(11)
    -inf
    >>> g = restrict_range(lambda x: 10, 1, 1000)
    >>> g("cat")
    10
    """
    {TFWWEGUZTLHAPBWGEFCFWKEQDQRLPIQL}
    #   (a)
        {TWRGFVJXKUBCQOZPRENYPXHNAZCUNPVY}
        #   (b)
        {QFPPHEXZFVPWGZWLCCNHIXFBSVCSMTJK}
        #   (c)
            {BKCEMXWMSJUUIESVRRCPXZBBSZRVBFXE}
            #  (d)
        {HCXUWGNLLFYJKSZIXBBUCGANCPIKDRJX}
        #  (e)
    return wrapper_method_name
''',
)


def depth(line):
    return len(line) - len(line.strip())


def indent_fixer(value):
    value = value.replace("\t", " " * 4)
    return value


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

    out = {}

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

                f = io.StringIO()
                with redirect_stdout(f):
                    try:
                        exec(soln, globs)
                        doctest.run_docstring_examples(
                            globs[alias_template_name],
                            globs,
                            verbose=True,
                        )
                    except SyntaxError as e:
                        print(e)
                    except Exception as e:
                        print_exc()
                        print(e)
                    except KeyboardInterrupt:
                        print("TIMEOUT")

                print(soln)

                print("-" * 50)
                value = f.getvalue()
                blocks = [x for x in value.split("*" * 70) if x]
                print(value)
                print(blocks)
                input()
                blocks = [
                    "\n".join(block.strip().split("\n")[-2:])
                    if "Error" in block
                    else block
                    for block in blocks
                ]
                ag = "\n".join(blocks)
                if not ag:
                    ag = "All correct"
                print(ag)
                out[email][template_name] = ag
                # input("continue?")

    finally:
        with open(f"doctests.json", "w+") as f:
            dump(out, f)
