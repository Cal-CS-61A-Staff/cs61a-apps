import re
from io import BytesIO

import requests
from PyPDF2 import pdf as pdf_reader
from PyPDF2.utils import PdfReadError
from bs4 import BeautifulSoup
from flask import Flask

from common.rpc.auth import PiazzaNetwork, piazza_course_id
from common.rpc.indexer import clear_resources, index_piazza, upload_resources
from common.rpc.secrets import get_secret, only

SITE_DOMAIN = "https://cs61a.org"
SEARCH_DOMAIN = "https://search-worker.app.cs61a.org"

PIAZZA_TEMPLATE = "https://piazza.com/class/{}?cid={}"

GOOGLE_DOC_PREFIX = "https://docs.google.com/document/"
GOOGLE_DOC_EXPORT_TEMPLATE = (
    "https://docs.google.com/document/u/1/export?format=txt&id={}"
)


app = Flask(__name__, static_folder="")


@app.route("/search.js")
def search_js():
    return app.send_static_file("search.js")


@app.route("/search.css")
def search_css():
    return app.send_static_file("search.css")


def do(path, data={}):
    requests.post(
        "{}/{}".format(SEARCH_DOMAIN, path),
        json={**data, "secret": get_secret(secret_name="WORKER_SECRET")},
    ).raise_for_status()


@index_piazza.bind(app)
@only("course-deploy")
def index_piazza():
    print("Starting to scrape Piazza")

    piazza = PiazzaNetwork(course="cs61a", is_staff=False, is_test=False)

    feed = piazza.get_feed(limit=10000)["feed"]

    course_id = piazza_course_id()

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
    return {"success": True}


@clear_resources.bind(app)
@only("course-deploy")
def clear_resources():
    do("clear/resources")
    return {"success": True}


@upload_resources.bind(app)
@only("course-deploy")
def upload_resources(resources):
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
    return {"success": True}


if __name__ == "__main__":
    app.run()
