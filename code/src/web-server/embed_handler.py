from flask import render_template, request


def create_embed_handler(app):
    @app.route("/embed")
    def serve_embed():
        data = {
            "fileName": request.args["fileName"],
            "data": request.args["data"],
            "shareRef": None,
            "srcOrigin": request.args["srcOrigin"],
        }

        return render_template("index.html", initData={"loadFile": data})
