
import requests, os

client_name = None
def send(message, course):
    requests.post(
        "https://auth.apps.cs61a.org/slack/post_message",
        json={
            "client_name": os.environ['CLIENT_NAME'],
            "secret": os.environ['SECRET'],
            "message": message,
            "purpose": "piazza-reminder",
            "course": course,
        },
    ).raise_for_status()
