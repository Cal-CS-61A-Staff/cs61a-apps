from flask import Flask

from admins_client import create_admins_client
from auth_client import create_auth_client
from common.oauth_client import create_oauth_client
from domains_client import create_domains_client
from google_client import create_google_client
from management_client import create_management_client
from piazza_client import create_piazza_client
from ed_client import create_ed_client
from slack_client import create_slack_client

app = Flask(__name__)

if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-account-auth")
create_management_client(app)
create_auth_client(app)
create_admins_client(app)
create_google_client(app)
create_piazza_client(app)
create_ed_client(app)
create_slack_client(app)
create_domains_client(app)


if __name__ == "__main__":
    app.run(debug=True)
