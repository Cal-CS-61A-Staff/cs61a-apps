import re, requests
from os import getenv

from cachetools import TTLCache
from flask import request

import common.rpc as rpc

DOMAIN_COURSES = TTLCache(1000, 1800)
COURSE_ENDPOINTS = TTLCache(1000, 1800)
ENDPOINT_ID = TTLCache(1000, 1800)


def get_course(domain=None):
    if getenv("ENV") != "prod":
        return "cs61a"
    if not domain:
        domain = get_domain()
    if "pr" in domain:
        DOMAIN_COURSES[domain] = "cs61a"
    if domain not in DOMAIN_COURSES:
        DOMAIN_COURSES[domain] = rpc.auth.get_course(domain=domain)
    return DOMAIN_COURSES[domain]


def get_domain():
    return request.headers.get("X-Forwarded-For-Host") or request.headers["HOST"]


def get_endpoint(course=None):
    if getenv("ENV") != "prod":
        return "cal/cs61a/sp21"
    if not course:
        course = get_course()
    if course not in COURSE_ENDPOINTS:
        COURSE_ENDPOINTS[course] = rpc.auth.get_endpoint(course=course)
    return COURSE_ENDPOINTS[course]


def get_course_id(course=None):
    if getenv("ENV") != "prod":
        return 1
    if not course:
        course = get_course()
    if course not in ENDPOINT_ID:
        ENDPOINT_ID[course] = rpc.auth.get_endpoint_id(course=course)
    return ENDPOINT_ID[course]


def is_admin(email, course=None):
    if getenv("ENV") != "prod":
        return True
    if not course:
        course = get_course()
    return rpc.auth.is_admin(email=email, course=course, force_course=course)


def is_admin_token(access_token, course=None):
    ret = requests.get(
        "https://okpy.org/api/v3/user/", params={"access_token": access_token}
    )
    return ret.status_code == 200 and is_admin(
        ret.json()["data"]["email"],
        course=course,
    )


def format_coursecode(course):
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course)
    return m and (m.group(1) + " " + m.group(2)).upper()
