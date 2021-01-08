from colorama import Style


def pretty_print(emoji, msg):
    print(f"{emoji}{Style.BRIGHT} {msg} {Style.RESET_ALL}{emoji}")
