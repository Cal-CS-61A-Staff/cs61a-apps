import datetime
import enum

import pytz
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class EnumType(db.TypeDecorator):
    impl = db.String(255)

    def __repr__(self):
        """ Make alembic detect the right type """
        return "db.String(length=255)"

    def __init__(self, enum_class):
        super(EnumType, self).__init__(self)
        self.enum_class = enum_class

    def process_bind_param(self, enum_value, dialect):
        return enum_value.name

    def process_result_value(self, name, dialect):
        return self.enum_class[name]

    @property
    def python_type(self):
        return self.enum_class


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())
    email = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)

    course = db.Column(db.String(255), nullable=False, index=True)

    call_url = db.Column(db.String(255))
    doc_url = db.Column(db.String(255))

    heartbeat_time = db.Column(db.DateTime, default=db.func.now(), index=True)

    @property
    def short_name(self):
        first_name = self.name.split()[0] if self.name.split() else ""
        if "@" in first_name:
            return first_name.rsplit("@")[0]
        return first_name


class ConfigEntry(db.Model):
    """Represents persistent server-side configuration entries"""

    __tablename__ = "config_entries"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text(), nullable=False)
    public = db.Column(db.Boolean, default=False)

    course = db.Column(db.String(255), nullable=False, index=True)


class Assignment(db.Model):
    """Represents a ticket's assignment."""

    __tablename__ = "assignment"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())
    name = db.Column(db.String(255), nullable=False)
    visible = db.Column(db.Boolean, default=False)

    course = db.Column(db.String(255), nullable=False, index=True)


class Location(db.Model):
    """Represents a ticket's location."""

    __tablename__ = "location"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())
    name = db.Column(db.String(255), nullable=False)
    online = db.Column(db.Boolean, nullable=False)
    link = db.Column(db.String(255), nullable=False)
    visible = db.Column(db.Boolean, default=False)

    course = db.Column(db.String(255), nullable=False, index=True)


TicketStatus = enum.Enum(
    "TicketStatus", "pending assigned resolved deleted juggled rerequested"
)

active_statuses = [
    TicketStatus.pending,
    TicketStatus.assigned,
    TicketStatus.juggled,
    TicketStatus.rerequested,
]


class Ticket(db.Model):
    """Represents an ticket in the queue. A student submits a ticket and receives
    help from a staff member.
    """

    __tablename__ = "ticket"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now(), index=True)
    updated = db.Column(db.DateTime, onupdate=db.func.now())
    status = db.Column(EnumType(TicketStatus), nullable=False, index=True)

    group = db.relationship("Group", back_populates="ticket", uselist=False)

    rerequest_threshold = db.Column(
        db.DateTime
    )  # time when student allowed to re-request help
    hold_time = db.Column(db.DateTime)  # time when student was put on hold
    rerequest_time = db.Column(db.DateTime)  # time when student re-requested help

    user_id = db.Column(db.ForeignKey("user.id"), nullable=False, index=True)
    helper_id = db.Column(db.ForeignKey("user.id"), index=True)

    assignment_id = db.Column(
        db.ForeignKey("assignment.id"), nullable=False, index=True
    )
    location_id = db.Column(db.ForeignKey("location.id"), nullable=False, index=True)
    question = db.Column(db.String(255), nullable=False)

    description = db.Column(db.Text)

    user = db.relationship(User, foreign_keys=[user_id])
    helper = db.relationship(User, foreign_keys=[helper_id])
    assignment = db.relationship(Assignment, foreign_keys=[assignment_id])
    location = db.relationship(Location, foreign_keys=[location_id])

    course = db.Column(db.String(255), nullable=False, index=True)

    call_url = db.Column(db.String(255))
    doc_url = db.Column(db.String(255))

    @classmethod
    def for_user(cls, user):
        if user and user.is_authenticated:
            from common.course_config import get_course

            return cls.query.filter(
                cls.user_id == user.id,
                cls.course == get_course(),
                cls.status.in_([TicketStatus.pending, TicketStatus.assigned]),
            ).one_or_none()

    @classmethod
    def by_status(cls, status=None):
        """ Tickets in any of the states as status.
        @param status: Iterable containing TicketStatus values
        """
        if status is None:
            status = [TicketStatus.pending, TicketStatus.assigned]
        return cls.query.filter(cls.status.in_(status)).order_by(cls.created).all()


TicketEventType = enum.Enum(
    "TicketEventType",
    "create assign unassign resolve delete update juggle rerequest return_to hold_released message_sent",
)


class TicketEvent(db.Model):
    """Represents an event that changes a ticket during its lifecycle."""

    __tablename__ = "ticket_event"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=db.func.now())
    event_type = db.Column(EnumType(TicketEventType), nullable=False)
    ticket_id = db.Column(db.ForeignKey("ticket.id"), nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    course = db.Column(db.String(255), nullable=False, index=True)

    ticket = db.relationship(Ticket)
    user = db.relationship(User)


AppointmentStatus = enum.Enum("AppointmentStatus", "pending active resolved hidden")


class Appointment(db.Model):
    """Represents an appointment block."""

    __tablename__ = "appointment"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, index=True, nullable=False)
    duration = db.Column(db.Interval, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    num_reminders_sent = db.Column(db.Integer, nullable=False, default=0)

    description = db.Column(db.String(255), nullable=False, default="")

    location_id = db.Column(db.ForeignKey("location.id"), nullable=False, index=True)
    location = db.relationship(Location, foreign_keys=[location_id])

    helper_id = db.Column(db.ForeignKey("user.id"), index=True)
    helper = db.relationship(User, foreign_keys=[helper_id])

    signups = db.relationship("AppointmentSignup", back_populates="appointment")

    status = db.Column(EnumType(AppointmentStatus), nullable=False, index=True)

    course = db.Column(db.String(255), nullable=False, index=True)


AttendanceStatus = enum.Enum("AttendanceStatus", "unknown present excused absent")


class AppointmentSignup(db.Model):
    __tablename__ = "appointment_signup"
    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.ForeignKey("appointment.id"), nullable=False, index=True
    )
    appointment = db.relationship("Appointment", back_populates="signups")

    user_id = db.Column(db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship(User, foreign_keys=[user_id])

    assignment_id = db.Column(db.ForeignKey("assignment.id"), index=True)
    assignment = db.relationship(Assignment, foreign_keys=[assignment_id])

    question = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    attendance_status = db.Column(
        EnumType(AttendanceStatus), nullable=False, default=AttendanceStatus.unknown
    )

    course = db.Column(db.String(255), nullable=False, index=True)


GroupStatus = enum.Enum("GroupStatus", "active resolved")


class Group(db.Model):
    __tablename__ = "group"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now(), index=True)

    question = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")

    assignment_id = db.Column(db.ForeignKey("assignment.id"), index=True)
    assignment = db.relationship(Assignment, foreign_keys=[assignment_id])

    location_id = db.Column(db.ForeignKey("location.id"), nullable=False, index=True)
    location = db.relationship(Location, foreign_keys=[location_id])

    ticket_id = db.Column(db.ForeignKey("ticket.id"), nullable=True, index=True)
    ticket = db.relationship(Ticket, back_populates="group", foreign_keys=[ticket_id])

    attendees = db.relationship(
        "GroupAttendance", back_populates="group", lazy="joined"
    )

    group_status = db.Column(
        EnumType(GroupStatus), nullable=False, default=GroupStatus.active
    )

    call_url = db.Column(db.String(255))
    doc_url = db.Column(db.String(255))

    course = db.Column(db.String(255), nullable=False, index=True)


GroupAttendanceStatus = enum.Enum("GroupAttendanceStatus", "present gone")


class GroupAttendance(db.Model):
    __tablename__ = "group_attendance"
    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(db.ForeignKey("group.id"), nullable=False, index=True)
    group = db.relationship("Group", back_populates="attendees")

    user_id = db.Column(db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship(User, foreign_keys=[user_id], lazy="joined")

    group_attendance_status = db.Column(
        EnumType(GroupAttendanceStatus),
        nullable=False,
        default=GroupAttendanceStatus.present,
    )

    course = db.Column(db.String(255), nullable=False, index=True)


class ChatMessage(db.Model):
    __tablename__ = "chat_message"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=db.func.now())

    body = db.Column(db.String(255), nullable=False, default="")

    user_id = db.Column(db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship(User, foreign_keys=[user_id])

    ticket_id = db.Column(db.ForeignKey("ticket.id"), nullable=True, index=True)
    ticket = db.relationship("Ticket", backref=db.backref("messages", lazy="joined"))

    appointment_id = db.Column(
        db.ForeignKey("appointment.id"), nullable=True, index=True
    )
    appointment = db.relationship(
        "Appointment", backref=db.backref("messages", lazy="joined")
    )

    group_id = db.Column(db.ForeignKey("group.id"), nullable=True, index=True)
    group = db.relationship("Group", backref=db.backref("messages", lazy="joined"))

    course = db.Column(db.String(255), nullable=False, index=True)


class CourseNotificationState(db.Model):
    __tablename__ = "notification_state"
    id = db.Column(db.Integer, primary_key=True)
    last_queue_ping = db.Column(db.DateTime, nullable=False)
    last_appointment_notif = db.Column(db.DateTime, nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    course = db.Column(db.String(255), nullable=False, index=True)


def get_current_time():
    return (
        pytz.utc.localize(datetime.datetime.utcnow())
        .astimezone(pytz.timezone("America/Los_Angeles"))
        .replace(tzinfo=None)
    )
