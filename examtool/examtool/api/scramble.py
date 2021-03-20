import random

from examtool.api.utils import dict_to_list


def scramble(email, exam, *, keep_data=False):
    random.seed(email)

    version = exam.get("version", 1)

    def scramble_group(group, substitutions, config, depth):
        group_substitutions = select_substitutions(group)
        substitute(
            group,
            [*substitutions, group_substitutions],
            ["name", "html", "tex", "text"],
        )

        def scramble_group_children():
            if depth in config["scramble_groups"] or group.get("scramble"):
                scramble_keep_fixed(get_elements(group))
            if group.get("pick_some"):
                get_elements(group)[:] = random.sample(
                    get_elements(group), group["pick_some"]
                )

        if version == 1:
            scramble_group_children()

        elements = []
        for element in get_elements(group):
            if element.get("type") == "group":
                elements.extend(
                    scramble_group(
                        element,
                        [*substitutions, group_substitutions],
                        config,
                        depth + 1,
                    )
                )
            else:
                elements.append(
                    scramble_question(
                        element, [*substitutions, group_substitutions], config
                    )
                )
        get_elements(group)[:] = elements

        if version > 1:
            scramble_group_children()

        if is_compressible_group(group):
            text, html, tex = group["text"], group["html"], group["tex"]
            elements = get_elements(group)
            out = []
            for element in elements:
                if element.get("type") != "group" and depth == 1:
                    return [group]
                element["text"] = text + "\n" + element["text"]
                element["html"] = html + "\n" + element["html"]
                element["tex"] = tex + "\n" + element["tex"]
                out.append(element)
            return out

        return [group]

    def scramble_question(question, substitutions, config):
        question_substitutions = select_substitutions(question)
        substitute(
            question,
            [question_substitutions, *substitutions],
            ["html", "tex", "text", "template"],
        )
        if isinstance(question["options"], list):
            if "scramble_options" in config:
                scramble_keep_fixed(question["options"])
            for option in question["options"]:
                substitute(
                    option,
                    [*substitutions, question_substitutions],
                    ["html", "tex", "text"],
                )

        if keep_data and "solution" in question:
            solution = question["solution"]
            if solution.get("solution") is not None:
                substitute(
                    solution["solution"],
                    [question_substitutions, *substitutions],
                    ["html", "tex", "text"],
                    store=False,
                )
            else:
                options = solution["options"]
                if options:
                    substitute(
                        options,
                        [question_substitutions, *substitutions],
                        range(len(options)),
                        store=False,
                    )
        else:
            question.pop("solution", None)

        return question

    def substitute(target: dict, list_substitutions, attrs, *, store=True):
        merged = {}
        for substitutions in list_substitutions:
            merged = {**merged, **substitutions}
            for attr in attrs:
                if attr not in target:
                    continue
                for k, v in substitutions.items():
                    target[attr] = target[attr].replace(k, v)
                    if k.title() != k:
                        target[attr] = target[attr].replace(k.title(), v.title())
                    if latex_escape(k) != k:
                        target[attr] = target[attr].replace(
                            latex_escape(k), latex_escape(v)
                        )
        if store:
            if keep_data:
                target["substitutions"] = merged
            else:
                target.pop("substitutions", None)
                target.pop("substitution_groups", None)
                target.pop("substitutions_match", None)

    def scramble_keep_fixed(objects):
        if keep_data:
            for i, object in enumerate(objects):
                object["index"] = i
        movable_object_pos = []
        movable_object_values = []
        for i, object in enumerate(objects):
            if not object.get("fixed"):
                movable_object_pos.append(i)
                movable_object_values.append(object)
        random.shuffle(movable_object_values)
        for i, object in zip(movable_object_pos, movable_object_values):
            objects[i] = object

    global_substitutions = select_substitutions(exam)
    exam["config"]["scramble_groups"] = exam["config"].get(
        "scramble_groups", [-1]
    ) or range(100)
    if 0 in exam["config"]["scramble_groups"]:
        scramble_keep_fixed(exam["groups"])
    groups = []
    for group in exam["groups"]:
        groups.extend(scramble_group(group, [global_substitutions], exam["config"], 1))

    exam["groups"] = groups
    exam.pop("config", None)
    exam.pop("substitutions", None)
    exam.pop("substitution_groups", None)
    exam.pop("substitutions_match", None)

    if exam.get("watermark"):
        exam["watermark"]["value"] = random.randrange(2 ** 20)

    return exam


def get_elements(group):
    return group.get("elements") if "elements" in group else group.get("questions")


def select_substitutions(element):
    substitutions = select_regular(element.get("substitutions", {}))
    substitutions.update(select_no_replace(element.get("substitutions_match", [])))
    substitutions.update(select_group(element.get("substitution_groups", [])))
    substitutions.update(select_ranges(element.get("substitution_ranges", {})))
    return substitutions


def select_regular(substitutions):
    out = {}
    # DEFINE
    for k, v in sorted(substitutions.items()):
        out[k] = random.choice(v)
    return out


def select_no_replace(substitutions_match):
    out = {}
    # DEFINE MATCH
    for item in substitutions_match:
        k = item["directives"]
        v = item["replacements"]
        values = v.copy()
        for choice in k:
            c = random.choice(values)
            values.remove(c)
            out[choice] = c
    return out


def select_group(substitution_groups):
    out = {}
    # DEFINE GROUP
    for blocks in substitution_groups:
        k = blocks["directives"]
        v = dict_to_list(blocks["replacements"])
        v = dict_to_list(random.choice(v))
        assert len(k) == len(v)
        for k0, v0 in zip(k, v):
            out[k0] = v0
    return out


def select_ranges(substitution_ranges):
    out = {}
    # DEFINE RANGE
    for k, [low, high] in sorted(substitution_ranges.items()):
        out[k] = str(random.randrange(low, high))
    return out


def is_compressible_group(group):
    return (
        group.get("pick_some") == 1
        and not group["name"].strip()
        and group["points"] is None
    ) or group.get("inline")


def latex_escape(text):
    return text.replace("_", r"\_")
