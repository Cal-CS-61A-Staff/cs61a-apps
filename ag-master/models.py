from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Course(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String)
    semester: str = db.Column(db.String)
    secret: str = db.Column(db.String)


class Assignment(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String)
    course: int = db.Column(db.Integer, db.ForeignKey("course.secret"))
    file: str = db.Column(db.String)
    command: str = db.Column(db.String)
    ag_key: str = db.Column(db.String)


class Job(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    assignment: str = db.Column(db.String, db.ForeignKey("assignment.ag_key"))
    backup: str = db.Column(db.String)
    status: str = db.Column(db.String)
    result: str = db.Column(db.String)
    job_key: str = db.Column(db.String)
