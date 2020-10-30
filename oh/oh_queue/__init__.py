import logging

# Flask-related stuff
from datetime import datetime, timedelta

from flask import Flask
from flask_compress import Compress

from common.jobs import job
from oh_queue import auth, assets
from oh_queue.models import (
    Group,
    GroupAttendance,
    GroupAttendanceStatus,
    GroupStatus,
    db,
    TicketStatus,
)
from oh_queue.slack import worker

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


@job(app, "slack_notify")
def slack_poll():
    worker(app)


@job(app, "clear_inactive_groups")
def clear_inactive_groups():
    active_groups = Group.query.filter_by(group_status=GroupStatus.active).all()
    for group in active_groups:
        for attendance in group.attendees:
            if (
                attendance.group_attendance_status == GroupAttendanceStatus.present
                and attendance.user.heartbeat_time
                and attendance.user.heartbeat_time
                > datetime.utcnow() - timedelta(minutes=3)
            ):
                break
        else:
            oh_queue.views.delete_group_worker(group, emit=False)
    db.session.commit()


# Caching
@app.after_request
def after_request(response):
    cache_control = "no-store"
    response.headers.add("Cache-Control", cache_control)
    return response


Compress(app)
