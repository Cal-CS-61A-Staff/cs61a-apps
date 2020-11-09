import tempfile
from typing import Dict

from flask import abort, current_app, redirect, safe_join, send_file
from google.cloud import storage
from google.cloud.exceptions import NotFound

from common.url_for import get_host


def get_bucket(app_lookup: Dict[str, str], default_app: str):
    if current_app.debug:
        return f"{default_app}.buckets.cs61a.org"

    host = get_host()
    if ".pr." in host:
        pr, app, *_ = host.split(".")
        pr = int(pr)
        if app not in app_lookup:
            abort(404)
        return f"{app_lookup[app]}-pr{pr}.buckets.cs61a.org"
    else:
        app, *_ = host.split(".")
        if app not in app_lookup:
            abort(404)
        return f"{app_lookup[app]}.buckets.cs61a.org"


def serve_path(bucket, root, path):
    filename = safe_join(root, path)[1:]
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    try:
        if not filename:
            raise NotFound(filename)
        blob = bucket.blob(filename)
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(temp.name, attachment_filename=filename)
    except NotFound:
        if filename.endswith("index.html"):
            abort(404)
        else:
            if path and not path.endswith("/"):
                if bucket.blob(filename + "/" + "index.html").exists():
                    return redirect("/" + filename + "/", 301)
                else:
                    abort(404)
            return serve_path(bucket, root, path + "index.html")
