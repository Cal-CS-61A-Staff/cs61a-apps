import base64
import os

from common.rpc.auth_utils import set_token_path
from common.rpc.ag_master import upload_zip, create_assignment


class Autograder:
    def __init__(self, course):
        self.course = course
        set_token_path(f"{os.path.expanduser('~')}/.sicp_token")

    def upload_zip(self, zip_file):
        """
        Uploads `filename` zip and returns the download url, overriding any
        existing filesOverrides existing
        """
        assert zip_file.endswith(".zip"), "Upload Error"

        with open(zip_file, "rb") as f:
            upload_zip(
                course=self.course,
                name=zip_file,
                file=base64.b64encode(f.read()).decode("ascii"),
            )

    def create_assignment(
        self, assign, script, zip_file, batch_size=100, grading_base="https://okpy.org"
    ):
        return create_assignment(
            name=assign,
            command=script,
            file=zip_file,
            batch_size=batch_size,
            grading_base=grading_base,
            course=self.course,
        )
