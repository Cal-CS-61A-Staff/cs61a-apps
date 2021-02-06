from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Assignment(db.Model):
    assignment_secret: str = db.Column(db.String(64), primary_key=True, index=True)
    name: str = db.Column(db.String(64))
    course: str = db.Column(db.String(64), index=True)
    endpoint: str = db.Column(db.String(64), index=True)
    file: str = db.Column(db.String(64))
    command: str = db.Column(db.Text)


class Job(db.Model):
    job_secret: str = db.Column(db.String(64), index=True, primary_key=True)
    external_job_id: str = db.Column(db.String(64), index=True)
    assignment_secret: int = db.Column(
        db.Integer, db.ForeignKey("assignment.assignment_secret"), index=True
    )
    assignment: Assignment = db.relationship("Assignment")
    backup: str = db.Column(db.String(64))
    status: str = db.Column(db.String(64))
    result: str = db.Column(db.Text)
    access_token: str = db.Column(db.String(64))
