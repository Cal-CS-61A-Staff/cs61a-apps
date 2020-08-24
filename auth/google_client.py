import json

from flask import request, redirect

from auth_utils import key_secure, course_oauth_secure
from common.db import connect_db
from google_api import load_document, load_sheet, dump_sheet
from common.rpc.auth import read_document, read_spreadsheet, write_spreadsheet


def init_db():
    with connect_db() as db:
        db(
            "CREATE TABLE IF NOT EXISTS auth_json (email varchar(256), data LONGBLOB, course varchar(128))"
        )


init_db()


def create_google_client(app):
    def google_help(course):
        with connect_db() as db:
            email = db(
                "SELECT email FROM auth_json WHERE course=(%s)", [course]
            ).fetchone()
            email = email[0] if email else ""
        return f"""
        <h3> Google Service Account </h3>
        Email address: <a href="mailto:{email}">{email}</a>
        <p>
        Share relevant Google Documents / Sheets with the above email account.
        <p>
        To configure, go to <a href="/google/{course}/config">Google Config</a>.
        """

    app.help_info.add(google_help)

    @read_document.bind(app)
    @key_secure
    def handle_read_document(course, url=None, doc_id=None):
        return load_document(url=url, doc_id=doc_id, course=course)

    @read_spreadsheet.bind(app)
    @key_secure
    def handle_read_spreadsheet(course, sheet_name, url=None, doc_id=None):
        return load_sheet(url=url, doc_id=doc_id, sheet_name=sheet_name, course=course)

    @write_spreadsheet.bind(app)
    @key_secure
    def handle_write_spreadsheet(course, sheet_name, content, url=None, doc_id=None):
        return dump_sheet(
            url=url,
            doc_id=doc_id,
            sheet_name=sheet_name,
            content=content,
            course=course,
        )

    @app.route("/google/<course>/config", methods=["GET"])
    @course_oauth_secure()
    def google_config(course):
        return """
            Upload Google service worker JSON. This may break existing Google integrations!
            <form action="/google/{}/set_auth_json" method="post" enctype="multipart/form-data">
                <input name="data" type="file">
                <input type="submit">
            </form>
        """.format(
            course
        )

    @app.route("/google/<course>/set_auth_json", methods=["POST"])
    @course_oauth_secure()
    def set_auth_json(course):
        f = request.files["data"]
        f.seek(0)
        data = f.read().decode("utf-8")
        if not data.strip():
            return "Upload failed, file is blank", 403
        parsed = json.loads(data)
        email = parsed["client_email"]
        with connect_db() as db:
            db("DELETE FROM auth_json WHERE course=(%s)", [course])
            db("INSERT INTO auth_json VALUES (%s, %s, %s)", [email, data, course])
        return redirect("/")
