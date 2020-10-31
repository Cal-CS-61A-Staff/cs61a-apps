import functools
import os
import re
import threading
from io import BytesIO
from queue import Queue

import requests
from PyPDF2 import pdf as pdf_reader
from PyPDF2.utils import PdfReadError
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, abort

SITE_DOMAIN = "https://cs61a.org"
SEARCH_DOMAIN = "https://search-worker.apps.cs61a.org"

PIAZZA_TEMPLATE = "https://piazza.com/class/{}?cid={}"

GOOGLE_DOC_PREFIX = "https://docs.google.com/document/"
GOOGLE_DOC_EXPORT_TEMPLATE = (
    "https://docs.google.com/document/u/1/export?format=txt&id={}"
)

CLIENT_NAME = "piazza-search-indexer"
AUTH_SECRET = os.getenv("AUTH_SECRET")  # needed for 61A Auth
ACCESS_SECRET = os.getenv("ACCESS_SECRET")  # users need this to access it
WORKER_SECRET = os.getenv(
    "WORKER_SECRET"
)  # needed to communicate with the search-worker

app = Flask(__name__, static_folder="")


@app.route("/search.js")
def search_js():
    return app.send_static_file("search.js")


@app.route("/search.css")
def search_css():
    return app.send_static_file("search.css")


def do(path, data={}):
    requests.post(
        "{}/{}".format(SEARCH_DOMAIN, path), json={**data, "secret": WORKER_SECRET}
    ).raise_for_status()


def secure(route):
    @functools.wraps(route)
    def wrapped(*args, **kwargs):
        if request.json["secret"] != ACCESS_SECRET:
            abort(401)
        return route(*args, **kwargs)

    return wrapped


def make_worker_group():
    queue = Queue()

    def handler():
        while not queue.empty():
            f, args, kwargs = queue.get()
            f(*args, **kwargs)
            queue.task_done()

    def worker(f):
        active_thread = None

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            nonlocal active_thread
            queue.put([f, args, kwargs])
            if not active_thread or not active_thread.is_alive():
                active_thread = threading.Thread(target=handler)
                active_thread.start()

        return wrapped

    return worker


piazza_worker = make_worker_group()
resource_worker = make_worker_group()


@piazza_worker
def upload_piazza():
    print("Starting to scrape Piazza")

    feed = requests.post(
        "https://auth.apps.cs61a.org/piazza/get_feed",
        json={
            "limit": 10000,
            "client_name": CLIENT_NAME,
            "secret": AUTH_SECRET,
            "staff": False,
        },
    ).json()["feed"]

    course_id = requests.post(
        "https://auth.apps.cs61a.org/piazza/course_id",
        json={
            "client_name": CLIENT_NAME,
            "secret": AUTH_SECRET,
        },
    ).json()

    do("clear/piazza")

    posts = []
    for post in feed:
        if post["status"] == "private":
            continue

        i = post["nr"]
        tags = post["folders"]
        subject = post["subject"]
        content = post["content_snipet"]
        name = "@{} {}".format(i, subject)
        link = PIAZZA_TEMPLATE.format(course_id, i)

        indexedPost = {
            "tags": tags,
            "type": "Piazza Post",
            "subject": subject,
            "content": content,
            "name": name,
            "link": link,
            "id": i,
        }

        posts.append(indexedPost)

    do("insert/piazza", {"data": posts})
    print("Piazza scraping completed")


@resource_worker
def scrape_and_upload_resources(resources):
    print("Starting to scrape resource batch")
    buffer = []
    buffer_length = 0

    resource: dict
    for resource in resources:
        content = resource.get("content", [])
        html_content = resource.get("html_content", [])
        pdf_content = resource.get("pdf_content", [])
        for link in resource["links"]:
            force_txt = False

            if link.startswith(SITE_DOMAIN):
                # data already in "*_content" attrs
                continue

            if link.startswith(GOOGLE_DOC_PREFIX):
                fmt = re.compile(r"/d/(.*)/")
                doc_id = fmt.search(link).group(1)
                link = GOOGLE_DOC_EXPORT_TEMPLATE.format(doc_id)
                force_txt = True

            try:
                if force_txt:
                    content.append(requests.get(link).text)
                elif link.endswith(".html"):
                    html_content.append(requests.get(link).text)
                elif link.endswith(".pdf"):
                    pdf_content.append(requests.get(link).content)
            except requests.exceptions.ConnectionError:
                continue

        for html_data in html_content:
            html_soup = BeautifulSoup(html_data, "html.parser")
            for p in html_soup.find_all("p"):
                content.append(p.get_text())

        for pdf in pdf_content:
            try:
                reader = pdf_reader.PdfFileReader(BytesIO(pdf))
                for page in range(reader.getNumPages()):
                    content.append(reader.getPage(page).extractText())
            except PdfReadError:
                continue

        resource.pop("html_content", None)
        resource.pop("pdf_content", None)
        resource.pop("links", None)

        buffer_length += sum(map(len, content))
        buffer.append(resource)

        if buffer_length > 10 ** 5 or resource == resources[-1]:
            do("insert/resources", {"resources": buffer})
            buffer = []
            buffer_length = 0

    print("Resource scraping completed")


@resource_worker
def clear_worker():
    do("clear/resources")


@app.route("/api/index_piazza", methods=["POST"])
@secure
def index_piazza():
    upload_piazza()
    return jsonify({"success": True})


@app.route("/api/clear_resources", methods=["POST"])
@secure
def clear_resources():
    clear_worker()
    return jsonify({"success": True})


@app.route("/api/upload_resources", methods=["POST"])
@secure
def upload_resources():
    resources = request.json["resources"]
    scrape_and_upload_resources(resources)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run()
