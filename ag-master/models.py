from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Assignment(db.Model):
    assignment_secret: str = db.Column(db.String(64), primary_key=True, index=True)
    name: str = db.Column(db.String(64), nullable=False)
    course: str = db.Column(db.String(64), index=True, nullable=False)
    endpoint: str = db.Column(db.String(64), index=True, nullable=False)
    file: str = db.Column(db.String(64), nullable=False)
    command: str = db.Column(db.Text, nullable=False)


class Job(db.Model):
    job_secret: str = db.Column(db.String(64), index=True, primary_key=True)
    external_job_id: str = db.Column(db.String(64), index=True, nullable=False)
    assignment_secret: int = db.Column(
        db.String(64),
        db.ForeignKey("assignment.assignment_secret"),
        index=True,
        nullable=False,
    )
    assignment: Assignment = db.relationship("Assignment")
    backup: str = db.Column(db.String(64), nullable=False)
    status: str = db.Column(db.String(64), default="queued", nullable=False)
    result: str = db.Column(db.Text, default="", nullable=False)
    access_token: str = db.Column(db.String(64), nullable=False)
