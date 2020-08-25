from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from login import create_login_client
from models import create_models, db
from state import create_state_client

app = Flask(
    __name__, static_url_path="", static_folder="static", template_folder="static"
)


if __name__ == "__main__":
    app.debug = True


create_state_client(app)
create_login_client(app)

create_models(app)
db.init_app(app)
db.create_all(app=app)

if __name__ == "__main__":
    DebugToolbarExtension(app)
    app.run(host="127.0.0.1", port=8000, debug=True)
