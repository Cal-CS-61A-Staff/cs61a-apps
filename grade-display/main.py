from flask import Flask

from common.jobs import job
from fa20 import update

app = Flask(__name__)

if __name__ == "__main__":
    app.debug = True


@job(app, "update_grades")
def run():
    update()


if __name__ == "__main__":
    app.run(debug=True)
