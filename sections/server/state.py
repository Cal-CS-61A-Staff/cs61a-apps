import calendar
import csv

from io import StringIO
from datetime import datetime, timedelta
from functools import wraps
from json import dumps
from typing import List, Optional, Union

import flask
import pytz
from flask import jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from common.course_config import get_course, is_admin
from common.rpc.auth import post_slack_message, read_spreadsheet, validate_secret
from common.rpc.secrets import only
from common.rpc.sections import rpc_export_attendance
from models import (
    Attendance,
    AttendanceStatus,
    CourseConfig,
    Section,
    Session,
    User,
    db,
)

FIRST_WEEK_START = datetime(year=2020, month=9, day=1).timestamp()


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


def admin_required(func):
    @wraps(func)
    @staff_required
    def wrapped(**kwargs):
        if not is_admin(current_user.email):
            raise Failure("Only course admins can perform this action.")
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
    spare_capacity = max(0, section.capacity - len(section.students))
    if spare_capacity:
        score -= big * spare_capacity
    score += section.id
    return score


def get_config() -> CourseConfig:
    return CourseConfig.query.filter_by(course=get_course()).one()


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

    @app.route("/", endpoint="index")
    @app.route("/history/")
    @app.route("/admin/")
    @app.route("/section/<path:path>")
    @app.route("/user/<path:path>")
    def generic(**_):
        return render_template("index.html")

    @app.route("/debug")
    def debug():
        refresh_state()
        return "<body></body>"

    @api
    def refresh_state():
        if current_user.is_authenticated:
            config = CourseConfig.query.filter_by(course=get_course()).one_or_none()
            if config is None:
                config = CourseConfig(course=get_course())
                db.session.add(config)
                db.session.commit()

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
                "currentUser": current_user.full_json,
                "config": config.json,
                "custom": None,
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
        if not get_config().can_students_change:
            raise Failure("Students cannot add themselves themselves to sections!")
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
        if not get_config().can_students_change:
            raise Failure("Students cannot remove themselves from sections!")
        section_id = int(section_id)
        current_user.sections = [
            section for section in current_user.sections if section.id != section_id
        ]
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def claim_section(section_id: str):
        if not get_config().can_tutors_change:
            raise Failure("Tutors cannot add themselves to sections!")
        section_id = int(section_id)
        section = Section.query.get(section_id)
        if section.staff:
            raise Failure("Section is already claimed!")
        section.staff = current_user
        db.session.commit()
        return refresh_state()

    @api
    @staff_required
    def unassign_section(section_id: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        if section.staff is None:
            raise Failure("Section is already unassigned!")
        if section.staff.email == current_user.email:
            if not get_config().can_tutors_change:
                raise Failure("Tutors cannot remove themselves from sections!")
        else:
            if not get_config().can_tutors_reassign:
                raise Failure("Tutors cannot remove other tutors from sections!")
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
        existing_session = Session.query.filter_by(
            start_time=start_time, section_id=section_id
        ).first()
        if existing_session is None:
            db.session.add(Session(start_time=start_time, section_id=section_id))
            db.session.commit()
        return fetch_section(section_id=section_id)

    @api
    @staff_required
    def set_attendance(session_id: str, student: str, status: Optional[str]):
        session_id = int(session_id)
        session = Session.query.get(session_id)
        status = AttendanceStatus[status]
        student = User.query.filter_by(email=student).one()
        Attendance.query.filter_by(session_id=session_id, student=student).delete()
        if status is not None:
            db.session.add(
                Attendance(status=status, session_id=session_id, student=student)
            )
        db.session.commit()
        return fetch_section(section_id=session.section_id)

    @api
    @admin_required
    def update_config(**kwargs):
        config = get_config()
        for key, value in kwargs.items():
            setattr(config, key, value)
        db.session.commit()
        return refresh_state()

    @api
    @admin_required
    def import_sections(sheet_url):
        index = read_spreadsheet(course="cs61a", url=sheet_url, sheet_name="Index")
        header = index[0][:4]
        if header != ["Day", "Start Time", "End Time", "Sheet"]:
            raise Failure("Invalid header for index sheet")
        for day, start_time, end_time, sheet, *args in index[1:]:
            sheet: List[List[Union[str, int]]] = read_spreadsheet(
                course="cs61a", url=sheet_url, sheet_name=repr(sheet)
            )
            header = sheet[0]
            name_col = header.index("Name")
            email_col = header.index("Email")

            day = list(calendar.day_name).index(day)

            start_time = datetime.strptime(start_time, "%I:%M %p")
            start_time = start_time.replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day,
            )
            while start_time.weekday() != day:
                start_time += timedelta(days=1)

            end_time = datetime.strptime(end_time, "%I:%M %p")
            end_time = end_time.replace(
                year=start_time.year, month=start_time.month, day=start_time.day
            )

            pst = pytz.timezone("US/Pacific")
            start_time = pst.localize(start_time).timestamp()
            end_time = pst.localize(end_time).timestamp()

            for section in sheet[1:]:
                tutor_name = section[name_col]
                tutor_email = section[email_col]
                if not tutor_name or not tutor_email:
                    continue
                tutor_user = User.query.filter_by(email=tutor_email).one_or_none()
                if tutor_user is None:
                    tutor_user = User(email=tutor_email, name=tutor_name, is_staff=True)
                    db.session.add(tutor_user)
                tutor_user.is_staff = True

                capacity = sum(1 for col in header if "Student" in col)

                db.session.add(
                    Section(
                        start_time=start_time,
                        end_time=end_time,
                        capacity=capacity,
                        staff=tutor_user,
                    )
                )

            db.session.commit()

        return refresh_state()

    @api
    @staff_required
    def remove_student(student: str, section_id: str):
        section_id = int(section_id)
        student = User.query.filter_by(email=student).one()
        student.sections = [
            section for section in current_user.sections if section.id != section_id
        ]
        db.session.commit()
        return fetch_section(section_id=section_id)

    @api
    @staff_required
    def add_student(email: str, section_id: str):
        section_id = int(section_id)
        section = Section.query.get(section_id)
        student = User.query.filter_by(email=email).one_or_none()
        if student is None:
            student = User(email=email, name=email, is_staff=False)
        student.sections = [section]
        db.session.commit()
        return fetch_section(section_id=section_id)

    @api
    @admin_required
    def delete_section(section_id: str):
        section_id = int(section_id)
        section = Section.query.filter_by(id=section_id).one()
        if section.students:
            raise Failure("Cannot delete an empty section")
        db.session.delete(section)
        db.session.commit()

        return refresh_state()

    @api
    @admin_required
    def export_attendance(full: bool):
        return export_helper(full)

    @rpc_export_attendance.bind(app)
    @only("grade-display", allow_staging=True)
    def export_attendance_rpc(full: bool):
        return export_helper(full)

    @api
    def export_attendance_secret(secret: str, full: bool):
        if validate_secret(secret=secret) == "cs61a":
            return export_helper(full)

    def export_helper(full: bool):
        if full:
            stringify = dumps
        else:

            def stringify(data):
                buff = StringIO()
                writer = csv.writer(buff)
                for student, attendance in data.items():
                    writer.writerow([student, attendance])
                return buff.getvalue()

        return {
            **refresh_state(),
            "custom": {
                "fileName": "attendances.json" if full else "attendance_scores.csv",
                "attendances": stringify(
                    {
                        user.email: [
                            {
                                "section_id": attendance.session.section_id,
                                "start_time": attendance.session.start_time,
                                "status": attendance.status.name,
                            }
                            for attendance in user.attendances
                        ]
                        if full
                        else len(
                            set(
                                (attendance.session.start_time - FIRST_WEEK_START)
                                // (60 * 60 * 24 * 7)
                                for attendance in user.attendances
                                if attendance.session.start_time >= FIRST_WEEK_START
                                and attendance.status == AttendanceStatus.present
                            )
                        )
                        for user in User.query.filter_by(is_staff=False)
                        .options(
                            joinedload(User.attendances).joinedload(Attendance.session)
                        )
                        .all()
                    }
                ),
            },
        }

    @api
    @staff_required
    def fetch_user(user_id: str):
        user_id = int(user_id)
        user = User.query.filter_by(id=user_id).one_or_none()
        return user.full_json

    @api
    @admin_required
    def remind_tutors_to_setup_zoom_links():
        sections: List[Section] = Section.query.filter_by(call_link=None).all()
        tutor_emails = set()
        for section in sections:
            tutor_emails.add(section.staff.email)
        tutor_emails = sorted(tutor_emails)
        if not tutor_emails:
            raise Failure("All tutors have set up their Zoom links!")

        message = (
            "The following tutors have not yet set up their Zoom links for all their sections:\n"
            + "\n".join(f" • <!{email}>" for email in tutor_emails)
            + "\n Please do so ASAP! Thanks."
        )

        post_slack_message(course="cs61a", message=message, purpose="tutors")

        return refresh_state()
