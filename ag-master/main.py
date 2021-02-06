from flask import Flask
from common.oauth_client import create_oauth_client

from models import create_models, db
from admin import create_admin_endpoints
from okpy import create_okpy_endpoints
from worker import create_worker_endpoints
from superadmin import create_superadmin_endpoints

app = Flask(__name__)
create_oauth_client(app, "61a-autograder")

create_models(app)

create_admin_endpoints(app)
create_okpy_endpoints(app)
create_worker_endpoints(app)
create_superadmin_endpoints(app)


@app.before_first_request
def init_db():
    db.init_app(app)
    db.create_all(app=app)


@app.route("/")
def index():
    return ""


if __name__ == "__main__":
    app.run()
