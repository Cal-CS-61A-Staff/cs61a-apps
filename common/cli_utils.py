from colorama import Style


def pretty_print(emoji, msg):
    """Pretty prints a message.

    :param emoji: the emoji to wrap the message in
    :param msg: the message to wrap with the emoji
    """
    print(f"{emoji}{Style.BRIGHT} {msg} {Style.RESET_ALL}{emoji}")
