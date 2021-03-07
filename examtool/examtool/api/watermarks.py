from __future__ import annotations

import random
from dataclasses import dataclass
from examtool.api.utils import as_list

from examtool.gui_files.svg import SVGGraphic


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __iter__(self):
        yield self.x
        yield self.y

    def dist(self, other: Point):
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2


@as_list
def get_watermark_points(seed):
    if isinstance(seed, dict):
        seed = seed["entropy"][0]
    old_seed = int(random.random() * 100000)
    random.seed(seed)
    for _ in range(20):
        yield Point(random.randrange(100), random.randrange(100))
    random.seed(old_seed)


def create_watermark(seed, *, scale=2):
    graphic = SVGGraphic(100 * scale, 100 * scale)
    graphic.draw_line(0, 0, 10, 10, "orange")
    graphic.draw_line(0, 10, 10, 0, "orange")
    for x, y in get_watermark_points(seed):
        graphic.draw_rect(x * scale, y * scale, scale, scale, "orange", "orange")
    return str(graphic)
