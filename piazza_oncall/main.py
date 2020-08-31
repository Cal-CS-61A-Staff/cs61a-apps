from flask import Flask

from common.jobs import job
from oncall import Main

app = Flask(__name__)

if __name__ == "__main__":
    app.debug = True


@job(app, "ping_unread")
def run():
    Main().run()


if __name__ == "__main__":
    app.run(debug=True)
