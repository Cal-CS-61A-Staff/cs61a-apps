import datetime
import functools
import hmac

import random
import time
from operator import or_
from os import getenv
from urllib.parse import urljoin, urlparse

from flask import abort, render_template, g, request, jsonify
from flask_login import current_user, login_user
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from common.rpc.auth import post_slack_message, read_spreadsheet, validate_secret
from common.url_for import url_for
from oh_queue import app, db
from common.course_config import (
    get_course,
    format_coursecode,
    get_course_id,
    get_domain,
)
from oh_queue.models import (
    Assignment,
    ChatMessage,
    ConfigEntry,
    CourseNotificationState,
    Location,
    Ticket,
    TicketEvent,
    TicketEventType,
    TicketStatus,
    active_statuses,
    Appointment,
    AppointmentSignup,
    User,
    AppointmentStatus,
    AttendanceStatus,
    get_current_time,
    GroupAttendance,
    GroupAttendanceStatus,
    Group,
    GroupStatus,
)
from oh_queue.slack import send_appointment_summary


def user_json(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "shortName": user.short_name,
        "isStaff": user.is_staff,
        "call_url": user.call_url,
        "doc_url": user.doc_url,
    }


def student_json(user):
    """ Only send student information to staff. """
    can_see_details = current_user.is_authenticated and (
        current_user.is_staff or user.id == current_user.id
    )
    if not can_see_details:
        return None
    return user_json(user)


def message_json(message: ChatMessage):
    return {
        "user": user_json(message.user),
        "body": message.body,
        "created": message.created.isoformat(),
    }


def ticket_json(ticket):
    group = ticket.group
    return {
        "id": ticket.id,
        "status": ticket.status.name,
        "user": user_json(ticket.user) if group else student_json(ticket.user),
        "created": ticket.created.isoformat(),
        "sort_key": ticket.sort_key.isoformat(),
        "rerequest_threshold": ticket.rerequest_threshold
        and ticket.rerequest_threshold.isoformat(),
        "hold_time": ticket.hold_time and ticket.hold_time.isoformat(),
        "rerequest_time": ticket.rerequest_time and ticket.rerequest_time.isoformat(),
        "updated": ticket.updated and ticket.updated.isoformat(),
        "location_id": ticket.location_id,
        "assignment_id": ticket.assignment_id,
        "description": ticket.description,
        "question": ticket.question,
        "helper": ticket.helper and user_json(ticket.helper),
        "call_url": ticket.call_url,
        "doc_url": ticket.doc_url,
        "group_id": group.id if group else None,
        "messages": [message_json(message) for message in ticket.messages],
    }


def assignment_json(assignment):
    return {"id": assignment.id, "name": assignment.name, "visible": assignment.visible}


def location_json(location):
    return {
        "id": location.id,
        "name": location.name,
        "visible": location.visible,
        "online": location.online,
        "link": location.link,
    }


def get_online_location():
    online_location = Location.query.filter_by(
        course=get_course(), name="Online"
    ).one_or_none()
    online_visible = (
        ConfigEntry.query.filter_by(key="online_active", course=get_course())
        .one()
        .value
        == "true"
    )
    if online_location is None:
        online_location = Location(
            name="Online",
            visible=online_visible,
            course=get_course(),
            online=True,
            link="",
        )
        db.session.add(online_location)
        db.session.commit()
    else:
        online_location.visible = online_visible
        db.session.commit()
    return online_location


def config_json():
    config = {}
    for config_entry in ConfigEntry.query.filter_by(course=get_course()).all():
        if config_entry.public:
            config[config_entry.key] = config_entry.value
    config["okpy_endpoint_id"] = get_course_id()
    return config


def appointments_json(appointment: Appointment):
    return {
        "id": appointment.id,
        "start_time": appointment.start_time.isoformat(),
        "duration": appointment.duration.total_seconds(),
        "signups": [signup_json(signup) for signup in appointment.signups],
        "capacity": appointment.capacity,
        "location_id": appointment.location_id,
        "helper": appointment.helper and user_json(appointment.helper),
        "status": appointment.status.name,
        "description": appointment.description,
        "messages": [message_json(message) for message in appointment.messages],
    }


def signup_json(signup: AppointmentSignup):
    return {
        "id": signup.id,
        "assignment_id": signup.assignment_id,
        "user": user_json(signup.user),  # TODO: This should be private!
        "question": signup.question,
        "description": signup.description,
        "attendance_status": signup.attendance_status.name,
    }


def group_json(group: Group):
    return {
        "id": group.id,
        "created": group.created.isoformat(),
        "attendees": [
            group_attendance_json(attendance)
            for attendance in group.attendees
            if attendance.group_attendance_status == GroupAttendanceStatus.present
        ],
        "location_id": group.location_id,
        "ticket_id": group.ticket_id,
        "assignment_id": group.assignment_id,
        "question": group.question,
        "description": group.description,
        "group_status": group.group_status.name,
        "call_url": group.call_url,
        "doc_url": group.doc_url,
        "messages": [message_json(message) for message in group.messages],
    }


def group_attendance_json(attendance: GroupAttendance):
    return {
        "id": attendance.id,
        "group_id": attendance.group_id,
        "group_attendance_status": attendance.group_attendance_status.name,
        "user": user_json(attendance.user),
    }


def add_response(event, payload):
    g.response_buffer.append([event, payload])


def emit_event(ticket, event_type):
    ticket_event = TicketEvent(
        event_type=event_type, ticket=ticket, user=current_user, course=get_course()
    )
    db.session.add(ticket_event)
    db.session.commit()
    add_response("event", {"type": event_type.name, "ticket": ticket_json(ticket)})


def emit_appointment_event(appointment, event_type):
    # TODO: log to db
    add_response(
        "appointment_event",
        {"type": event_type, "appointment": appointments_json(appointment)},
    )


def emit_group_event(group, event_type):
    add_response("group_event", {"type": event_type, "group": group_json(group)})


def emit_state(attrs, entity=None):
    state = {}
    if "tickets" in attrs:
        tickets = (
            Ticket.query.filter(
                Ticket.status.in_(active_statuses), Ticket.course == get_course()
            )
            .options(joinedload(Ticket.user, innerjoin=True))
            .options(joinedload(Ticket.helper))
            .options(joinedload(Ticket.group))
            .all()
        )
        if entity not in tickets and isinstance(entity, Ticket):
            if has_ticket_access(entity):
                tickets.append(entity)
        state["tickets"] = [ticket_json(ticket) for ticket in tickets]
    if "assignments" in attrs:
        assignments = Assignment.query.filter_by(course=get_course()).all()
        state["assignments"] = [
            assignment_json(assignment) for assignment in assignments
        ]
    if "locations" in attrs:
        locations = Location.query.filter(
            Location.course == get_course(), Location.name != "Online"
        ).all()
        state["locations"] = [location_json(location) for location in locations]
        state["locations"].append(location_json(get_online_location()))
    if "config" in attrs:
        state["config"] = config_json()
    if "appointments" in attrs:
        appointments = (
            Appointment.query.filter(
                Appointment.status != AppointmentStatus.resolved,
                Appointment.course == get_course(),
            )
            .order_by(Appointment.id)
            .options(joinedload(Appointment.helper))
            .options(
                joinedload(Appointment.signups).joinedload(
                    AppointmentSignup.user, innerjoin=True
                )
            )
            .all()
        )
        if entity not in appointments and isinstance(entity, Appointment):
            if current_user.is_staff or current_user.id in [
                signup.user.id for signup in entity.signups
            ]:
                appointments.append(entity)

        state["appointments"] = [
            appointments_json(appointment) for appointment in appointments
        ]
    if "groups" in attrs:
        groups = Group.query.filter(
            Group.group_status == GroupStatus.active, Group.course == get_course()
        ).all()
        if entity not in groups and isinstance(entity, Group):
            if has_group_access(entity):
                groups.append(entity)
        state["groups"] = [group_json(group) for group in groups]
    if "current_user" in attrs:
        state["current_user"] = student_json(current_user)
    if "presence" in attrs:
        out = dict(
            students=User.query.filter(
                User.heartbeat_time
                > datetime.datetime.utcnow() - datetime.timedelta(seconds=30),
                User.course == get_course(),
                User.is_staff == False,
            ).count()
        )
        active_staff = {
            (t.helper.email, t.helper.name)
            for t in Ticket.query.filter(
                Ticket.status.in_(active_statuses),
                Ticket.helper != None,
                Ticket.course == get_course(),
            ).all()
        }
        active_staff |= {
            (user.email, user.name)
            for user in User.query.filter(
                User.heartbeat_time
                > datetime.datetime.utcnow() - datetime.timedelta(seconds=30),
                User.course == get_course(),
                User.is_staff == True,
            ).all()
        }
        out["staff"] = len(active_staff)
        out["staff_list"] = list(active_staff)
        state["presence"] = out

    add_response("state", state)


def init_config():
    db.session.add(
        ConfigEntry(
            key="welcome",
            value="Welcome to the OH Queue!",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(key="is_queue_open", value="true", public=True, course=get_course())
    )
    db.session.add(
        ConfigEntry(
            key="description_required", value="false", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="queue_magic_word_mode", value="none", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="queue_magic_word_data", value="", public=False, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(key="juggling_delay", value="5", public=True, course=get_course())
    )
    db.session.add(
        ConfigEntry(key="ticket_prompt", value="", public=True, course=get_course())
    )
    db.session.add(
        ConfigEntry(
            key="appointments_open", value="false", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="online_active", value="false", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="students_set_online_link",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="students_set_online_doc",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="daily_appointment_limit", value="2", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="weekly_appointment_limit", value="5", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="simul_appointment_limit", value="5", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="show_okpy_backups", value="false", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="slack_notif_long_queue",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="slack_notif_appt_summary",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="slack_notif_missed_appt",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="party_enabled", value="false", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="allow_private_party_tickets",
            value="true",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="recommend_appointments", value="true", public=True, course=get_course()
        )
    )
    db.session.add(
        ConfigEntry(
            key="only_registered_students",
            value="false",
            public=True,
            course=get_course(),
        )
    )
    db.session.add(
        ConfigEntry(
            key="party_name",
            value="Party",
            public=True,
            course=get_course(),
        )
    )
    db.session.commit()


# We run a React app, so serve index.html on all routes
@app.route("/")
@app.route("/<path:path>")
@app.route("/tickets/<int:ticket_id>/")
@app.route("/groups/<int:group_id>/")
@app.route("/error", endpoint="error")
def index(*args, **kwargs):
    check = db.session.query(ConfigEntry).filter_by(course=get_course()).first()
    if not check:
        init_config()
    notif_state = CourseNotificationState.query.filter_by(
        course=get_course()
    ).one_or_none()
    if not notif_state:
        notif_state = CourseNotificationState(
            course=get_course(),
            domain=get_domain(),
            last_queue_ping=datetime.datetime.now(),
            last_appointment_notif=get_current_time(),
        )
        db.session.add(notif_state)
    db.session.commit()

    return render_template("index.html", course_name=format_coursecode(get_course()))


@app.before_request
def initialize_response_buffer():
    g.response_buffer = []


def api(endpoint):
    def decorator(f):
        @functools.wraps(f)
        def handler():
            args = request.json
            resp = f() if args == {} else f(args)
            return jsonify({"action": resp, "updates": g.response_buffer})

        def sudo_handler():
            data = request.json
            secret = data["secret"]
            email = data["email"]
            course = data.get("course", None)
            args = data.get("args", None)
            course = validate_secret(secret=secret, course=course)
            user = User.query.filter_by(course=course, email=email).one()
            login_user(user)
            resp = f() if args is None else f(args)
            return jsonify({"action": resp, "updates": g.response_buffer})

        app.add_url_rule(
            "/api/{}".format(endpoint), f.__name__, handler, methods=["POST"]
        )

        app.add_url_rule(
            "/api/sudo/{}".format(endpoint),
            "sudo_" + f.__name__,
            sudo_handler,
            methods=["POST"],
        )

        return f

    return decorator


def socket_error(message, category="danger", ticket_id=None):
    redirect = url_for("index")
    if ticket_id is not None:
        redirect = url_for("index", ticket_id=ticket_id)
    return {"messages": [{"category": category, "text": message}], "redirect": redirect}


def socket_redirect(**kwargs):
    from flask import url_for

    redirect = url_for("index", **kwargs)
    return {"redirect": redirect}


def socket_unauthorized():
    return socket_error("You don't have permission to do that")


def logged_in(f):
    @functools.wraps(f)
    def wrapper(*args, **kwds):
        if not current_user.is_authenticated and current_user.course == get_course():
            return socket_unauthorized()
        return f(*args, **kwds)

    return wrapper


def is_staff(f):
    @functools.wraps(f)
    def wrapper(*args, **kwds):
        if not (
            current_user.is_authenticated
            and current_user.is_staff
            and current_user.course == get_course()
        ):
            return socket_unauthorized()
        return f(*args, **kwds)

    return wrapper


def has_ticket_access(ticket: Ticket):
    if not current_user.is_authenticated:
        return False
    group = ticket.group
    if group:
        if not (current_user.is_staff or is_member_of(group)):
            return False
    elif not (current_user.is_staff or ticket.user.id == current_user.id):
        return False
    return True


def requires_ticket_access(f):
    @functools.wraps(f)
    def wrapper(*args, **kwds):
        data = args[0]
        ticket_id = data.get("id")
        if not ticket_id:
            return socket_error("Invalid ticket ID")
        ticket = Ticket.query.filter_by(id=ticket_id, course=get_course()).one_or_none()
        if not has_ticket_access(ticket):
            return socket_unauthorized()
        kwds["ticket"] = ticket
        return f(*args, **kwds)

    return wrapper


def has_group_access(group: Group):
    if not current_user.is_authenticated:
        return socket_unauthorized()
    if not group:
        return False
    if not (current_user.is_staff or is_member_of(group)):
        return False
    return True


def requires_group_access(f):
    @functools.wraps(f)
    def wrapper(*args, **kwds):
        data = args[0]
        group_id = data.get("id")
        if not group_id:
            return socket_error("Invalid group ID")
        group = Group.query.filter_by(id=group_id, course=get_course()).one_or_none()
        if not has_group_access(group):
            return socket_unauthorized()
        kwds["group"] = group
        return f(*args, **kwds)

    return wrapper


@api("connect")
def connect(data=None):
    if not current_user.is_authenticated:
        pass

    current_user.heartbeat_time = datetime.datetime.utcnow()

    entity_type = None

    if data:
        url = data["url"]
        path = urlparse(url).path
        path = path.strip("/")
        parts = path.split("/")
        if len(parts) == 2:
            if parts[1].isdigit():
                entity_type = parts[0]
                entity_id = int(parts[1])

    if entity_type == "tickets":
        entity = Ticket.query.filter_by(course=get_course(), id=entity_id).one_or_none()
    elif entity_type == "appointments":
        entity = Appointment.query.filter_by(
            course=get_course(), id=entity_id
        ).one_or_none()
    elif entity_type == "groups":
        entity = Group.query.filter_by(course=get_course(), id=entity_id).one_or_none()
    else:
        entity = None

    emit_state(
        [
            "tickets",
            "appointments",
            "assignments",
            "groups",
            "locations",
            "current_user",
            "config",
            "presence",
        ],
        entity,
    )


def get_magic_word(mode=None, data=None, time_offset=0):
    if mode is None:
        mode = (
            ConfigEntry.query.filter_by(
                course=get_course(), key="queue_magic_word_mode"
            )
            .one()
            .value
        )
    if mode == "none":
        return None

    if data is None:
        data = (
            ConfigEntry.query.filter_by(
                course=get_course(), key="queue_magic_word_data"
            )
            .one()
            .value
        )
    if mode == "text":
        return data
    if mode == "timed_numeric":
        # We don't need fancy ultra-secure stuff here
        # A basic server-side time-based, seeded RNG is enough
        # Seed data should be in the form 'a:b:c:d', where:
        # a: 8-byte seed (in hexadecimal)
        # b: Downsampling interval (in seconds)
        # c: Minimum generated number (in unsigned decimal)
        # d: Maximum generated number (in unsigned decimal)
        data = data.split(":")
        # Downsample time to allow for temporal leeway
        rand = random.Random()
        timestamp = time.time() // int(data[1])
        # Seeded RNG
        rand.seed("{}.{}".format(timestamp + time_offset, data[0]))
        return str(rand.randint(int(data[2]), int(data[3]))).zfill(len(data[3]))
    raise Exception("Unrecognized queue magic word mode")


def check_magic_word(magic_word):
    mode = (
        ConfigEntry.query.filter_by(course=get_course(), key="queue_magic_word_mode")
        .one()
        .value
    )
    if mode == "none":
        return True
    data = (
        ConfigEntry.query.filter_by(course=get_course(), key="queue_magic_word_data")
        .one()
        .value
    )
    if mode == "timed_numeric":
        # Allow for temporal leeway from lagging clients/humans
        for offset in (0, -1, 1):
            if get_magic_word(mode, data, time_offset=offset) == magic_word:
                return True
        return False
    return get_magic_word(mode, data) == magic_word


@api("refresh_magic_word")
@is_staff
def refresh_magic_word():
    return {"magic_word": get_magic_word()}


@api("create")
@logged_in
def create(form):
    """Stores a new ticket to the persistent database, and emits it to all
    connected clients.
    """
    is_open = (
        ConfigEntry.query.filter_by(course=get_course(), key="is_queue_open")
        .one()
        .value
        == "true"
    )
    party_enabled = (
        ConfigEntry.query.filter_by(course=get_course(), key="party_enabled")
        .one()
        .value
        == "true"
    )
    private_party_tickets_allowed = (
        ConfigEntry.query.filter_by(
            course=get_course(), key="allow_private_party_tickets"
        )
        .one()
        .value
        == "true"
    )
    if not is_open or (party_enabled and not private_party_tickets_allowed):
        return socket_error("The queue is closed", category="warning")
    if not check_magic_word(form.get("magic_word")):
        return socket_error("Invalid magic_word", category="warning")
    my_ticket = Ticket.for_user(current_user)
    if my_ticket:
        return socket_error(
            "You are already on the queue",
            category="warning",
            ticket_id=my_ticket.ticket_id,
        )
    assignment_id = form.get("assignment_id")
    location_id = form.get("location_id")
    question = form.get("question")
    description = form.get("description")

    call_link = form.get("call-link", "")
    doc_link = form.get("doc-link", "")

    location = Location.query.filter_by(
        course=get_course(), id=location_id
    ).one_or_none()
    if not location:
        return socket_error(
            "Unknown location (id: {})".format(location_id), category="warning"
        )

    call_link = process_call_link(call_link, location)

    if doc_link:
        doc_link = urljoin("https://", doc_link)

    # Create a new ticket and add it to persistent storage
    if assignment_id is None or location_id is None or not question:
        return socket_error("You must fill out all the fields", category="warning")

    assignment = Assignment.query.filter_by(
        course=get_course(), id=assignment_id
    ).one_or_none()
    if not assignment:
        return socket_error(
            "Unknown assignment (id: {})".format(assignment_id), category="warning"
        )

    ticket = Ticket(
        status=TicketStatus.pending,
        user=current_user,
        assignment=assignment,
        location=location,
        question=question,
        description=description,
        course=get_course(),
        call_url=call_link,
        doc_url=doc_link,
    )

    db.session.add(ticket)
    db.session.commit()

    emit_event(ticket, TicketEventType.create)
    return socket_redirect(ticket_id=ticket.id)


def get_tickets(ticket_ids):
    return Ticket.query.filter(
        Ticket.id.in_(ticket_ids), Ticket.course == get_course()
    ).all()


def get_next_ticket(location=None):
    """Return the user's first assigned but unresolved ticket.
    If none exist, return the first pending student re-request.
    If none exist, return to the first unassigned ticket.

    If a location is passed in, only returns a next ticket from
    provided location.
    """
    ticket = Ticket.query.filter(
        Ticket.helper_id == current_user.id,
        Ticket.status == TicketStatus.assigned,
        Ticket.course == get_course(),
    ).first()
    if not ticket:
        ticket = Ticket.query.filter(
            Ticket.status == TicketStatus.rerequested,
            Ticket.helper_id == current_user.id,
            Ticket.course == get_course(),
        ).order_by(Ticket.sort_key)
        ticket = ticket.first()
    if not ticket:
        ticket = Ticket.query.filter(
            Ticket.status == TicketStatus.rerequested,
            Ticket.helper_id == None,
            Ticket.course == get_course(),
        ).order_by(Ticket.sort_key)
        ticket = ticket.first()
    if not ticket:
        ticket = Ticket.query.filter(
            Ticket.status == TicketStatus.pending, Ticket.course == get_course()
        ).order_by(Ticket.sort_key)
        if location:
            ticket = ticket.filter(Ticket.location == location)
        ticket = ticket.first()
    if ticket:
        return socket_redirect(ticket_id=ticket.id)
    else:
        return socket_redirect()


@api("next")
@is_staff
def next_ticket(ticket_ids):
    return get_next_ticket()


def is_member_of(group):
    return any(
        attendance.user.id == current_user.id
        for attendance in group.attendees
        if attendance.group_attendance_status == GroupAttendanceStatus.present
    )


@api("delete")
@logged_in
def delete(ticket_ids):
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        ticket_group = ticket.group
        if not (
            current_user.is_staff
            or ticket.user.id == current_user.id
            or ticket_group
            and is_member_of(ticket_group)
        ):
            return socket_unauthorized()
        ticket.status = TicketStatus.deleted
        emit_event(ticket, TicketEventType.delete)
    db.session.commit()


@api("resolve")
@logged_in
def resolve(data):
    """Gets ticket_ids and an optional argument 'local'.
    Resolves all ticket_ids. If 'local' is set, then
    will only return a next ticket from the same location
    where the last ticket was resolved from.
    """
    ticket_ids = data.get("ticket_ids")
    local = data.get("local", False)
    location = None
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        if not (current_user.is_staff or ticket.user.id == current_user.id):
            return socket_unauthorized()
        ticket.status = TicketStatus.resolved
        if local:
            location = ticket.location
        emit_event(ticket, TicketEventType.resolve)
    db.session.commit()
    return get_next_ticket(location)


@api("juggle")
@is_staff
def juggle(data):
    """
    Gets ticket_ids and places them all on the juggle queue for the corresponding staff member
    """
    ticket_ids = data.get("ticket_ids")
    tickets = get_tickets(ticket_ids)
    location = None
    for ticket in tickets:
        ticket.status = TicketStatus.juggled
        ticket.hold_time = datetime.datetime.utcnow()
        ticket.rerequest_threshold = ticket.hold_time + datetime.timedelta(
            minutes=int(
                ConfigEntry.query.filter_by(course=get_course(), key="juggling_delay")
                .one()
                .value
            )
        )
        location = ticket.location
        emit_event(ticket, TicketEventType.juggle)
    db.session.commit()
    return get_next_ticket(location)


@api("assign")
@is_staff
def assign(ticket_ids):
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        ticket.status = TicketStatus.assigned

        ticket.helper_id = current_user.id
        emit_event(ticket, TicketEventType.assign)
    db.session.commit()


@api("return_to")
@is_staff
def return_to(ticket_ids):
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        ticket.status = TicketStatus.assigned

        ticket.helper_id = current_user.id
        emit_event(ticket, TicketEventType.return_to)

    db.session.commit()


@api("rerequest")
@logged_in
def rerequest(data):
    ticket_ids = data.get("ticket_ids")
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        if not ticket.user.id == current_user.id:
            return socket_unauthorized()

        if ticket.rerequest_threshold > datetime.datetime.utcnow():
            return socket_unauthorized()

        ticket.status = TicketStatus.rerequested
        ticket.rerequest_time = datetime.datetime.utcnow()

        emit_event(ticket, TicketEventType.rerequest)

    db.session.commit()


@api("cancel_rerequest")
@logged_in
def cancel_rerequest(data):
    ticket_ids = data.get("ticket_ids")
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        if not ticket.user.id == current_user.id:
            return socket_unauthorized()

        ticket.status = TicketStatus.juggled
        emit_event(ticket, TicketEventType.juggle)

    db.session.commit()


@api("release_holds")
@is_staff
def release_holds(data):
    ticket_ids = data.get("ticket_ids")
    to_me = data.get("to_me")
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        if ticket.status in [TicketStatus.juggled, TicketStatus.rerequested]:
            ticket.helper_id = current_user.id if to_me else None
            emit_event(ticket, TicketEventType.hold_released)
    db.session.commit()

    return socket_redirect()


@api("unassign")
@is_staff
def unassign(ticket_ids):
    tickets = get_tickets(ticket_ids)
    for ticket in tickets:
        ticket.status = TicketStatus.pending
        ticket.helper_id = None
        emit_event(ticket, TicketEventType.unassign)
    db.session.commit()


@api("shuffle_tickets")
@is_staff
def shuffle_tickets(ticket_ids):
    tickets = get_tickets(ticket_ids)
    ticket_sort_keys = [ticket.sort_key for ticket in tickets]
    random.shuffle(ticket_sort_keys)
    for ticket, sort_key in zip(tickets, ticket_sort_keys):
        ticket.sort_key = sort_key
        emit_event(ticket, TicketEventType.shuffled)
    db.session.commit()


@api("load_ticket")
@is_staff
def load_ticket(ticket_id):
    if not ticket_id:
        return socket_error("Invalid ticket ID")
    ticket = Ticket.query.filter_by(course=get_course(), id=ticket_id).one_or_none()
    if ticket:
        return ticket_json(ticket)


def apply_ticket_update(data, ticket=None):
    if not ticket:
        ticket_id = data["id"]
        ticket = Ticket.query.filter_by(id=ticket_id, course=get_course()).one()
    if "description" in data:
        ticket.description = data["description"]
    if "location_id" in data:
        ticket.location = Location.query.filter_by(
            course=get_course(), id=data["location_id"]
        ).one()
    if "assignment_id" in data:
        ticket.assignment = Assignment.query.filter_by(
            course=get_course(), id=data["assignment_id"]
        ).one()
    if "question" in data:
        ticket.question = data["question"]


@api("update_ticket")
@requires_ticket_access
def update_ticket(data, ticket):
    apply_ticket_update(data, ticket)
    db.session.commit()
    emit_event(ticket, TicketEventType.update)
    return ticket_json(ticket)


@api("update_tickets")
@is_staff
def update_tickets(arr):
    ticket_ids = [data["id"] for data in arr]
    tickets = Ticket.query.filter(
        Ticket.id.in_(ticket_ids), Ticket.course == get_course()
    ).all()
    ticket_dict = {ticket.id: ticket for ticket in tickets}
    for data in arr:
        apply_ticket_update(data, ticket_dict[data["id"]])
    db.session.commit()
    return emit_state(["tickets"])


@api("add_assignment")
@is_staff
def add_assignment(data):
    name = data["name"]
    assignment = Assignment(name=name, course=get_course())
    db.session.add(assignment)
    db.session.commit()

    emit_state(["assignments"])
    db.session.refresh(assignment)
    return assignment_json(assignment)


@api("update_assignment")
@is_staff
def update_assignment(data):
    assignment = Assignment.query.filter_by(course=get_course(), id=data["id"]).one()
    if "name" in data:
        assignment.name = data["name"]
    if "visible" in data:
        assignment.visible = data["visible"]
    db.session.commit()

    emit_state(["assignments"])
    return assignment_json(assignment)


@api("add_location")
@is_staff
def add_location(data):
    name = data["name"]
    if name == "Online":
        return
    location = Location(name=name, course=get_course(), link="", online=False)
    db.session.add(location)
    db.session.commit()

    emit_state(["locations"])
    db.session.refresh(location)
    return location_json(location)


@api("update_location")
@is_staff
def update_location(data):
    location = Location.query.filter_by(id=data["id"], course=get_course()).one()
    if "name" in data:
        location.name = data["name"]
    if "visible" in data:
        location.visible = data["visible"]
    if "link" in data:
        location.link = data["link"]
    if "online" in data:
        location.online = data["online"]
    if location.link:
        location.online = True
    location.link = location.link and urljoin("https://", location.link)
    if location.name == "Online":
        return
    db.session.commit()

    emit_state(["locations"])
    return location_json(location)


@api("update_config")
@is_staff
def update_config(data):
    config = {}
    if "keys" in data:
        config = {k: v for k, v in zip(data["keys"], data["values"]) if v is not None}
    elif "key" in data:
        config = {data["key"]: data["value"]}
    if "queue_magic_word_mode" in config:
        if config["queue_magic_word_mode"] == "timed_numeric":
            config["queue_magic_word_data"] = (
                format(random.randrange(2 ** 64), "x") + ":60:0:9999"
            )
    for key, value in config.items():
        entry = ConfigEntry.query.filter_by(key=key, course=get_course()).one()
        entry.value = value
    db.session.commit()

    emit_state(["config", "locations"])

    return config_json()


@api("assign_staff_appointment")
@is_staff
def assign_staff_appointment(appointment_id):
    appointment = Appointment.query.filter(
        Appointment.id == appointment_id, Appointment.course == get_course()
    ).one()
    appointment.helper_id = current_user.id
    db.session.commit()
    emit_appointment_event(appointment, "staff_unassigned")


@api("unassign_staff_appointment")
@is_staff
def unassign_staff_appointment(appointment_id):
    appointment = Appointment.query.filter(
        Appointment.id == appointment_id, Appointment.course == get_course()
    ).one()
    appointment.helper_id = None
    db.session.commit()

    emit_appointment_event(appointment, "staff_unassigned")


@api("assign_appointment")
@logged_in
def assign_appointment(data):
    user_id = current_user.id

    if current_user.is_staff:
        user = User.query.filter_by(
            email=data["email"], course=get_course()
        ).one_or_none()
        if not user:
            return socket_error("Email could not be found")
        user_id = user.id

    old_signup = AppointmentSignup.query.filter_by(
        appointment_id=data["appointment_id"], user_id=user_id, course=get_course()
    ).one_or_none()

    appointment = Appointment.query.filter_by(
        id=data["appointment_id"], course=get_course()
    ).one()  # type = Appointment

    if not current_user.is_staff:
        daily_threshold = int(
            ConfigEntry.query.filter_by(
                key="daily_appointment_limit", course=get_course()
            )
            .one()
            .value
        )
        weekly_threshold = int(
            ConfigEntry.query.filter_by(
                key="weekly_appointment_limit", course=get_course()
            )
            .one()
            .value
        )
        pending_threshold = int(
            ConfigEntry.query.filter_by(
                key="simul_appointment_limit", course=get_course()
            )
            .one()
            .value
        )

        start = appointment.start_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_start = start - datetime.timedelta(days=appointment.start_time.weekday())
        week_end = week_start + datetime.timedelta(days=7)
        num_this_week = (
            AppointmentSignup.query.join(AppointmentSignup.appointment)
            .filter(
                week_start < Appointment.start_time,
                Appointment.start_time < week_end,
                AppointmentSignup.user_id == current_user.id,
                AppointmentSignup.attendance_status != AttendanceStatus.excused,
            )
            .count()
            - int(bool(old_signup))
        )
        if num_this_week >= weekly_threshold:
            return socket_error(
                "You have already signed up for {} OH slots this week".format(
                    weekly_threshold
                )
            )

        day_end = start + datetime.timedelta(days=1)
        num_today = (
            AppointmentSignup.query.join(AppointmentSignup.appointment)
            .filter(
                start < Appointment.start_time,
                Appointment.start_time < day_end,
                AppointmentSignup.user_id == current_user.id,
                AppointmentSignup.attendance_status != AttendanceStatus.excused,
            )
            .count()
            - int(bool(old_signup))
        )
        if num_today >= daily_threshold:
            return socket_error(
                "You have already signed up for {} OH slots for the same day".format(
                    daily_threshold
                )
            )

        num_pending = (
            AppointmentSignup.query.join(AppointmentSignup.appointment)
            .filter(
                Appointment.status == AppointmentStatus.pending,
                AppointmentSignup.user_id == current_user.id,
            )
            .count()
            - int(bool(old_signup))
        )
        if num_pending >= pending_threshold:
            return socket_error(
                "You have already signed up for {} OH slots that have not yet occurred.".format(
                    pending_threshold
                )
            )

    old_attendance = (
        old_signup.attendance_status if old_signup else AttendanceStatus.unknown
    )

    if appointment.status != AppointmentStatus.pending:
        return socket_error("Appointment is not pending")

    if old_signup:
        db.session.delete(old_signup)
        db.session.commit()

    if (
        len(appointment.signups) >= appointment.capacity
        and not current_user.is_staff
        and not old_signup
    ):
        return socket_error("Appointment is at full capacity")

    signup = AppointmentSignup(
        appointment_id=data["appointment_id"],
        user_id=user_id,
        assignment_id=data["assignment_id"],
        question=data["question"],
        description=data["description"],
        attendance_status=old_attendance,
        course=get_course(),
    )
    db.session.add(signup)
    db.session.commit()

    emit_appointment_event(appointment, "student_assigned")


@api("unassign_appointment")
@logged_in
def unassign_appointment(signup_id):
    old_signup = AppointmentSignup.query.filter_by(
        id=signup_id, course=get_course()
    ).first()

    appointment = old_signup.appointment

    if (
        not current_user.is_staff
        and (not old_signup or old_signup.user_id != current_user.id)
        or appointment.status != AppointmentStatus.pending
    ):
        return socket_unauthorized()

    db.session.delete(old_signup)
    db.session.commit()

    emit_appointment_event(appointment, "student_unassigned")


@api("load_appointment")
@is_staff
def load_appointment(appointment_id):
    if not appointment_id:
        return socket_error("Invalid appointment ID")
    appointment = Appointment.query.filter_by(
        id=appointment_id, course=get_course()
    ).one()
    if appointment:
        return appointments_json(appointment)


@api("set_appointment_status")
@is_staff
def set_appointment_status(data):
    appointment_id = data["appointment"]
    status = data["status"]
    appointment = Appointment.query.filter_by(
        id=appointment_id, course=get_course()
    ).one()
    appointment.status = AppointmentStatus[status]
    db.session.commit()

    emit_appointment_event(appointment, "status_change")


@api("mark_attendance")
@is_staff
def mark_attendance(data):
    signup_id = data["signup_id"]
    attendance_status = data["status"]

    signup = AppointmentSignup.query.filter_by(id=signup_id, course=get_course()).one()
    signup.attendance_status = AttendanceStatus[attendance_status]
    db.session.commit()

    emit_appointment_event(signup.appointment, "attendance_marked")


@api("toggle_visibility")
@is_staff
def toggle_visibility(appointment_id):
    appointment = Appointment.query.filter_by(
        id=appointment_id, course=get_course()
    ).one()
    if appointment.status == AppointmentStatus.hidden:
        appointment.status = AppointmentStatus.pending
    elif appointment.status == AppointmentStatus.pending:
        appointment.status = AppointmentStatus.hidden
    else:
        return socket_error(
            "Cannot show/hide appointment that is in progress / completed"
        )
    db.session.commit()

    emit_appointment_event(appointment, "visibility_toggled")


@api("delete_appointment")
@is_staff
def delete_appointment(appointment_id):
    appointment = Appointment.query.filter_by(
        id=appointment_id, course=get_course()
    ).one()
    db.session.delete(appointment)
    db.session.commit()

    emit_state(["appointments"])


@api("upload_appointments")
@is_staff
def upload_appointments(data):
    sheet_url = data["sheetUrl"]
    sheet_name = data["sheetName"]

    try:
        data = read_spreadsheet(course="cs61a", url=sheet_url, sheet_name=sheet_name)

        locations = {}

        def get_location(name):
            if name not in locations:
                locations[name] = Location.query.filter_by(
                    name=name, course=get_course()
                ).one()
            return locations[name]

        helpers = {}

        def get_helper(email, name):
            if not email:
                return None
            if email not in helpers:
                helper = User.query.filter_by(
                    email=email, course=get_course()
                ).one_or_none()
                if not helper:
                    helper = User(
                        name=name, email=email, is_staff=True, course=get_course()
                    )
                    db.session.add(helper)
                    db.session.commit()
                helpers[email] = helper
            return helpers[email]

        header = data[0]
        for row in data[1:]:
            start_date_raw = row[header.index("Day")]
            start_time_raw = row[header.index("Start Time")]
            start_time = datetime.datetime.strptime(
                start_date_raw + " " + start_time_raw, "%B %d %I:%M %p"
            )
            start_time = start_time.replace(year=datetime.datetime.now().year)

            appointment = Appointment(
                start_time=start_time,
                duration=datetime.timedelta(
                    minutes=int(row[header.index("Duration (mins)")])
                ),
                capacity=int(row[header.index("Capacity")]),
                location=get_location(row[header.index("Location")]),
                status=AppointmentStatus.hidden,
                helper=get_helper(
                    row[header.index("Email")], row[header.index("Name")]
                ),
                course=get_course(),
            )
            db.session.add(appointment)

        db.session.commit()
    except Exception as e:
        return socket_error("Internal Error:" + str(e))
    emit_state(["appointments"])


@api("update_staff_online_setup")
@is_staff
def update_staff_online_setup(data):
    if "staff-call-link" in data:
        current_user.call_url = data["staff-call-link"] and urljoin(
            "https://", data["staff-call-link"]
        )
    if "staff-doc-link" in data:
        current_user.doc_url = data["staff-doc-link"] and urljoin(
            "https://", data["staff-doc-link"]
        )
    db.session.add(current_user)

    db.session.commit()

    emit_state(["current_user"])
    emit_state(["tickets", "appointments"])


@api("send_chat_message")
@logged_in
def send_chat_message(data):
    mode = data.get("mode")
    event_id = data["id"]

    message = ChatMessage(user=current_user, course=get_course(), body=data["content"])

    if mode == "appointment":
        appointment = Appointment.query.filter_by(
            course=get_course(), id=event_id
        ).one()
        if not current_user.is_staff:
            for signup in appointment.signups:
                if signup.user.id == current_user.id:
                    break
            else:
                return socket_unauthorized()

        message.appointment = appointment

    elif mode == "ticket":
        ticket = Ticket.query.filter_by(course=get_course(), id=event_id).one()
        if not current_user.is_staff and ticket.user_id != current_user.id:
            return socket_unauthorized()
        message.ticket = ticket

    elif mode == "group":
        group = Group.query.filter_by(course=get_course(), id=event_id).one()
        if not current_user.is_staff and not is_member_of(group):
            return socket_unauthorized()
        message.group = group

    db.session.add(message)
    db.session.commit()

    if mode == "appointment":
        emit_appointment_event(message.appointment, "message_sent")
    elif mode == "ticket":
        emit_event(message.ticket, TicketEventType.message_sent)
    elif mode == "group":
        emit_group_event(message.group, "message_sent")


@api("bulk_appointment_action")
@is_staff
def bulk_appointment_action(data):
    action = data["action"]
    ids = data.get("ids", None)
    if action == "open_all_assigned":
        appointments = Appointment.query.filter(
            Appointment.course == get_course(),
            Appointment.helper_id != None,
            Appointment.status == AppointmentStatus.hidden,
        )
        if ids is not None:
            appointments = appointments.filter(Appointment.id.in_(ids))
        appointments.update(
            {Appointment.status: AppointmentStatus.pending}, synchronize_session=False
        )
    elif action == "resolve_all_past":
        appointments = Appointment.query.filter(
            Appointment.course == get_course(),
            Appointment.helper_id != None,
            Appointment.start_time < get_current_time(),
            Appointment.status == AppointmentStatus.pending,
        )
        if ids is not None:
            appointments = appointments.filter(Appointment.id.in_(ids))
        appointments = appointments.all()
        Appointment.query.filter(
            Appointment.id.in_({x.id for x in appointments})
        ).update(
            {Appointment.status: AppointmentStatus.resolved}, synchronize_session=False
        )
    elif action == "remove_all_unassigned":
        appointments = (
            Appointment.query.filter(
                Appointment.course == get_course(), Appointment.helper_id == None
            )
            .outerjoin(Appointment.signups)
            .group_by(Appointment)
            .having(func.count(AppointmentSignup.id) == 0)
        )
        if ids is not None:
            appointments = appointments.filter(Appointment.id.in_(ids))
        appointments = appointments.all()
        Appointment.query.filter(
            Appointment.id.in_({x.id for x in appointments})
        ).delete(False)
    db.session.commit()
    emit_state(["appointments"])


@api("list_users")
@is_staff
def list_users():
    return [user_json(user) for user in User.query.filter_by(course=get_course()).all()]


@api("get_user")
@logged_in
def get_user(user_id):
    if user_id != current_user.id and not current_user.is_staff:
        return socket_unauthorized()
    user = User.query.filter_by(course=get_course(), id=user_id).one()
    tickets = (
        Ticket.query.filter(
            or_(Ticket.user_id == user.id, Ticket.helper_id == user.id),
            Ticket.course == get_course(),
        )
        .order_by(desc(Ticket.created))
        .options(joinedload(Ticket.user, innerjoin=True))
        .options(joinedload(Ticket.helper))
        .options(joinedload(Ticket.group))
        .all()
    )
    appointments = (
        Appointment.query.filter(
            Appointment.helper_id == user.id, Appointment.course == get_course()
        )
        .order_by(desc(Appointment.start_time))
        .options(joinedload(Appointment.helper))
        .options(
            joinedload(Appointment.signups).joinedload(
                AppointmentSignup.user, innerjoin=True
            )
        )
        .all()
    )
    signups = (
        AppointmentSignup.query.join(AppointmentSignup.appointment)
        .filter(
            AppointmentSignup.user_id == user.id, Appointment.course == get_course()
        )
        .options(
            joinedload(AppointmentSignup.appointment).options(
                joinedload(Appointment.helper)
            )
        )
        .order_by(desc(Appointment.start_time))
        .all()
    )

    return {
        "user": user_json(user),
        "tickets": [ticket_json(ticket) for ticket in tickets],
        "appointments": (
            [appointments_json(appointment) for appointment in appointments]
            + [appointments_json(signup.appointment) for signup in signups]
        ),
    }


def apply_appointment_update(data, appointment=None):
    if not appointment:
        appointment_id = data["id"]
        appointment = Appointment.query.filter_by(
            id=appointment_id, course=get_course()
        ).one()
    if "description" in data:
        appointment.description = data["description"]
    if "location_id" in data:
        appointment.location = Location.query.filter_by(
            course=get_course(), id=data["location_id"]
        ).one()
    if "helper_id" in data:
        if data["helper_id"] is None:
            appointment.helper = None
        else:
            appointment.helper = User.query.filter_by(
                course=get_course(), id=data["helper_id"]
            ).one()


@api("update_appointment")
@is_staff
def update_appointment(data):
    apply_appointment_update(data)
    db.session.commit()
    return emit_state(["appointments"])


@api("update_appointments")
@is_staff
def update_appointments(arr):
    appointment_ids = [data["id"] for data in arr]
    appointments = Appointment.query.filter(
        Appointment.id.in_(appointment_ids), Appointment.course == get_course()
    ).all()
    appointment_dict = {appointment.id: appointment for appointment in appointments}
    for data in arr:
        apply_appointment_update(data, appointment_dict[data["id"]])
    db.session.commit()
    return emit_state(["appointments"])


@api("test_slack")
@is_staff
def test_slack():
    notif_config: CourseNotificationState = CourseNotificationState.query.filter_by(
        course=get_course()
    ).one()
    post_slack_message(
        message="This is a test message from the OH queue! Your default queue domain is {}. This channel will "
        "be used for all future notifications. To change the channel, visit auth.cs61a.org and "
        "update the channel associated with `oh-queue`.".format(notif_config.domain),
        purpose="oh-queue",
        course=get_course(),
    )


@api("appointment_summary")
@is_staff
def appointment_summary():
    send_appointment_summary(get_course())


def leave_current_groups():
    prev_attendance = GroupAttendance.query.filter_by(
        user_id=current_user.id, group_attendance_status=GroupAttendanceStatus.present
    ).one_or_none()
    if prev_attendance:
        prev_attendance.group_attendance_status = GroupAttendanceStatus.gone
        db.session.commit()
        other_attendances = GroupAttendance.query.filter_by(
            group=prev_attendance.group,
            group_attendance_status=GroupAttendanceStatus.present,
        ).all()

        if prev_attendance.group.ticket and (
            not other_attendances
            or prev_attendance.group.ticket.user_id == current_user.id
        ):
            # delete the ticket if the group is closed or the ticket creator leaves
            prev_attendance.group.ticket.status = TicketStatus.deleted
            emit_event(prev_attendance.group.ticket, TicketEventType.delete)

        if not other_attendances:
            prev_attendance.group.group_status = GroupStatus.resolved
            db.session.commit()
            emit_group_event(prev_attendance.group, "group_closed")
        else:
            emit_group_event(prev_attendance.group, "group_left")


def process_call_link(link, location):
    if link:
        if location.link:
            if all(x.isdigit() for x in link):
                return "Breakout Room " + link
        else:
            return urljoin("https://", link)
    return link


@api("create_group")
@logged_in
def create_group(form):
    party_enabled = ConfigEntry.query.filter_by(
        course=get_course(), key="party_enabled"
    ).one()
    if party_enabled.value != "true":
        return socket_error("Party mode is not enabled.", category="warning")

    assignment_id = form.get("assignment_id")
    location_id = form.get("location_id")
    question = form.get("question")

    call_link = form.get("call-link", "")
    doc_link = form.get("doc-link", "")

    location = Location.query.filter_by(
        course=get_course(), id=location_id
    ).one_or_none()
    if not location:
        return socket_error(
            "Unknown location (id: {})".format(location_id), category="warning"
        )

    call_link = process_call_link(call_link, location)

    if doc_link:
        doc_link = urljoin("https://", doc_link)

    if assignment_id is None or location_id is None or not question:
        return socket_error("You must fill out all the fields", category="warning")

    assignment = Assignment.query.filter_by(
        course=get_course(), id=assignment_id
    ).one_or_none()
    if not assignment:
        return socket_error(
            "Unknown assignment (id: {})".format(assignment_id), category="warning"
        )

    if location.name == "Online" and not call_link:
        return socket_error("You must fill out all the fields", category="warning")

    leave_current_groups()

    group = Group(
        group_status=GroupStatus.active,
        assignment=assignment,
        location=location,
        description="Hi! Anyone else want to work on this problem with me?",
        question=question,
        course=get_course(),
        call_url=call_link,
        doc_url=doc_link,
    )

    db.session.add(group)

    group_attendance = GroupAttendance(
        group=group,
        user=current_user,
        group_attendance_status=GroupAttendanceStatus.present,
        course=get_course(),
    )

    db.session.add(group_attendance)

    db.session.commit()

    emit_group_event(group, "group_created")

    return socket_redirect(group_id=group.id)


@api("load_group")
@is_staff
def load_group(group_id):
    if not group_id:
        return socket_error("Invalid group ID")
    group = Group.query.filter_by(id=group_id, course=get_course()).one()
    if group:
        return group_json(group)


@api("join_group")
def join_group(group_id):
    group = Group.query.filter_by(
        id=group_id, course=get_course(), group_status=GroupStatus.active
    ).one()
    leave_current_groups()
    attendance = GroupAttendance(
        group=group,
        user=current_user,
        group_attendance_status=GroupAttendanceStatus.present,
        course=get_course(),
    )
    db.session.add(attendance)
    db.session.commit()

    emit_group_event(group, "group_joined")

    return socket_redirect(group_id=group_id)


@api("leave_group")
def leave_group(group_id):
    leave_current_groups()
    return socket_redirect()


def apply_group_update(data, group=None):
    if not group:
        group_id = data["id"]
        group = Group.query.filter_by(id=group_id, course=get_course()).one()
    if "description" in data:
        group.description = data["description"]
    if "assignment_id" in data:
        group.assignment = Assignment.query.filter_by(
            course=get_course(), id=data["assignment_id"]
        ).one()
    if "question" in data:
        group.question = data["question"]
    if "location_id" in data:
        group.location = Location.query.filter_by(
            course=get_course(), id=data["location_id"]
        ).one()


@api("update_group")
@requires_group_access
def update_group(data, group):
    apply_group_update(data, group)
    db.session.commit()
    emit_group_event(group, "update_group")
    return group_json(group)


@api("update_groups")
@is_staff
def update_groups(arr):
    group_ids = [data["id"] for data in arr]
    groups = Group.query.filter(
        Group.id.in_(group_ids), Group.course == get_course()
    ).all()
    group_dict = {group.id: group for group in groups}
    for data in arr:
        apply_group_update(data, group_dict[data["id"]])
    db.session.commit()
    return emit_state(["groups"])


@api("create_group_ticket")
@requires_group_access
def create_group_ticket(data, group):
    is_queue_open = ConfigEntry.query.filter_by(
        course=get_course(), key="is_queue_open"
    ).one()
    if is_queue_open.value != "true":
        return socket_error("The queue is closed", category="warning")
    if (
        group.ticket
        and group.ticket.status not in [TicketStatus.resolved, TicketStatus.deleted]
        or Ticket.for_user(current_user)
    ):
        return socket_error("You are already on the queue", category="warning")

    ticket = Ticket(
        status=TicketStatus.pending,
        user=current_user,
        assignment=group.assignment,
        location=group.location,
        question=group.question,
        description="This ticket is associated with a group.",
        course=get_course(),
        call_url=group.call_url,
        doc_url=group.doc_url,
    )

    db.session.add(ticket)
    db.session.commit()

    group.ticket = ticket
    db.session.commit()

    emit_event(ticket, TicketEventType.create)
    emit_group_event(group, "group_ticket_created")


@api("delete_group")
@is_staff
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id, course=get_course()).one()
    delete_group_worker(group, emit=True)
    db.session.commit()


def delete_group_worker(group, *, emit):
    group.group_status = GroupStatus.resolved
    for attendance in group.attendees:
        attendance.group_attendance_status = GroupAttendanceStatus.gone
    if emit:
        emit_group_event(group, "group_closed")
    if group.ticket:
        group.ticket.status = TicketStatus.deleted
        if emit:
            emit_event(group.ticket, TicketEventType.delete)


@app.route("/debug")
def debug():
    try:
        emit_state(
            [
                "tickets",
                "assignments",
                "groups",
                "locations",
                "current_user",
                "config",
                "appointments",
            ]
        )
    except AttributeError:
        pass
    return "<body></body>"
