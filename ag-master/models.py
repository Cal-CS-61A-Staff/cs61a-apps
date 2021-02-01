from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Course(db.Model):
    secret: str = db.Column(db.String(64), index=True, primary_key=True)
    name: str = db.Column(db.String(64))
    semester: str = db.Column(db.String(64))


class Assignment(db.Model):
    ag_key: str = db.Column(db.String(64), index=True, primary_key=True)
    name: str = db.Column(db.String(64))
    course: int = db.Column(db.String(64), db.ForeignKey("course.secret"), index=True)
    file: str = db.Column(db.String(64))
    command: str = db.Column(db.Text)


class Job(db.Model):
    job_key: str = db.Column(db.String(64), index=True, primary_key=True)
    assignment: str = db.Column(
        db.String(64), db.ForeignKey("assignment.ag_key"), index=True
    )
    backup: str = db.Column(db.String(64))
    status: str = db.Column(db.String(64))
    result: str = db.Column(db.Text)
    access_token: str = db.Column(db.String(64))
