from base64 import b64encode

from ics import Calendar, Event
import pytz

from common.course_config import get_domain
from common.rpc.mail import send_email
from common.course_config import format_coursecode, get_course
from oh_queue.models import AppointmentSignup


def send_appointment_reminder(signup: AppointmentSignup):
    """
    Sends an appointment reminder in the form of an email to the user who signed up.
    The email has a set title and subject. The body is filled in with information
    specific to the appointment, but otherwise follows a template. The email is
    sent to the User who just signed up for the appointment.

    :param signup: The object associated with the OH appointment
    :type signup: AppointmentSignup
    """
    appointment = signup.appointment
    user = signup.user

    c = Calendar()
    e = Event()
    e.name = f"{format_coursecode(get_course())} Appointment"
    e.begin = pytz.timezone("America/Los_Angeles").localize(appointment.start_time)
    e.end = e.begin + appointment.duration
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
