import random
import re
from string import punctuation

import requests

from integration import Integration
from staff import STAFF, STAFF_EMOJI

cached_names = {}


class EmojiIntegration(Integration):
    @property
    def message(self):
        return process(self._message, self._token)


def get_name(id, token):
    if id in cached_names:
        return cached_names[id]

    resp = requests.post(
        "https://slack.com/api/users.info", {"token": token, "user": id}
    )
    out = resp.json()["user"]["real_name"]
    cached_names[id] = out
    return out


def can_get_name(id):
    if " " in id or "@" in id:
        return False
    return True


def get_staff(word, token):
    candidates = set()
    if (
        word.startswith("<@")
        and word.endswith(">")
        and token
        and can_get_name(word[2:-1])
    ):
        word = get_name(word[2:-1], token)
    for staff in STAFF:
        if (staff.firstName + " " + staff.lastName).lower() == word.lower():
            candidates.add(staff)
    for staff in STAFF:
        if word.lower() == (staff.firstName + " " + staff.lastName[0]).lower():
            candidates.add(staff)
    for staff in STAFF:
        if staff.firstName.lower() == word.lower():
            candidates.add(staff)
    if candidates:
        return random.choice(list(candidates))


def strip_punctuation(word):
    if word.startswith("<@") and word.endswith(">"):
        return "", word, ""
    rest = word.lstrip(punctuation)
    leading = word[: len(word) - len(rest)]
    stripped = rest.rstrip(punctuation)
    trailing = rest[len(stripped) :]
    return leading, stripped, trailing


def has_staff_emoji(text):
    emojis = re.findall(":.+?:", text)
    for emoji in emojis:
        if emoji in STAFF_EMOJI:
            return True
    return False


def process(text, token):
    text = text.replace("<@", " <@")
    text = text.replace("  <@", " <@")
    if text.startswith(" <@"):
        text = text[1:]
    words = text.split(" ")

    if has_staff_emoji(text):
        return text

    for i, word in enumerate(words):
        if not words[i]:
            continue

        if i != len(words) - 1:
            next_word = words[i + 1]
            combined = word + " " + next_word
            leading, stripped, trailing = strip_punctuation(combined)
            staff = get_staff(stripped, token)
            if staff is not None:
                words[i] = leading + combined + f" ({staff.emoji}) " + trailing
                words[i + 1] = ""
                continue

        leading, stripped, trailing = strip_punctuation(word)
        staff = get_staff(stripped, token)
        if staff is None:
            continue
        words[i] = leading + stripped + f" ({staff.emoji})" + trailing
    return " ".join(words)
