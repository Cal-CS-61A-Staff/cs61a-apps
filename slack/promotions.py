def make_promo_block(message):
    quoted_message = "\n".join(">" + x for x in message.split("\n"))
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Your message includes content that I can improve! It could look like: \n{}\nDo you want to activate this bot for your posts on this Slack workspace?".format(
                    quoted_message
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Yes, activate the bot!"},
                    "style": "primary",
                    "value": "activate",
                    "url": "https://slack.apps.cs61a.org",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Maybe later..."},
                    "value": "maybe_later",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "No, never ask me again."},
                    "style": "danger",
                    "value": "never_ask_again",
                    "confirm": {
                        "title": {"type": "plain_text", "text": "Are you sure?"},
                        "text": {
                            "type": "mrkdwn",
                            "text": "Imagine how good your posts could look!",
                        },
                        "confirm": {"type": "plain_text", "text": "Do it."},
                        "deny": {
                            "type": "plain_text",
                            "text": "Stop, I've changed my mind!",
                        },
                    },
                },
            ],
        },
    ]
