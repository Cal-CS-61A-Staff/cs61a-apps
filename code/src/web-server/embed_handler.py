from flask import render_template, request


def create_embed_handler(app):
    @app.route("/embed")
    @app.route("/embed2")
    def serve_embed():
        data = {
            "fileName": request.args["fileName"],
            "data": request.args["data"],
            "shareRef": None,
        }

        return render_template(
            "index.html",
            initData={
                "loadFile": data,
                "srcOrigin": request.args["srcOrigin"],
            },
        )
