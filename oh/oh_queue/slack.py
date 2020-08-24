import atexit
import threading
from collections import defaultdict, namedtuple
from datetime import timedelta, datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from common.course_config import COURSE_DOMAINS
from common.rpc.auth import post_slack_message
from oh_queue.models import (
    Ticket,
    TicketStatus,
    Appointment,
    get_current_time,
    AppointmentStatus,
    db,
    ConfigEntry,
)

pinged_appointments = set()
alerted_appointments = set()
last_queue_ping = {}

last_appointment_notif = {}


def make_send(course):
    def send(message):
        post_slack_message(course=course, message=message, purpose="oh-queue")

    return send


def worker(app):
    with app.app_context():
        for course, domain in COURSE_DOMAINS.items():
            queue_url = "https://{}".format(domain)
            send = make_send(course)

            if (
                ConfigEntry.query.filter_by(key="slack_notif_long_queue", course=course)
                .one()
                .value
                == "true"
            ):
                # check for overlong queue
                if course not in last_queue_ping or datetime.now() - last_queue_ping[
                    course
                ] > timedelta(hours=8):
                    queue_len = Ticket.query.filter_by(
                        course=course, status=TicketStatus.pending
                    ).count()
                    if queue_len > 10:
                        send(
                            "<!here> The OH queue currently has more than {} students waiting. "
                            "If you can, please drop by and help! Go to the <{}|OH Queue> to see more.".format(
                                queue_len, queue_url
                            )
                        )
                        last_queue_ping[course] = datetime.now()

            if (
                ConfigEntry.query.filter_by(
                    key="slack_notif_missed_appt", course=course
                )
                .one()
                .value
                == "true"
            ):
                # check for appointments that should have started
                appointments = Appointment.query.filter(
                    Appointment.start_time < get_current_time() - timedelta(minutes=2),
                    Appointment.status == AppointmentStatus.pending,
                    Appointment.course == course,
                ).all()

                for appointment in appointments:
                    if appointment.id in alerted_appointments:
                        continue
                    if len(appointment.signups) > 0:
                        appointment_url = "{}/appointments/{}".format(
                            queue_url, appointment.id
                        )
                        if appointment.helper:
                            if appointment.id not in pinged_appointments:
                                send(
                                    "<!{email}> You have an appointment right now that hasn't started, and students are "
                                    "waiting! Your appointment is {location}. Go to the <{appointment_url}|OH Queue> to see more "
                                    "information.".format(
                                        email=appointment.helper.email,
                                        location="*Online*"
                                        if appointment.location.name == "Online"
                                        else "at *{}*".format(
                                            appointment.location.name
                                        ),
                                        appointment_url=appointment_url,
                                    )
                                )
                                pinged_appointments.add(appointment.id)
                            else:
                                send(
                                    "<!here> {name}'s appointment is right now but hasn't started, and students are "
                                    "waiting! The appointment is {location}. Can anyone available help out? "
                                    "Go to the <{appointment_url}|OH Queue> to see more information.".format(
                                        name=appointment.helper.name,
                                        location="*Online*"
                                        if appointment.location.name == "Online"
                                        else "at *{}*".format(
                                            appointment.location.name
                                        ),
                                        appointment_url=appointment_url,
                                    )
                                )
                                alerted_appointments.add(appointment.id)
                        else:
                            send(
                                "<!here> An appointment is scheduled for right now that hasn't started, and students "
                                "are waiting! *No staff member has signed up for it!* The appointment is {location}. "
                                "Go to the <{appointment_url}|OH Queue> to see more information.".format(
                                    location="*Online*"
                                    if appointment.location.name == "Online"
                                    else "at *{}*".format(appointment.location.name),
                                    appointment_url=appointment_url,
                                )
                            )
                            alerted_appointments.add(appointment.id)
                    else:
                        if not appointment.helper:
                            send(
                                "An appointment is scheduled right now that hasn't started, but no students have "
                                "signed up *and no staff member was assigned*. I am automatically resolving the "
                                "appointment. Be careful - a student _could_ have signed up since the appointment "
                                "wasn't hidden."
                            )
                        appointment.status = AppointmentStatus.resolved

            if (
                ConfigEntry.query.filter_by(
                    key="slack_notif_appt_summary", course=course
                )
                .one()
                .value
                == "true"
            ):
                if (
                    course in last_appointment_notif
                    and last_appointment_notif[course].day != get_current_time().day
                ):
                    # send appointment summary
                    last_appointment_notif[course] = get_current_time()
                    send_appointment_summary(app, course)
                elif course not in last_appointment_notif:
                    last_appointment_notif[course] = get_current_time()

        db.session.commit()


def send_appointment_summary(app, course):
    appointments = Appointment.query.filter(
        get_current_time() < Appointment.start_time,
        Appointment.start_time < get_current_time() + timedelta(days=1),
        Appointment.status == AppointmentStatus.pending,
        Appointment.course == course,
    ).all()

    Upcoming = namedtuple("Upcoming", ["total", "nonempty", "start_time"])
    staff = defaultdict(lambda: Upcoming(0, 0, None))
    for appointment in appointments:
        if appointment.helper:
            old = staff[appointment.helper.email]
            staff[appointment.helper.email] = old._replace(
                total=old.total + 1,
                nonempty=old.nonempty + int(bool(appointment.signups)),
                start_time=min(
                    old.start_time or appointment.start_time, appointment.start_time
                ),
            )

    if not staff:
        return

    make_send(course)(
        [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hi all! You all have appointments today (Pacific Time).",
                },
            },
            {"type": "divider"},
            *[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<!{email}>\nYou have *{total}* appointments, "
                        "*{nonempty}* of which currently have students signed up. "
                        "Your first appointment begins at {time} Pacific Time, "
                        "in about {delta} hours from the time of this message.".format(
                            email=email,
                            total=upcoming.total,
                            nonempty=upcoming.nonempty,
                            time=upcoming.start_time.strftime("%I:%M%p"),
                            delta=(upcoming.start_time - get_current_time()).seconds
                            // 3600,
                        ),
                    },
                }
                for email, upcoming in staff.items()
            ],
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Remember that if you can't make your appointment you should unassign "
                    "yourself and notify someone to replace you. If you want to remove "
                    "yourself from an appointment with no students, just hit the "
                    ":double_vertical_bar: icon or just resolve the appointment.",
                },
            },
        ]
    )


def fire_thread(app):
    threading.Thread(target=worker, args=(app,)).start()


def start_flask_job(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fire_thread, args=(app,), trigger="interval", minutes=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
