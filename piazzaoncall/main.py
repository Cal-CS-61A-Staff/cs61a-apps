from flask import Flask

from common.jobs import job

# from piazza_oc import Main
from ed_oc import Main

app = Flask(__name__)

if __name__ == "__main__":
    app.debug = True


@job(app, "ping_unread")
def run():
    Main().run()


if __name__ == "__main__":
    app.run(debug=True)
