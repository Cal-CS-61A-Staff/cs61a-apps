from flask import Blueprint, abort, redirect, render_template, request, session
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_oauthlib.client import OAuth, OAuthException

from werkzeug import security

from common.course_config import get_course
from common.url_for import url_for
from oh_queue.models import db, User, ConfigEntry

auth = Blueprint("auth", __name__)
auth.config = {}

oauth = OAuth()


@auth.record
def record_params(setup_state: dict):
    """
    Records the parameters required for for the authentication according to a given
    setup state.

    :param setup_state: The setup state containing the app for authentication
    :type setup_state: dict
    """
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
    """
    Loads the user by querying the User database using the given User ID and
    {meth}`common.get_course`.

    :param user_id: The ID for the user being loaded
    :type int:

    :return: The User with the given ID and associated course OR None if no
    match is found.
    """
    return User.query.filter_by(id=user_id, course=get_course()).one_or_none()


@login_manager.unauthorized_handler
def unauthorized():
    """
    Handles an unauthorized access to the OH queue.

    :return: A redirect to the login page.
    """
    session["after_login"] = request.url
    return redirect(url_for("auth.login"))


def authorize_user(user):
    """
    Logs the given user into the OH queue.

    :param user: The User trying to log in
    :type user: User

    :return: A redirect to the index.
    """
    login_user(user, remember=True)
    return redirect(url_for("index"))


def user_from_email(name, email, is_staff):
    """
    Get a User with the given email, or create one.

    :param name: The name of the User to be fetched
    :type name: str
    :param email: The email of the User to be fetched
    :type email: str
    :param is_staff: If the User to be fetched is staff or not
    :type is_staff: bool

    :return: The User with the given email if found in the User database, or a newly
    created User with the given email if not.
    """
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
    """
    Authorizes the current user then redirects to the OH queue.

    :return: A redirect to the index.
    """
    callback = url_for(".authorized", _external=True)
    return auth.ok_auth.authorize(callback=callback)


@auth.route("/assist/", strict_slashes=False)
def try_login():
    """
    Authorizes the current user if the user has not been authenticated yet,
    then redirects to the OH queue.

    :return: A redirect to the index.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    callback = url_for(".authorized", _external=True)
    return auth.ok_auth.authorize(callback=callback)


@auth.route("/login/authorized", strict_slashes=False)
def authorized():
    """
    Authorizes the current user if possible by checking for any authentication
    errors, including: OAuth, Invalid Ok Response, OAuthException, and
    registration Status.

    :return: A redirect to the appropriate link, which may be the OH queue or
    some page indicating the error that occured.
    """
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
        if p["course"]["offering"] == offering:
            if p["role"] != "student":
                is_staff = True
            else:
                is_staff = False
            break
    else:
        if (
            ConfigEntry.query.filter_by(
                course=get_course(), key="only_registered_students"
            )
            .one()
            .value
            == "true"
        ):
            return redirect(
                url_for(
                    "error",
                    message="Only registered students can log in",
                )
            )
    user = user_from_email(name, email, is_staff)
    return authorize_user(user)


@auth.route("/logout/", strict_slashes=False)
def logout():
    """
    Logs the user out of the OH queue.

    :return: A redirect to the index (just logged out).
    """
    logout_user()
    session.pop("access_token", None)
    return redirect(url_for("index"))


@auth.route("/testing-login/", strict_slashes=False)
def testing_login():
    """
    Tests a login. Throws a 404 error if not in debug mode.

    :return: A rendered version of a simple login interface.
    """
    if not auth.debug:
        abort(404)
    callback = url_for(".testing_authorized")
    return render_template("login.html", callback=callback)


@auth.route("/testing-login/authorized", methods=["POST"], strict_slashes=False)
def testing_authorized():
    """
    Tests an authorized login. Throws a 404 error if not in debug mode.

    :return: A redirect to the index upon successful authentication.
    """
    if not auth.debug:
        abort(404)
    form = request.form
    is_staff = form.get("is_staff") == "on"
    user = user_from_email(form["name"], form["email"], is_staff)
    return authorize_user(user)


def init_app(app):
    """
    Initializes the login manager.

    :param app: Flask app instance.
    :type app: Flask
    """
    app.register_blueprint(auth)
    login_manager.init_app(app)
