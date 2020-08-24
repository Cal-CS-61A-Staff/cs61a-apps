import os

from common.rpc.secrets import get_secret

basedir = os.path.abspath(os.path.dirname(__file__))

ENV = os.getenv("ENV", "dev")

if ENV in ("dev", "staging"):
    DEBUG = True
elif ENV == "prod":
    DEBUG = False

if ENV == "dev":
    SECRET_KEY = "dev"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db")
    ).replace("mysql://", "mysql+pymysql://")
else:
    SECRET_KEY = get_secret(secret_name="SESSION_COOKIE_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

SQLALCHEMY_TRACK_MODIFICATIONS = False
DATABASE_CONNECT_OPTIONS = {}

LOCAL_TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")

AUTH_KEY = "oh-queue-staging" if os.getenv("IN_STAGING") else "oh-queue"

if ENV == "dev":
    AUTH_SECRET = ""
    OK_KEY = "local-dev-email"
    OK_SECRET = "KH0mvknMUWT5w3U7zvz6wsUQZoy6UmQ"
else:
    AUTH_SECRET = get_secret(secret_name="AUTH_SECRET")
    OK_KEY = "oh-queue"
    OK_SECRET = get_secret(secret_name="OKPY_OAUTH_SECRET")

OK_SERVER_URL = os.getenv("OK_DEPLOYMENT", "https://okpy.org")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
