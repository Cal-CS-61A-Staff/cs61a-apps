import logging

# Flask-related stuff
from flask import Flask, request

from oh_queue import auth, assets
from oh_queue.models import db, TicketStatus

logging.basicConfig(level=logging.INFO)

# Initialize the application
app = Flask(__name__)
app.config.from_object("config")
app.url_map.strict_slashes = False

app.jinja_env.globals.update(
    {"TicketStatus": TicketStatus, "assets_env": assets.assets_env}
)

db.init_app(app)
auth.init_app(app)

# Import views
import oh_queue.views

# Start slack cron job
# import oh_queue.slack
# oh_queue.slack.start_flask_job(app)

# Caching
@app.after_request
def after_request(response):
    cache_control = "no-store"
    response.headers.add("Cache-Control", cache_control)
    return response
