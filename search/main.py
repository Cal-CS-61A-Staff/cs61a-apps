import requests
from flask import Flask, redirect
from flask_cors import CORS

from common.rpc.search import (
    clear_piazza,
    clear_resources,
    insert_piazza,
    insert_resources,
    query,
)
from common.rpc.secrets import only

app = Flask(__name__)
CORS(app)

ELASTIC_SEARCH = "http://localhost:9200"
PIAZZA_INDEX = "piazza"
RESOURCE_INDEX = "resources"

config = {
    "mappings": {
        "properties": {
            "name": {"type": "search_as_you_type"},
            "content": {"type": "search_as_you_type"},
            "type": {"type": "search_as_you_type"},
            "tags": {"type": "search_as_you_type"},
        }
    },
    "settings": {
        "analysis": {
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_keywords": {"type": "keyword_marker", "keywords": ["example"]},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "english_possessive_stemmer": {
                    "type": "stemmer",
                    "language": "possessive_english",
                },
                "zero_prefix_remover": {
                    "type": "pattern_replace",
                    "pattern": r"0([0-9])+",
                    "replacement": r"$1",
                },
            },
            "analyzer": {
                "default": {
                    "tokenizer": "standard",
                    "char_filter": ["html_strip"],
                    "filter": [
                        "english_possessive_stemmer",
                        "lowercase",
                        "english_stop",
                        "english_keywords",
                        "english_stemmer",
                        "zero_prefix_remover",
                    ],
                }
            },
        }
    },
}


@app.route("/")
def index():
    return redirect("https://cs61a.org")


@clear_piazza.bind(app)
@only("indexer")
def clear_piazza():
    requests.delete(f"{ELASTIC_SEARCH}/{PIAZZA_INDEX}").json()
    return requests.put(f"{ELASTIC_SEARCH}/{PIAZZA_INDEX}", json=config).json()


@insert_piazza.bind(app)
@only("indexer")
def insert_piazza(posts):
    for post in posts:
        id = post["id"]
        requests.post(f"{ELASTIC_SEARCH}/{PIAZZA_INDEX}/_doc/{id}", json=post)
    return {"success": True}


@clear_resources.bind(app)
@only("indexer")
def clear_resources():
    requests.delete(f"{ELASTIC_SEARCH}/{RESOURCE_INDEX}").json()
    return requests.put(f"{ELASTIC_SEARCH}/{RESOURCE_INDEX}", json=config).json()


@insert_resources.bind(app)
@only("indexer")
def insert_resources(resources):
    for resource in resources:
        requests.post(f"{ELASTIC_SEARCH}/{RESOURCE_INDEX}/_doc", json=resource)
    return {"success": True}


@query.bind(app)
def query(piazza_params, resource_params):
    piazza = requests.get(
        f"{ELASTIC_SEARCH}/{PIAZZA_INDEX}/_search", json=piazza_params
    ).json()
    resources = requests.get(
        f"{ELASTIC_SEARCH}/{RESOURCE_INDEX}/_search", json=resource_params
    ).json()
    return {"piazza": piazza, "resources": resources}


if __name__ == "__main__":
    app.run()
