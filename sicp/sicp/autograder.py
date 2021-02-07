import base64
import requests
import os

from common.rpc.auth_utils import get_token, refresh_token, set_token_path
from common.rpc.ag_master import upload_zip, create_assignment


class Autograder:
    def __init__(self, course):
        self.course = course

        set_token_path(f"{os.path.expanduser('~')}/.sicp_token")
        r = requests.get(
            "https://okpy.org/api/v3/user/?access_token={}".format(get_token())
        )
        if not r.ok:
            refresh_token()

    def upload_zip(self, zip_file):
        """
        Uploads `filename` zip and returns the download url, overriding any
        existing filesOverrides existing
        """
        assert zip_file.endswith(".zip"), "Upload Error"

        with open(zip_file, "rb") as f:
            upload_zip(
                token=get_token(),
                course=self.course,
                name=zip_file,
                file=base64.b64encode(f.read()).decode("ascii"),
            )

    def create_assignment(self, assign, script, zip_file):
        return create_assignment(
            name=assign,
            command=script,
            file=zip_file,
            course=self.course,
            token=get_token(),
        )
