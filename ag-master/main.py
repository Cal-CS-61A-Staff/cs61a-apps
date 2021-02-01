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
db.init_app(app)
db.create_all(app=app)

app.register_blueprint(create_admin_endpoints(db))
app.register_blueprint(create_okpy_endpoints(db))
app.register_blueprint(create_worker_endpoints(db))
app.register_blueprint(create_superadmin_endpoints(db))


if __name__ == "__main__":
    app.run()
