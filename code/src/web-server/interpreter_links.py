from flask import render_template


def create_interpreter_links(app):
    @app.route("/python")
    @app.route("/python/")
    def python():
        return render_template(
            "index.html",
            initData={
                "loadFile": {"fileName": "untitled.py", "data": ""},
                "startInterpreter": True,
            },
        )

    @app.route("/scheme")
    @app.route("/scheme/")
    def scheme():
        return render_template(
            "index.html",
            initData={
                "loadFile": {"fileName": "untitled.scm", "data": ""},
                "startInterpreter": True,
            },
        )

    @app.route("/sql")
    @app.route("/sql/")
    def sql():
        return render_template(
            "index.html",
            initData={
                "loadFile": {"fileName": "untitled.sql", "data": ""},
                "startInterpreter": True,
            },
        )
