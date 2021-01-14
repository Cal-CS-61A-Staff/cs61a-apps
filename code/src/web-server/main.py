from flask import Flask, render_template, send_from_directory

from constants import STATIC_FOLDER
from embed_handler import create_embed_handler

from interpreter_links import create_interpreter_links
from language_apis import create_language_apis
from oauth_client import create_oauth_client
from ok_server_interface import create_ok_server_interface
from preloaded_tables import create_preloaded_tables
from refresher import create_refresher
from shortlink_generator import create_shortlink_generator
from shortlink_handler import create_shortlink_handler
from stored_files import create_stored_files

app = Flask(__name__, template_folder=STATIC_FOLDER)

if __name__ == "__main__":
    app.debug = True


@app.route("/")
def root():
    return render_template("index.html", initData={})


@app.route("/service-worker.js")
def serviceworker():
    return send_from_directory(STATIC_FOLDER, "service-worker.js")


create_shortlink_handler(app)
create_oauth_client(app)
create_refresher(app)
create_shortlink_generator(app)
create_interpreter_links(app)
create_language_apis(app)
create_preloaded_tables(app)
create_stored_files(app)
create_ok_server_interface(app)
create_embed_handler(app)


if __name__ == "__main__":
    app.run(debug=True)
