from __future__ import annotations

from typing import List

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from common.db import database_url


def create_models(app: Flask):
    """Creates database models

    :param app: the app to attach the database URL to
    :type app: ~flask.Flask
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


class Assignment(db.Model):
    """Represents an Assignment that can be autograded

    :param assignment_secret: a randomly-generated unique key to be used by
        Okpy to identify this assignment
    :type assignment_secret: str
    :param name: the shortname of the assignment, conventionally the same as
        the Okpy shortname
    :type name: str
    :param course: the course code for the course whose assignment this is
    :type course: str
    :param endpoint: the Okpy endpoint for the relevant course (saved here as
        endpoints change across semesters)
    :type endpoint: str
    :param file: the name of the grading zip file to use to grade the assignment
    :type file: str
    :param command: the command to run on the worker to grade a backup
    :type command:
    :param last_modified: the unix timestamp for the last modification of this
        assignment on the autograder
    :type last_modified: int
    :param batch_size: the grading batch size for this assignment (one worker
        will grade this many items -- must be set such that less than 50 total
        batches are created by an individual run)
    :type batch_size: int
    :param grading_base: the server associated with this assignment (usually
        https://okpy.org)
    :type grading_base: str
    :param jobs: all grading jobs associated with this assignment
    :type jobs: list[Job]
    """

    assignment_secret: str = db.Column(db.String(64), primary_key=True, index=True)
    name: str = db.Column(db.String(64), nullable=False)
    course: str = db.Column(db.String(64), index=True, nullable=False)
    endpoint: str = db.Column(db.String(64), index=True, nullable=False)
    file: str = db.Column(db.String(64), nullable=False)
    command: str = db.Column(db.Text, nullable=False)
    last_modified: int = db.Column(db.Integer, nullable=False)
    batch_size: int = db.Column(db.Integer, nullable=False, default=100)
    grading_base: str = db.Column(
        db.String(64), nullable=False, default="https://okpy.org"
    )
    jobs: List[Job]


class Job(db.Model):
    """Represents an autograding Job

    :param job_secret: the internal job identifier, used for communication
        between the host and the worker
    :type job_secret: str
    :param external_job_id: the external job identifier, used for communication
        between the grading server and the host
    :type external_job_id: str
    :param assignment_secret: a foreign key to the assignment identifier
    :type assignment_secret: str
    :param assignment: the assignment that this job is associated with
    :type assignment: Assignment
    :param backup: the grading server backup this job is associated with
    :type backup: str
    :param status: whether this is queued, started, running, finished, etc.
    :type status: str
    :param result: the grading command's output for this job
    :type result: str
    :param access_token: the grading server's access token to get backup
        content and upload scores for this job
    :type access_token: str
    :param queued_at: the unix timestamp for when this job was queued -- if
        multiple jobs are queued by the same request, they are automatically
        treated as a single trigger by the UI
    :type queued_at: int
    :param started_at: the unix timestamp for when the worker began running
        this job
    :type started_at: int
    :param finished_at: the unix timestamp for when the worker returned the
        result for this job, whether it succeeded or errored
    :type finished_at: int
    """

    job_secret: str = db.Column(db.String(64), index=True, primary_key=True)
    external_job_id: str = db.Column(db.String(64), index=True, nullable=False)
    assignment_secret: str = db.Column(
        db.String(64),
        db.ForeignKey("assignment.assignment_secret"),
        index=True,
        nullable=False,
    )
    assignment: Assignment = db.relationship("Assignment", backref=db.backref("jobs"))
    backup: str = db.Column(db.String(64), nullable=False)
    status: str = db.Column(db.String(64), default="queued", nullable=False)
    result: str = db.Column(db.Text, default="", nullable=False)
    access_token: str = db.Column(db.String(64), nullable=False)
    queued_at: int = db.Column(db.Integer, nullable=False)
    started_at: int = db.Column(db.Integer)
    finished_at: int = db.Column(db.Integer)
