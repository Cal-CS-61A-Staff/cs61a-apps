from os import getenv

import flask
from flask import redirect
from flask_login import LoginManager, login_user, logout_user

from common.course_config import get_course, get_endpoint
from common.oauth_client import create_oauth_client, get_user, is_staff
from common.url_for import url_for
from models import User, db

dev = getenv("ENV") != "prod"


def create_login_client(app: flask.Flask):
    login_manager = LoginManager()
    login_manager.init_app(app)

    def login():
        user_data = get_user()
        user = User.query.filter_by(email=user_data["email"]).one_or_none()
        if user is None:
            user = User(
                email=user_data["email"], name=user_data["name"], is_staff=False
            )
            db.session.add(user)
        user.name = user_data["name"] or user_data["email"]
        for participation in user_data["participations"]:
            if participation["course"]["offering"] == get_endpoint():
                break
        else:
            if getenv("ENV") == "prod":
                return

        user.is_staff = is_staff("cs61a" if dev else get_course())
        db.session.commit()
        login_user(user)

    create_oauth_client(app, "sections", success_callback=login)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @app.route("/oauth/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))
