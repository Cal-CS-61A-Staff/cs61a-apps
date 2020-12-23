from flask import redirect, request

from auth_utils import course_oauth_secure
from common.db import connect_db
from common.rpc.auth import get_course
from common.rpc.domains import add_domain
from common.url_for import url_for
from common.html import make_row


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS domains_config (
                domain varchar(128), 
                course varchar(128)
             )"""
        )


init_db()


def create_domains_client(app):
    def domains_help(course):
        with connect_db() as db:
            ret = db(
                "SELECT domain FROM domains_config WHERE course=(%s)", [course]
            ).fetchall()
        client_names = [
            make_row(domain, url_for("remove_domain", domain=domain, course=course))
            for domain, in ret
        ]
        register_domain = f"""
            Register new domain:
            <form action="/domains/{course}/register_domain" method="post">
                <input name="domain_name" type="text" placeholder="seating.cs61a.org">
                <input type="submit">
            </form>

            View the status of your domain setup at 
            <a href="https://domains.cs61a.org/">domains.cs61a.org</a>
        """
        return "<h3>Domains</h3>" + register_domain + "<p>".join(client_names)

    app.help_info.add(domains_help)

    @app.route("/domains/<course>/register_domain", methods=["POST"])
    @course_oauth_secure()
    def register_domain(course):
        domain_name = request.form["domain_name"]
        with connect_db() as db:
            ret = db(
                "SELECT * FROM domains_config WHERE domain = (%s)", [domain_name]
            ).fetchone()
            if ret:
                return "domain already registered", 409
            db("INSERT INTO domains_config VALUES (%s, %s)", [domain_name, course])

        add_domain(course=course, domain=domain_name, noreply=True)

        return redirect("/")

    @app.route("/domains/<course>/remove_domain", methods=["POST"])
    @course_oauth_secure()
    def remove_domain(course):
        domain = request.args["domain"]
        with connect_db() as db:
            db(
                "DELETE FROM domains_config WHERE domain = (%s) AND course = (%s)",
                [domain, course],
            )
        return redirect("/")

    @get_course.bind(app)
    def handle_get_course(domain, **_kwargs):
        # note: deliberately not secured, not sensitive data
        with connect_db() as db:
            [course] = db(
                "SELECT course FROM domains_config WHERE domain = (%s)", [domain]
            ).fetchone()
        return course
