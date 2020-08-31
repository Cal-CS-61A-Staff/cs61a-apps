from common.rpc.auth import post_slack_message

client_name = None


def send(message, course):
    post_slack_message(course=course, message=message, purpose="piazza-reminder")
