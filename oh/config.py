import os

from common.db import database_url
from common.rpc.secrets import get_secret

basedir = os.path.abspath(os.path.dirname(__file__))

ENV = os.getenv("ENV", "dev")

if ENV == "DEV_ON_PROD":
    ENV = "dev"

if ENV == "dev":
    DEBUG = True
    SECRET_KEY = "dev"
else:
    DEBUG = False
    SECRET_KEY = get_secret(secret_name="SESSION_COOKIE_SECRET")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

SQLALCHEMY_DATABASE_URI = database_url

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
