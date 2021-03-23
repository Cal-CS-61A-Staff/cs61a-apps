import click
import cv2

from examtool.api.database import get_exam, get_roster
from examtool.api.watermark_decoder import decode_watermark
from examtool.api.watermarks import Point
from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--image",
    prompt=True,
    type=click.Path(exists=True),
    help="The image or screenshot you wish to identify.",
)
def identify_watermark(exam, image):
    """
    Identify the student from a screenshot containing a watermark.
    """
    img = cv2.imread(image)
    img = cv2.copyMakeBorder(img, 100, 100, 100, 100, cv2.BORDER_CONSTANT)

    corners = []
    bits = []

    def handle_click(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            bits.append(Point(x, y))
            cv2.circle(img, (x, y), 5, (255, 0, 0), -1)
        if event == cv2.EVENT_RBUTTONDOWN:
            corners.append(Point(x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)

    cv2.namedWindow("image")
    cv2.setMouseCallback("image", handle_click)
    while True:
        cv2.imshow("image", img)
        if cv2.waitKey(20) & 0xFF == 13:
            break

    print(decode_watermark(get_exam(exam=exam), get_roster(exam=exam), corners, bits))
