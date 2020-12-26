import os
from collections import namedtuple

COOKIE_IS_POPUP = "is_popup"
COOKIE_SHORTLINK_REDIRECT = "shortlink"
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ServerFile = namedtuple(
    "ServerFile",
    ["short_link", "full_name", "url", "data", "share_ref", "discoverable"],
)
CSV_ROOT = "https://docs.google.com/spreadsheets/d/1v3N9fak7a-pf70zBhAIUuzplRw84NdLP5ptrhq_fKnI/"
NOT_FOUND = "NOT_FOUND"
NOT_AUTHORIZED = "NOT_AUTHORIZED"
NOT_LOGGED_IN = "NOT_LOGGED_IN"
