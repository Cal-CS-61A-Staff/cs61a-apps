from json import dumps
from multiprocessing import Process, Queue

import black
import requests
from flask import jsonify, request

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
