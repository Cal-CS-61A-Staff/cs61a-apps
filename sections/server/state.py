from datetime import datetime
from functools import wraps
from typing import Union

import flask
from flask import jsonify, render_template, request
from flask_login import current_user, login_required

from models import Attendance, AttendanceStatus, Section, Session, User, db


class Failure(Exception):
    pass


def staff_required(func):
    @wraps(func)
    @login_required
    def wrapped(**kwargs):
        if not current_user.is_staff:
            raise Failure("Only staff can perform this action")
        return func(**kwargs)

    return wrapped


def section_sorter(section: Section) -> int:
    score = 0
    big = 10000
    if current_user.is_staff and section.staff is None:
        score -= big * 100
    if (
        section.staff is not None
        and section.staff.id == current_user.id
        or current_user.id in [student.id for student in section.students]
    ):
        score -= big * 10
    if section.capacity > len(section.students):
        score -= big
    score += section.id
    return score


def create_state_client(app: flask.Flask):
    def api(handler):
        def wrapped():
            try:
                return jsonify({"success": True, "data": handler(**request.json)})
            except Failure as failure:
                return jsonify({"success": False, "message": str(failure)})

        app.add_url_rule(
            f"/api/{handler.__name__}", handler.__name__, wrapped, methods=["POST"]
        )

        return handler

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/debug")
    def debug():
        refresh_state()
        return render_template("index.html")

    @api
    def refresh_state():
        if current_user.is_authenticated:
            return {
                "enrolledSection": current_user.sections[0].json
                if current_user.sections
                else None,
                "taughtSections": [
                    section.json
                    for section in sorted(
                        current_user.sections_taught, key=section_sorter
                    )
                ],
                "sections": [
                    section.json
                    for section in sorted(Section.query.all(), key=section_sorter)
                ],
                "currentUser": current_user.json,
            }
        else:
            return {"sections": []}

    @api
    @staff_required
    def fetch_section(section_id: Union[int, str]):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        return section.full_json

    @api
    @login_required
    def join_section(target_section_id: str):
        target_section_id = int(target_section_id)
        # check if they can be added to the new section
        target_section: Section = Section.query.get(target_section_id)
        if target_section.capacity <= len(target_section.students):
            raise Failure("Target tutorial section is already full.")
        # remove them from *all* old_sections for now
        current_user.sections = [target_section]
        db.session.commit()
        return refresh_state()

    @api
    @login_required
    def leave_section(section_id: str):
        section_id = int(section_id)
        current_user.sections = [
            section for section in current_user.sections if section.id != section_id
        ]
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def claim_section(section_id: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        section.staff = current_user
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def unassign_section(section_id: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        section.staff = None
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def update_section_description(section_id: str, description: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        section.description = description
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def update_section_call_link(section_id: str, call_link: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        section.call_link = call_link
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def start_session(section_id: str, start_time: int):
        section_id = int(section_id)
        db.session.add(Session(start_time=start_time, section_id=section_id))
        db.session.commit()
        return fetch_section(section_id=section_id)

    @api
    @staff_required
    def set_attendance(session_id: str, student: str, status: str):
        session_id = int(session_id)
        session = Session.query.get(session_id)
        status = AttendanceStatus[status]
        student = User.query.filter_by(email=student).one()
        Attendance.query.filter_by(session_id=session_id, student=student).delete()
        db.session.add(
            Attendance(status=status, session_id=session_id, student=student)
        )
        db.session.commit()
        return fetch_section(section_id=session.section_id)
