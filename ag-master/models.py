from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Course(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(64))
    semester: str = db.Column(db.String(64))
    secret: str = db.Column(db.String(64), unique=True)


class Assignment(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(64))
    course: int = db.Column(db.String(64), db.ForeignKey("course.secret"), index=True)
    file: str = db.Column(db.String(64))
    command: str = db.Column(db.Text)
    ag_key: str = db.Column(db.String(64), unique=True)


class Job(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    assignment: str = db.Column(
        db.String(64), db.ForeignKey("assignment.ag_key"), index=True
    )
    backup: str = db.Column(db.String(64))
    status: str = db.Column(db.String(64))
    result: str = db.Column(db.Text)
    job_key: str = db.Column(db.String(64))
    access_token: str = db.Column(db.String(64))
