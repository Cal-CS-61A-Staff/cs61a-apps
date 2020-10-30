import os

from examtool.api.server_delegate import server_only

from sendgrid import SendGridAPIClient


@server_only
def send_email(*, exam, data):
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    sg.client.mail.send.post(data)


@server_only
def send_email_batch(*, exam, data_list):
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    for data in data_list:
        sg.client.mail.send.post(data)


@server_only
def get_api_key(*, exam):
    return os.environ.get("SENDGRID_API_KEY")


def send_email_local(key, data):
    sg = SendGridAPIClient(key)
    response = sg.client.mail.send.post(data)
    print(response.status_code)
    print(response.body)
    print(response.headers)


def send_email_local_safe(key, data, timeout=10):
    """
    Sends an email, and raises a BadResponse if either the response code is not
        2xx or it takes more than `timeout` seconds to respond
    """
    from func_timeout import func_timeout, FunctionTimedOut

    try:

        def do_send_email():
            sg = SendGridAPIClient(key)
            response = sg.client.mail.send.post(data)
            if not 200 <= response.status_code < 300:
                raise BadResponse(
                    "{}\n{}\n{}".format(
                        response.status_code, response.body, response.headers
                    )
                )

        func_timeout(timeout, do_send_email)
    except FunctionTimedOut:
        raise BadResponse("Timed out!")


class BadResponse(Exception):
    pass
