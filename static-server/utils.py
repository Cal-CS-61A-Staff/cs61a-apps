import tempfile
from os import getenv
from typing import Dict
from urllib.parse import urlparse, urlunparse

from flask import abort, current_app, redirect, request, safe_join, send_file
from google.cloud import storage
from google.cloud.exceptions import NotFound

from common.url_for import get_host


def get_bucket(app_lookup: Dict[str, str], default_app: str = None):
    if current_app.debug:
        return f"{default_app}.buckets.cs61a.org"

    host = get_host()
    if ".pr." in host:
        pr, app, *_ = host.split(".")
        pr = int(pr)
        if app not in app_lookup:
            abort(404)
        bucket = f"{app_lookup[app]}-pr{pr}.buckets.cs61a.org"
        try:
            storage.Client().get_bucket(bucket)
            return bucket
        except NotFound:
            pass
    else:
        app, *_ = host.split(".")
        if app not in app_lookup:
            abort(404)
    return f"{app_lookup[app]}.buckets.cs61a.org"


def serve_path(bucket, root, path, *, path_404="404.html"):
    filename = safe_join(root, path)[1:]
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    try:
        if not filename:
            raise NotFound(filename)
        blob = bucket.blob(filename)
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            mimetype = None
            if filename.endswith(".scm"):
                mimetype = "text/x-scheme"
            return send_file(temp.name, attachment_filename=filename, mimetype=mimetype)
    except NotFound:
        if filename == path_404:
            abort(404)
        elif filename.endswith("index.html"):
            return serve_path(bucket, root, path_404), 404
        else:
            if path and not path.endswith("/"):
                if bucket.blob(filename + "/" + "index.html").exists():
                    target = urlunparse(
                        (
                            "https" if getenv("ENV") == "prod" else "http",
                            get_host(),
                            "/" + path + "/",
                            urlparse(request.url).params,
                            urlparse(request.url).query,
                            urlparse(request.url).fragment,
                        )
                    )
                    return redirect(target, 301)
                else:
                    return serve_path(bucket, root, path_404), 404
            return serve_path(bucket, root, path + "index.html")
