import hashlib
import http.server
import os
import pickle
import requests
import time
from urllib.parse import urlencode, urlparse, parse_qsl
import webbrowser

from contextlib import contextmanager
import sys

import logging
import traceback
import ssl

from flask import session, g, redirect

from common.oauth_client import create_oauth_client, is_staff
from common.rpc.secrets import get_secret
from common.url_for import url_for
from common.db import connect_db

log = logging.getLogger(__name__)

CLIENT_ID = 'grade-display-exports'
CLIENT_SECRET = get_secret(secret_name="OKPY_OAUTH_SECRET")

OAUTH_SCOPE = 'all'

TIMEOUT = 10

INFO_ENDPOINT = '/api/v3/user/'
TOKEN_ENDPOINT = '/oauth/token'

# ---------------------

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS tokens (
    access_token VARCHAR(128),
    expires_at INTEGER,
    refresh_token VARCHAR(128)
)
"""
    )

create_oauth_client(app, 'grade-display-exports')

def make_token_post(server, data):
    """Try getting an access token from the server. If successful, returns the
    JSON response. If unsuccessful, raises an OAuthException.
    """
    try:
        response = requests.post(server + TOKEN_ENDPOINT, data=data, timeout=TIMEOUT)
        body = response.json()
    except Exception as e:
        log.warning('Other error when exchanging code', exc_info=True)
        raise OAuthException(
            error='Authentication Failed',
            error_description=str(e))
    if 'error' in body:
        log.error(body)
        raise OAuthException(
            error=body.get('error', 'Unknown Error'),
            error_description = body.get('error_description', ''))
    return body

def make_refresh_post(refresh_token):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    info = make_token_post(server_url(), data)
    return info['access_token'], int(info['expires_in'])

def get_storage():
    with connect_db() as db:
        token = db(
            "SELECT * FROM tokens"
        ).fetchone()
        
        if token:
            access_token = token[0]
            expires_at = token[1]
            refresh_token = token[2]

            return access_token, expires_at, refresh_token
    return None, 0, None

def update_storage(data):
    access_token, expires_in, refresh_token = data.get("access_token"), data.get("expires_in"), data.get("refresh_token")
    if not (access_token and expires_in and refresh_token):
        raise AuthenticationException(
            "Authentication failed and returned an empty token.")

    cur_time = int(time.time())

    with connect_db() as db:
        db("TRUNCATE TABLE tokens")
        db(
            "INSERT INTO tokens (access_token, expires_at, refresh_token) VALUES (%s, %s, %s)",
            [access_token, cur_time + expires_in, refresh_token],
        )

def refresh_local_token():
    cur_time = int(time.time())
    access_token, expires_at, refresh_token = get_storage()
    if cur_time < expires_at - 10:
        return access_token
    access_token, expires_in = make_refresh_post(refresh_token)
    if not (access_token and expires_in):
        raise AuthenticationException(
            "Authentication failed and returned an empty token.")

    update_storage({
        "access_token": access_token, 
        "expires_in": expires_in, 
        "refresh_token": refresh_token
    })

    return access_token

def server_url():
    return "https://okpy.org"

def authenticate(app):
    """Returns an OAuth token that can be passed to the server for
    identification. If FORCE is False, it will attempt to use a cached token
    or refresh the OAuth token. If NOINTERACT is true, it will return None
    rather than prompting the user.
    """
    try:
        access_token = refresh_local_token()
        session["access_token"] = access_token
    except Exception:
        print("Performing authentication.")
    
    if not is_staff("cs61a"):
        g.cache_token = update_storage
        return redirect(url_for("login"))
    
    return "Authorized!"

def get_info(access_token):
    response = requests.get(
        server_url() + INFO_ENDPOINT,
        headers={'Authorization': 'Bearer {}'.format(access_token)},
        timeout=5)
    response.raise_for_status()
    return response.json()['data']

def display_student_email(access_token):
    try:
        email = get_info(access_token)['email']
        print('Successfully logged in as', email)
        return email
    except Exception:  # Do not catch KeyboardInterrupts
        log.debug("Did not obtain email", exc_info=True)
        return None

class OkException(Exception):
    """Base exception class for OK."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug('Exception raised: {}'.format(type(self).__name__))
        log.debug('python version: {}'.format(sys.version_info))

class AuthenticationException(OkException):
    """Exceptions related to authentication."""

class OAuthException(AuthenticationException):
    def __init__(self, error='', error_description=''):
        super().__init__()
        self.error = error
        self.error_description = error_description
