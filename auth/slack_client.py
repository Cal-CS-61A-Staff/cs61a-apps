from flask import redirect, request

from auth_utils import course_oauth_secure, key_secure
from common.db import connect_db
from common.rpc.auth import post_slack_message, slack_workspace_name
from common.rpc.slack import list_channels, post_message
from common.url_for import url_for
from html_utils import make_row


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS slack_config (
                course varchar(128),
                workspace varchar(128)
            )"""
        )
        db(
            """CREATE TABLE IF NOT EXISTS slack_channels (
                course varchar(128),
                purpose varchar(128),
                channel varchar(128),
                channel_id varchar(128)
            )"""
        )


init_db()


def create_slack_client(app):
    def slack_help(course):
        with connect_db() as db:
            workspace = db(
                "SELECT workspace FROM slack_config WHERE course=(%s)", [course]
            ).fetchone()
            workspace = workspace[0] if workspace else ""

            registered_channels = db(
                "SELECT purpose, channel, channel_id FROM slack_channels WHERE course=(%s)",
                [course],
            ).fetchall()

        try:
            channels = list_channels(course=course)
        except:
            registration = """
            To register Slack channels, first go to 
            <a href="https://slack.cs61a.org">slack.cs61a.org</a> 
            to add the bot to your workspace.
            """
        else:
            channels = [
                f"<option value=\"{channel['name']}\">{channel['name']}</option>"
                for channel in channels
            ]
            registration = f"""
                Register a new Slack channel.
                <form action="/slack/{course}/register_channel" method="post">
                    <input name="purpose" type="text" placeholder="Purpose">
                    <select name="channel">
                        {channels}
                    </select>
                    <input type="submit">
                </form>
            """

        registered_channels_list = "".join(
            make_row(
                f"{purpose} associated with #{channel} (id: {channel_id})",
                url_for("remove_channel", course=course, purpose=purpose),
            )
            for purpose, channel, channel_id in registered_channels
        )

        return f"""
        <h3> Slack Configuration </h3>
        <p>
        Current workspace: <a href="https://{workspace}.slack.com">{workspace}.slack.com</a>
        </p>
        {registration}
        {registered_channels_list}
        </form>
        <p>
        To configure, go to <a href="/slack/{course}/config">Slack Config</a>.
        """

    app.help_info.add(slack_help)

    @slack_workspace_name.bind(app)
    @key_secure
    def workspace_name(course):
        with connect_db() as db:
            workspace = db(
                "SELECT workspace FROM slack_config WHERE course=(%s)", [course]
            ).fetchone()
        if workspace:
            return workspace[0]

    @app.route("/slack/<course>/config", methods=["GET"])
    @course_oauth_secure()
    def slack_config(course):
        return """
            Enter Slack workspace url.
            <form action="/slack/{}/set_config" method="post">
                <label>
                    Slack Workspace <br />
                    <input name="workspace" type="text" placeholder="cs61a.slack.com"> <br />
                </label>
                <label>
                <input type="submit">
            </form>
        """.format(
            course
        )

    @app.route("/slack/<course>/set_config", methods=["POST"])
    @course_oauth_secure()
    def set_slack_config(course):
        workspace = request.form["workspace"].split(".")[0]

        with connect_db() as db:
            existing = db(
                "SELECT course FROM slack_config WHERE workspace=(%s) AND course <>(%s)",
                [workspace, course],
            ).fetchone()
            if existing:
                return "{} is already using that workspace.".format(existing)
            db("DELETE FROM slack_config WHERE course=(%s)", [course])
            db("INSERT INTO slack_config VALUES (%s, %s)", [course, workspace])

        return redirect("/")

    @app.route("/slack/<course>/register_channel", methods=["POST"])
    @course_oauth_secure()
    def register_channel(course):
        purpose = request.form["purpose"]
        channel_name = request.form["channel"]

        channel_data = list_channels(course=course)

        for channel in channel_data:
            if channel["name"] == channel_name:
                channel_id = channel["id"]
                break
        else:
            return "Channel not found.", 404

        with connect_db() as db:
            ret = db(
                "SELECT * FROM slack_channels WHERE course = (%s) AND purpose = (%s)",
                [course, purpose],
            ).fetchone()
            if ret:
                return "Channel with same purpose already registered", 409
            db(
                "INSERT INTO slack_channels VALUES (%s, %s, %s, %s)",
                [course, purpose, channel_name, channel_id],
            )

        return redirect("/")

    @app.route("/slack/<course>/remove_channel", methods=["POST"])
    @course_oauth_secure()
    def remove_channel(course):
        purpose = request.args["purpose"]
        with connect_db() as db:
            db(
                "DELETE FROM slack_channels WHERE course=(%s) AND purpose=(%s)",
                [course, purpose],
            )
        return redirect("/")

    @post_slack_message.bind(app)
    @key_secure
    def handle_post_message(course, message, purpose):
        with connect_db() as db:
            channel_id, = db(
                "SELECT channel_id FROM slack_channels WHERE course=(%s) AND purpose=(%s)",
                [course, purpose],
            ).fetchone()

        post_message(course=course, message=message, channel=channel_id)

        return ""
