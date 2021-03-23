from base64 import b64encode

from ics import Calendar, Event

from common.course_config import get_domain
from common.rpc.mail import send_email
from common.course_config import format_coursecode, get_course
from oh_queue.models import AppointmentSignup


def send_appointment_reminder(signup: AppointmentSignup):
    appointment = signup.appointment
    user = signup.user

    c = Calendar()
    e = Event()
    e.name = f"{format_coursecode(get_course())} Appointment"
    e.begin = appointment.start_time
    e.end = appointment.start_time + appointment.duration
    e.location = appointment.location.name
    c.events.add(e)

    helper_msg = (
        f"It will be led by {appointment.helper.name}.\n" if appointment.helper else ""
    )

    send_email(
        sender="OH Queue <cs61a@berkeley.edu>",
        target=user.email,
        subject=f"{format_coursecode(get_course())} Appointment Scheduled",
        body=(
            f"""
    Hi {user.short_name},

    An appointment has been scheduled for you using the {format_coursecode(get_course())} OH Queue. 
    It is at {appointment.start_time.strftime('%A %B %-d, %I:%M%p')} Pacific Time, at location {appointment.location.name}.
    {helper_msg}
    To edit or cancel this appointment, go to https://{get_domain()}.

    Best,
    The 61A Software Team
    """.strip()
        ),
        attachments={"invite.ics": b64encode(str(c).encode("utf-8")).decode("ascii")},
    )
