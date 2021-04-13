from colorama import Style


def pretty_print(emoji: str, msg: str):
    """Pretty prints a message.

    :param emoji: the emoji to wrap the message in
    :type emoji: str
    :param msg: the message to wrap with the emoji
    :type msg: str
    """
    print(f"{emoji}{Style.BRIGHT} {msg} {Style.RESET_ALL}{emoji}")
