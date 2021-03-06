import json
import re
import os

import pypandoc
from tqdm import tqdm
from os.path import dirname

from examtool.api.utils import list_to_dict, rand_id

VERSION = 2  # increment when backward-incompatible changes are made

html_convert = lambda x: pypandoc.convert_text(x, "html5", "md", ["--mathjax"])
tex_convert = lambda x: pypandoc.convert_text(x, "latex", "md")


class LineBuffer:
    def __init__(self, text, *, src_map=None):
        self.lines = []
        self.src_map = src_map
        self.i = 0
        self.lines = text.strip().split("\n")

    def _pop(self) -> str:
        if self.i == len(self.lines):
            raise SyntaxError("File terminated unexpectedly")
        self.i += 1
        return self.lines[self.i - 1]

    def pop(self) -> str:
        line = self._pop()
        stripped = line.rstrip()
        while stripped.endswith("\\"):
            line = stripped[:-1] + "\n" + self._pop()
            stripped = line.rstrip()
        return line

    def remove_prev(self):
        self.i -= 1
        if self.i < 0:
            self.i = 0
        del self.lines[self.i]

    def empty(self):
        return self.i == len(self.lines)

    def reset(self):
        self.i = 0

    def location(self):
        if self.src_map is None:
            return [self.i - 1, "<string>"]
        else:
            return self.src_map[self.i - 1]


def parse_directive(line):
    if not any(
        line.startswith(f"# {x} ")
        for x in ["BEGIN", "END", "INPUT", "CONFIG", "DEFINE", "IMPORT"]
    ):
        return None, None, None
    tokens = line.split(" ", 3)
    return (
        tokens[1],
        tokens[2] if len(tokens) > 2 else "",
        tokens[3] if len(tokens) > 3 else "",
    )


def process_title(line):
    tokens = line.split(" ")
    point_sec = tokens[-1]
    has_fixed = tokens and tokens[0] == "FIXED"
    if has_fixed:
        tokens = tokens[1:]
        line = " ".join(tokens)
    if not point_sec or point_sec[0] != "[" or point_sec[-1] != "]":
        return line.strip(), has_fixed, None
    try:
        return " ".join(tokens[:-1]).strip(), has_fixed, float(point_sec[1:-1])
    except ValueError:
        return line.strip(), has_fixed, None


class ToParse:
    def __init__(self, text, type):
        self.text = text
        self.type = type

        self.html = None
        self.tex = None


def parse(text):
    return {"text": text, "html": ToParse(text, "html"), "tex": ToParse(text, "tex")}


def parse_define(
    directive, rest, substitutions, substitutions_match, substitution_groups
):
    if directive == "MATCH":
        regex = r"\[(.*)\]\s+\[(.*)\]"
        matches = re.match(regex, rest)
        if not matches or len(matches.groups()) != 2:
            raise SyntaxError("Invalid declaration of DEFINE MATCH")
        directives, replacements = matches.groups()
        directives_list = directives.split(" ")
        replacements_list = replacements.split(" ")
        if len(replacements_list) < len(directives_list):
            raise SyntaxError(
                "DEFINE MATCH must have at least as many replacements as it has directives"
            )
        substitutions_match.append(
            {"directives": directives_list, "replacements": replacements_list}
        )
    elif directive == "GROUP":
        regex = r"(\([^()]+\)\s*)+"
        matches = re.match(regex, rest)
        if not matches:
            raise SyntaxError("Invalid declaration of DEFINE GROUP")
        blocks = re.findall(r"\([^()]+\)", rest)
        if len(blocks) <= 1:
            raise SyntaxError("DEFINE GROUP is incomplete")
        for i, block in enumerate(blocks):
            blocks[i] = tuple(block[1:-1].split(" "))
        if not all(len(block) == len(blocks[0]) for block in blocks):
            raise SyntaxError("DEFINE GROUP blocks must all be of the same length")
        substitution_groups.append(
            {
                "directives": blocks[0],
                "replacements": list_to_dict([list_to_dict(block) for block in blocks]),
            }
        )
    else:
        substitutions[directive] = rest.split(" ")


def parse_input_lines(lines):
    if not lines:
        raise SyntaxError("No INPUT directives found in QUESTION")
    _, directive, rest = parse_directive(lines[0])
    correct_options = []
    if directive == "OPTION" or directive == "SELECT":
        options = []
        existing_options = set()
        for line in lines:
            _, other_directive, rest = parse_directive(line)
            if other_directive != directive:
                raise SyntaxError("Multiple INPUT types found in a single QUESTION")
            fixed = "FIXED "
            is_fixed = False
            if rest.startswith(fixed):
                is_fixed = True
                rest = rest[len(fixed) :]

            correct = "CORRECT "
            is_correct = False
            if rest.startswith(correct):
                is_correct = True
                rest = rest[len(correct) :]

            if is_correct:
                correct_options.append(rest)

            if rest in existing_options:
                raise SyntaxError("Cannot have duplicate INPUT options")
            existing_options.add(rest)

            options.append(parse(rest))
            options[-1]["fixed"] = is_fixed
        return (
            "multiple_choice" if directive == "OPTION" else "select_all",
            options,
            correct_options,
        )
    elif directive in (
        "SHORT_ANSWER",
        "SHORT_CODE_ANSWER",
        "LONG_ANSWER",
        "LONG_CODE_ANSWER",
    ):
        if len(lines) > 1:
            raise SyntaxError(
                "Multiple INPUT directives found for a {}".format(directive)
            )
        if directive == "SHORT_ANSWER":
            return "short_answer", None, None
        elif directive == "SHORT_CODE_ANSWER":
            return "short_code_answer", None, None
        try:
            num_lines = int(rest or "10")
        except TypeError:
            raise SyntaxError("Expected integer as option for {}".format(directive))
        if directive == "LONG_ANSWER":
            return "long_answer", num_lines, None
        elif directive == "LONG_CODE_ANSWER":
            return "long_code_answer", num_lines, None
    raise SyntaxError("Unrecognized directive: {}".format(directive))


def consume_rest_of_solution(buff, end):
    out = []
    while True:
        line = buff.pop()
        mode, directive, rest = parse_directive(line)
        if mode is None:
            out.append(line)
        elif mode == "END":
            if directive == end:
                return parse("\n".join(out))
            else:
                raise SyntaxError(
                    f"Unexpected END ({directive if directive else line}) in SOLUTION"
                )
        else:
            raise SyntaxError(
                f"Unexpected directive ({mode if mode else line}) in SOLUTION"
            )


def consume_rest_of_question(buff):
    contents = []
    input_lines = []
    substitutions = {}
    substitutions_match = []
    substitution_groups = []
    solution = None
    solution_note = None
    config = {}
    while True:
        line = buff.pop()
        mode, directive, rest = parse_directive(line)
        if mode is None:
            if input_lines and line.strip():
                raise SyntaxError("Unexpected content in QUESTION after INPUT")
            elif not input_lines:
                contents.append(line)
        elif mode == "INPUT":
            input_lines.append(line)
        elif mode == "BEGIN":
            if directive == "SOLUTION":
                solution = consume_rest_of_solution(buff, directive)
            elif directive == "NOTE":
                solution_note = consume_rest_of_solution(buff, directive)
            else:
                raise SyntaxError(
                    f"Unexpected BEGIN ({directive if directive else line}) in QUESTION"
                )
        elif mode == "END":
            if directive == "QUESTION":
                question_type, options, option_solutions = parse_input_lines(
                    input_lines
                )

                if option_solutions and solution:
                    raise SyntaxError("Received multiple solutions.")

                return {
                    "id": rand_id(),
                    "type": question_type,
                    "solution": {
                        "solution": solution,
                        "options": option_solutions,
                        "note": solution_note,
                    },
                    **parse("\n".join(contents)),
                    "config": config,
                    "options": options,
                    "substitutions": substitutions,
                    "substitutions_match": substitutions_match,
                    "substitution_groups": substitution_groups,
                }
            else:
                raise SyntaxError(
                    f"Unexpected END {directive if directive else line} in QUESTION"
                )
        elif mode == "DEFINE":
            parse_define(
                directive,
                rest,
                substitutions,
                substitutions_match,
                substitution_groups,
            )
        elif mode == "CONFIG":
            config[directive] = rest
        else:
            raise SyntaxError(
                f"Unexpected directive ({mode if mode else line}) in QUESTION"
            )


def consume_rest_of_group(buff, end):
    group_contents = []
    elements = []
    started_elements = False
    substitutions = {}
    substitutions_match = []
    substitution_groups = []
    pick_some = None
    scramble = False
    inline = False
    while True:
        line = buff.pop()
        mode, directive, rest = parse_directive(line)
        if mode is None:
            if started_elements and line.strip():
                raise SyntaxError("Unexpected text in GROUP after QUESTIONs started")
            elif not started_elements:
                group_contents.append(line)
        elif mode == "BEGIN" and directive == "QUESTION":
            started_elements = True
            title, is_fixed, points = process_title(rest)
            if title:
                raise SyntaxError(
                    "Unexpected arguments passed in BEGIN QUESTION directive"
                )
            question = consume_rest_of_question(buff)
            question["points"] = points
            question["fixed"] = is_fixed
            elements.append(question)
        elif mode == "BEGIN" and directive == "GROUP":
            started_elements = True
            title, is_fixed, points = process_title(rest)
            group = consume_rest_of_group(buff, "GROUP")
            if (title or points) and group["inline"]:
                raise SyntaxError("Cannot create an inline group with title or points")
            group["name"] = title
            group["points"] = points
            group["fixed"] = is_fixed
            elements.append(group)
        elif mode == "END" and directive == end:
            return {
                "type": "group",
                **parse("\n".join(group_contents)),
                "elements": elements,
                "substitutions": substitutions,
                "substitutions_match": substitutions_match,
                "substitution_groups": substitution_groups,
                "pick_some": pick_some,
                "scramble": scramble,
                "inline": inline,
            }
        elif mode == "DEFINE":
            parse_define(
                directive, rest, substitutions, substitutions_match, substitution_groups
            )
        elif mode == "CONFIG":
            if directive == "PICK":
                if pick_some:
                    raise SyntaxError("Multiple CONFIG PICK found in GROUP")
                try:
                    pick_some = int(rest)
                except ValueError:
                    raise SyntaxError("Invalid argument passed to CONFIG PICK")
            elif directive == "SCRAMBLE":
                scramble = True
            elif directive == "INLINE":
                inline = True
            else:
                raise SyntaxError(
                    f"Unexpected CONFIG directive ({directive if directive else line}) in GROUP"
                )
        else:
            raise SyntaxError(f"Unexpected directive ({line}) in GROUP")


def _convert(text, *, path=None):
    groups = []
    public = None
    config = {}
    substitutions = {}
    substitutions_match = []
    substitution_groups = []
    if path is not None:
        buff = load_imports(text, path)
    else:
        buff = LineBuffer(text)

    try:
        while not buff.empty():
            line = buff.pop()
            if not line.strip():
                continue
            mode, directive, rest = parse_directive(line)
            if mode == "CONFIG":
                if directive in [
                    "SCRAMBLE_GROUPS",
                    "SCRAMBLE_QUESTIONS",
                    "SCRAMBLE_OPTIONS",
                ]:
                    config[directive.lower()] = [int(x) for x in rest.split(" ") if x]
                else:
                    raise SyntaxError(
                        "Unexpected CONFIG directive {}".format(directive)
                    )
            elif mode == "BEGIN" and directive in ["GROUP", "PUBLIC"]:
                title, is_fixed, points = process_title(rest)
                group = consume_rest_of_group(buff, directive)
                group["name"] = title
                group["points"] = points
                group["fixed"] = is_fixed
                if (title.strip() or points) and group["inline"]:
                    raise SyntaxError(
                        "Cannot create an inline group with a title or points"
                    )
                if directive == "PUBLIC":
                    if public:
                        raise SyntaxError("Only one PUBLIC block is allowed")
                    if is_fixed:
                        raise SyntaxError("PUBLIC blocks are already FIXED")
                    public = group
                else:
                    groups.append(group)
            elif mode == "DEFINE":
                parse_define(
                    directive,
                    rest,
                    substitutions,
                    substitutions_match,
                    substitution_groups,
                )
            else:
                raise SyntaxError(f"Unexpected directive: {line}")
    except SyntaxError as e:
        line_num, file = buff.location()
        raise SyntaxError(
            "Parse stopped on {}:{} (<merged>:{}) with error {}".format(
                file, line_num, buff.i, e
            )
        )

    return {
        "public": public,
        "groups": groups,
        "config": config,
        "substitutions": substitutions,
        "substitutions_match": substitutions_match,
        "substitution_groups": substitution_groups,
        "version": VERSION,
    }


def pandoc(target, *, draft=False):
    to_parse = []

    def explore(pos):
        if isinstance(pos, ToParse):
            to_parse.append(pos)
        elif isinstance(pos, dict):
            for child in pos.values():
                explore(child)
        elif isinstance(pos, list):
            for child in pos:
                explore(child)

    explore(target)

    DELIMITER = """\n\nDELIMITER\n\n"""

    if draft:
        transpile_target = lambda t: DELIMITER.join(
            x.text for x in to_parse if x.type == t
        )

        html = html_convert(transpile_target("html")).split(html_convert(DELIMITER))
        tex = tex_convert(transpile_target("tex")).split(tex_convert(DELIMITER))

        for x, h in zip(filter(lambda x: x.type == "html", to_parse), html):
            x.html = h

        for x, t in zip(filter(lambda x: x.type == "tex", to_parse), tex):
            x.tex = t
    else:
        for x in tqdm(to_parse):
            x.__dict__[x.type] = (
                html_convert(x.text) if x.type == "html" else tex_convert(x.text)
            )

    def pandoc_dump(obj):
        assert isinstance(obj, ToParse)
        return obj.__dict__[obj.type]

    return json.dumps(target, default=pandoc_dump)


def convert(text, *, path=None, draft=False):
    return json.loads(convert_str(text, path=path, draft=draft))


def convert_str(text, *, path=None, draft=False):
    return pandoc(_convert(text, path=path), draft=draft)


def import_file(filepath: str) -> str:
    if not filepath:
        raise SyntaxError("IMPORT must take in a filepath")
    with open(filepath, "r") as f:
        return f.read()


def load_imports(base_src: str, base_path: str):
    lines = []

    def _load(src: str, path: str):
        for i, line in enumerate(src.split("\n")):
            mode, directive, rest = parse_directive(line)
            if mode == "IMPORT":
                filepath = os.path.join(
                    dirname(path), " ".join([directive, rest]).rstrip()
                )
                try:
                    _load(import_file(filepath), filepath)
                except FileNotFoundError:
                    raise SyntaxError(f"Unable to import {filepath}")
            else:
                lines.append([i + 1, path, line])

    _load(base_src, base_path)

    line_strs = []
    src_map = []
    for line_num, path, line in lines:
        line_strs.append(line)
        src_map.append([line_num, path])

    return LineBuffer("\n".join(line_strs), src_map=src_map)
