from json import dumps, loads
from typing import List

import numpy as np
from tqdm import tqdm

from examtool.api.scramble import scramble
from examtool.api.watermarks import Point, get_watermark_points


def decode_watermark(exam_data, roster, corners: List[Point], bits: List[Point]):
    """
    Assume x coord increases from left to right, y increases from top to bottom
    """
    observed_points = correct_watermark_bits(corners, bits)
    email_distances = [
        [email, bit_distance(observed_points, exam_data, email)]
        for email, _ in tqdm(roster)
    ]
    email_distances.sort(key=lambda x: x[1])
    return email_distances[:10]


def bit_distance(observed_points: List[Point], exam_data, email):
    scrambled_exam = scramble(email, loads(dumps(exam_data)))
    expected_points = get_watermark_points(scrambled_exam["watermark"]["value"])
    assert len(observed_points) >= len(expected_points) / 2, "Too few observed bits"
    costs = []
    for observed_point in observed_points:
        closest = min(expected_points, key=observed_point.dist)
        costs.append(
            observed_point.dist(closest) ** 2
        )  # large penalty for misalignment
    costs.sort()
    del costs[-5:]
    return sum(costs) / len(costs)


def correct_watermark_bits(corners: List[Point], bits: List[Point]):
    assert len(corners) == 4, "All four corners must be selected"
    corners.sort(key=lambda pt: pt.x)
    left, right = corners[:2], corners[2:]
    left.sort(key=lambda pt: pt.y)
    right.sort(key=lambda pt: pt.y)
    top_left, bottom_left = left
    top_right, bottom_right = right

    def compute_basis_map(points):
        *base, ref = points
        A = np.array(
            [
                *zip(*base),
                [1, 1, 1],
            ]
        )
        b = np.array([*ref, 1])
        coeffs = np.linalg.solve(A, b)
        return A * coeffs

    source_transform = compute_basis_map(
        [
            top_left,
            top_right,
            bottom_right,
            bottom_left,
        ]
    )

    target_transform = compute_basis_map(
        [Point(5, 5), Point(105, 5), Point(105, 105), Point(5, 105)]
    )

    full_transform = target_transform @ np.linalg.inv(source_transform)

    homogenized_bits = full_transform @ np.vstack(
        [np.array(list(zip(*bits))), np.ones(len(bits))]
    )

    return [
        Point(x % 100, y % 100)
        for x, y in zip(
            homogenized_bits[0] / homogenized_bits[2],
            homogenized_bits[1] / homogenized_bits[2],
        )
    ]
