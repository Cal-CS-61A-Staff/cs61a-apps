import re, requests
from os import getenv

from cachetools import TTLCache
from flask import request
from common.rpc import auth

DOMAIN_COURSES = TTLCache(1000, 1800)
COURSE_ENDPOINTS = TTLCache(1000, 1800)
ENDPOINT_ID = TTLCache(1000, 1800)


def get_course(domain=None):
    """Gets the course code of the course that owns the current domain, using
    :meth:`~common.rpc.auth.get_domain`.

    :param domain: the domain name in question, inferred using
        :meth:`~common.course_config.get_domain` if omitted
    :type domain: str

    :return: the course code, such as "cs61a"
    """
    if getenv("ENV") != "prod":
        return "cs61a"
    if not domain:
        domain = get_domain()
    if "pr" in domain:
        DOMAIN_COURSES[domain] = "cs61a"
    if domain not in DOMAIN_COURSES:
        DOMAIN_COURSES[domain] = auth.get_course(domain=domain)
    return DOMAIN_COURSES[domain]


def get_domain():
    """Gets the domain that this request is being made on.

    :return: the domain name, based on request headers
    """
    return request.headers.get("X-Forwarded-For-Host") or request.headers["HOST"]


def get_endpoint(course=None):
    """Gets a course's most recent Okpy endpoint, typically the current
    semester's, using :meth:`~common.rpc.auth.get_endpoint`.

    :param course: the course code, such as "cs61a", inferred using
        :meth:`~common.course_config.get_course` if omitted
    :type course: str

    :return: the Okpy endpoint, such as "cal/cs61a/sp21"
    """
    if getenv("ENV") != "prod":
        return "cal/cs61a/sp21"
    if not course:
        course = get_course()
    if course not in COURSE_ENDPOINTS:
        COURSE_ENDPOINTS[course] = auth.get_endpoint(course=course)
    return COURSE_ENDPOINTS[course]


def get_course_id(course=None):
    """Gets a course's most recent Okpy course ID, typically the current
    semester's, using :meth:`~common.rpc.auth.get_endpoint_id`.

    :param course: the course code, such as "cs61a", inferred using
        :meth:`~common.course_config.get_course` if omitted
    :type course: str

    :return: the Okpy endpoint, such as 707
    """
    if getenv("ENV") != "prod":
        return 1
    if not course:
        course = get_course()
    if course not in ENDPOINT_ID:
        ENDPOINT_ID[course] = auth.get_endpoint_id(course=course)
    return ENDPOINT_ID[course]


def is_admin(email, course=None):
    """Returns whether or not an email address belongs to an admin
    for the given course, using :meth:`~common.rpc.auth.is_admin`.

    :param email: the email address in question
    :type email: str
    :param course: the course code, such as "cs61a", inferred using
        :meth:`~common.course_config.get_course` if omitted
    :type course: str

    :return: ``True`` if the user is an admin, ``False`` otherwise
    """
    if getenv("ENV") != "prod":
        return True
    if not course:
        course = get_course()
    return auth.is_admin(email=email, course=course, force_course=course)


def is_admin_token(access_token, course=None):
    """Returns whether or not an Okpy access token belongs to an admin
    for the given course.

    :param access_token: the Okpy access token in question
    :type access_token: str
    :param course: the course code, such as "cs61a", inferred using
        :meth:`~common.course_config.get_course` if omitted
    :type course: str

    :return: ``True`` if the user is an admin, ``False`` otherwise
    """
    ret = requests.get(
        "https://okpy.org/api/v3/user/", params={"access_token": access_token}
    )
    return ret.status_code == 200 and is_admin(
        ret.json()["data"]["email"],
        course=course,
    )


def format_coursecode(course):
    """Formats a course code is a pretty way, separating the department from
    the course number.

    :param course: the course code, such as "cs61a"
    :type course: str

    :return: prettified course code, such as "CS 61A"
    """
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course)
    return m and (m.group(1) + " " + m.group(2)).upper()
