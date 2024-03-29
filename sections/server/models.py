from enum import Enum
from typing import List
from urllib.parse import quote

import flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload

from common.course_config import get_course_id, is_admin
from common.db import database_url


def create_models(app: flask.Flask):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy()


user_section_junction = db.Table(
    "user_section_junction",
    db.Model.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), index=True),
    db.Column("section_id", db.Integer, db.ForeignKey("section.id"), index=True),
)


class Section(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    description: str = db.Column(db.String(255))
    start_time: int = db.Column(db.Integer)
    end_time: int = db.Column(db.Integer)
    capacity: int = db.Column(db.Integer)
    call_link: str = db.Column(db.String(255), nullable=True)
    enrollment_code: str = db.Column(db.String(255), nullable=True)
    staff_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    staff: "User" = db.relationship(
        "User", backref=db.backref("sections_taught", lazy="joined"), lazy="joined"
    )
    students: List["User"] = db.relationship(
        "User",
        secondary=user_section_junction,
        backref=db.backref("sections", lazy="joined"),
        lazy="joined",
    )
    tag_string: str = db.Column(
        db.String(255), nullable=False, default=""
    )  # comma separated list of tags

    @property
    def tags(self):
        return self.tag_string.split(",")

    @tags.setter
    def tags(self, tags: List[str]):
        self.tag_string = ",".join(tags)

    @property
    def needs_enrollment_code(self):
        return self.enrollment_code not in ["", None]

    @property
    def json(self):
        return {
            "id": str(self.id),
            "staff": self.staff.json if self.staff is not None else None,
            "students": [
                student.json
                for student in sorted(self.students, key=lambda student: student.name)
            ],
            "description": self.description,
            "capacity": self.capacity,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "callLink": self.call_link,
            "needsEnrollmentCode": self.needs_enrollment_code,
            "tags": self.tags,
        }

    @property
    def full_json(self):
        return {
            **self.json,
            "sessions": [
                session.full_json
                for session in sorted(
                    self.sessions, key=lambda session: session.start_time
                )
            ],
        }


class Session(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    start_time: int = db.Column(db.Integer)
    section_id: int = db.Column(db.Integer, db.ForeignKey("section.id"), index=True)
    section: Section = db.relationship(
        "Section", backref=db.backref("sessions"), lazy="joined"
    )
    attendances: List["Attendance"]

    @property
    def json(self):
        return {"id": self.id, "startTime": self.start_time}

    @property
    def full_json(self):
        return {
            **self.json,
            "attendances": [
                attendance.json
                for attendance in sorted(
                    self.attendances, key=lambda attendance: attendance.student.name
                )
            ],
        }


# note that the *keys* are persisted to the db, not the values
class AttendanceStatus(Enum):
    present = 1
    excused = 2
    absent = 3


class Attendance(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    status: AttendanceStatus = db.Column(db.Enum(AttendanceStatus))
    session_id: int = db.Column(db.Integer, db.ForeignKey("session.id"), index=True)
    session: Session = db.relationship(
        "Session",
        backref=db.backref("attendances", lazy="joined"),
        lazy="joined",
        innerjoin=True,
    )
    student_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    student: "User" = db.relationship(
        "User", backref=db.backref("attendances"), lazy="joined", innerjoin=True
    )

    @property
    def json(self):
        return {"student": self.student.json, "status": self.status.name}

    @property
    def full_json(self):
        return {
            **self.json,
            "session": self.session.json,
            "section": self.session.section.json if self.session.section else None,
        }


class User(db.Model, UserMixin):
    # just here to make PyCharm stop complaining
    def __init__(self, email: str, name: str, is_staff: bool):
        # noinspection PyArgumentList
        super().__init__(email=email, name=name, is_staff=is_staff)

    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(255), index=True)
    name: str = db.Column(db.String(255))
    is_staff: bool = db.Column(db.Boolean)
    sections: List[Section]
    attendances: List[Attendance]

    @property
    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "isStaff": self.is_staff,
            "backupURL": f"https://okpy.org/admin/course/{get_course_id()}/{quote(self.email)}",
        }

    @property
    def full_json(self):
        attendances = (
            Attendance.query.filter_by(student_id=self.id)
            .options(
                joinedload(Attendance.session, innerjoin=True)
                .joinedload(Session.section)
                .joinedload(Section.staff)
            )
            .all()
        )
        return {
            **self.json,
            "isAdmin": is_admin(self.email),
            "attendanceHistory": [
                attendance.full_json
                for attendance in sorted(
                    attendances, key=lambda attendance: attendance.session.start_time
                )
            ],
        }


class CourseConfig(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    course: str = db.Column(db.String(255), index=True)

    can_students_change = db.Column(db.Boolean, default=True)
    can_tutors_change = db.Column(db.Boolean, default=True)
    can_tutors_reassign = db.Column(db.Boolean, default=True)
    message: str = db.Column(db.String(1024), default="")

    @property
    def json(self):
        return {
            "canStudentsChange": self.can_students_change,
            "canTutorsChange": self.can_tutors_change,
            "canTutorsReassign": self.can_tutors_reassign,
            "message": self.message,
        }
