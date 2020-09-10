from flask import Blueprint, abort, redirect, render_template, request, session
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_oauthlib.client import OAuth, OAuthException

from werkzeug import security

from common.course_config import get_course
from common.url_for import url_for
from oh_queue.models import db, User

auth = Blueprint("auth", __name__)
auth.config = {}

oauth = OAuth()


@auth.record
def record_params(setup_state):
    app = setup_state.app
    server_url = app.config.get("OK_SERVER_URL")
    auth.ok_auth = oauth.remote_app(
        "ok-server",
        consumer_key=app.config.get("OK_KEY"),
        consumer_secret=app.config.get("OK_SECRET"),
        request_token_params={"scope": "email", "state": lambda: security.gen_salt(10)},
        base_url=server_url + "/api/v3/",
        request_token_url=None,
        access_token_method="POST",
        access_token_url=server_url + "/oauth/token",
        authorize_url=server_url + "/oauth/authorize",
    )
    auth.debug = app.config.get("DEBUG")

    @auth.ok_auth.tokengetter
    def get_access_token(token=None):
        return session.get("access_token")


login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id, course=get_course()).one_or_none()


@login_manager.unauthorized_handler
def unauthorized():
    session["after_login"] = request.url
    return redirect(url_for("auth.login"))


def authorize_user(user):
    login_user(user, remember=True)
    return redirect(url_for("index"))


def user_from_email(name, email, is_staff):
    """Get a User with the given email, or create one."""
    from common.course_config import get_course

    user = User.query.filter_by(email=email, course=get_course()).one_or_none()
    if not user:
        user = User(name=name, email=email, course=get_course(), is_staff=is_staff)
    else:
        user.name = name
        user.is_staff = is_staff
        user.course = get_course()
    db.session.add(user)
    db.session.commit()
    return user


@auth.route("/login/", strict_slashes=False)
def login():
    callback = url_for(".authorized", _external=True)
    return auth.ok_auth.authorize(callback=callback)


@auth.route("/assist/", strict_slashes=False)
def try_login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    callback = url_for(".authorized", _external=True)
    return auth.ok_auth.authorize(callback=callback)


@auth.route("/login/authorized", strict_slashes=False)
def authorized():
    from common.course_config import get_endpoint

    message = request.args.get("error")
    if message:
        message = "Ok OAuth error: %s" % (message)
        return redirect(url_for("error", message=message))
    try:
        auth_resp = auth.ok_auth.authorized_response()
        if auth_resp is None:
            message = "Invalid Ok response: %s" % (message)
            return redirect(url_for("error", message=message))
    except OAuthException as ex:
        message = str(ex)
        return redirect(url_for("error", message=message))
    token = auth_resp["access_token"]
    session["access_token"] = (token, "")  # (access_token, secret)
    info = auth.ok_auth.get("user").data["data"]
    email = info["email"]
    name = info["name"]
    if not name:
        name = email
    if ", " in name:
        last, first = name.split(", ")
        name = first + " " + last
    is_staff = False
    offering = get_endpoint()
    for p in info["participations"]:
        if p["course"]["offering"] == offering and p["role"] != "student":
            is_staff = True
    user = user_from_email(name, email, is_staff)
    return authorize_user(user)


@auth.route("/logout/", strict_slashes=False)
def logout():
    logout_user()
    session.pop("access_token", None)
    return redirect(url_for("index"))


@auth.route("/testing-login/", strict_slashes=False)
def testing_login():
    if not auth.debug:
        abort(404)
    callback = url_for(".testing_authorized")
    return render_template("login.html", callback=callback)


@auth.route("/testing-login/authorized", methods=["POST"], strict_slashes=False)
def testing_authorized():
    if not auth.debug:
        abort(404)
    form = request.form
    is_staff = form.get("is_staff") == "on"
    user = user_from_email(form["name"], form["email"], is_staff)
    return authorize_user(user)


def init_app(app):
    app.register_blueprint(auth)
    login_manager.init_app(app)
