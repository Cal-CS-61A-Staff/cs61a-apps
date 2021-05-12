import re
from json import dumps
from multiprocessing import Process, Queue

import black
import requests
from flask import jsonify, request
from lark import Lark, LarkError, Token, Tree, UnexpectedEOF

from IGNORE_scheme_debug import (
    Buffer,
    SchemeError,
    debug_eval,
    scheme_read,
    tokenize_lines,
)
from formatter import scm_reformat


def create_language_apis(app):
    # python
    @app.route("/api/pytutor", methods=["POST"])
    def pytutor_proxy():
        data = {
            "user_script": request.form["code"],
            # "options_json": r'{"cumulative_mode":true,"heap_primitives":false}',
        }
        if "options_json" in request.form:
            data["options_json"] = request.form["options_json"]
        response = requests.post(
            "http://pythontutor.com/web_exec_py3.py",
            data=data,
        )
        return response.text

    @app.route("/api/black", methods=["POST"])
    def black_proxy():
        try:
            return jsonify(
                {
                    "success": True,
                    "code": black.format_str(
                        request.form["code"], mode=black.FileMode()
                    )
                    + "\n",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": repr(e)})

    # scheme
    @app.route("/api/scm_debug", methods=["POST"])
    def scm_debug():
        code = request.form["code"]
        q = Queue()
        p = Process(target=scm_worker, args=(code, q))
        p.start()
        p.join(10)
        if not q.empty():
            return jsonify(q.get())

    @app.route("/api/scm_format", methods=["POST"])
    def scm_format():
        try:
            return jsonify(
                {"success": True, "code": scm_reformat(request.form["code"])}
            )
        except Exception as e:
            return jsonify({"success": False, "error": repr(e)})

    @app.route("/api/lark_run", methods=["POST"])
    def lark_run():
        grammar = request.form["grammar"]
        import_regex = r"%import common\.([a-zA-Z]*)"

        imports = [match.group(1) for match in re.finditer(import_regex, grammar)]
        grammar = re.sub(r"%import common\.[a-zA-Z]*", "", grammar)

        if "%import" in grammar:
            return jsonify(dict(error="Arbitrary %imports are not supported"))

        for terminal in imports:
            grammar += f"""
            %import common.{terminal}
            """
        text = request.form.get("text", None)
        try:
            parser = Lark(grammar, start="start")
        except LarkError as e:
            return jsonify(dict(error=str(e)))

        if text is None:
            return jsonify(dict(success=True))

        try:
            parse_tree = parser.parse(text)
        except UnexpectedEOF as e:
            return jsonify(
                dict(
                    error=str(e)
                    + "[Hint: use the .begin and .end commands to input multiline strings]\n"
                )
            )
        except LarkError as e:
            return jsonify(dict(error=str(e)))

        def export(node):
            if isinstance(node, Tree):
                return [
                    node.data,
                    [export(child) for child in node.children],
                ]
            elif isinstance(node, Token):
                return [repr(node.value)]
            else:
                return [repr(node)]

        return jsonify(
            success=True, parsed=export(parse_tree), repr=parse_tree.pretty()
        )


def scm_worker(code, queue):
    try:
        buff = Buffer(tokenize_lines(code.split("\n")))
        exprs = []
        while buff.current():
            exprs.append(scheme_read(buff))
        out = debug_eval(exprs)
    except (SyntaxError, SchemeError) as err:
        queue.put(dumps(dict(error=str(err))))
    except:
        queue.put(dumps(dict(error="An internal error occurred.")))
        raise
    else:
        queue.put(out)
