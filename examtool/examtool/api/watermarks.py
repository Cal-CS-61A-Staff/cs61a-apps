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
    old_seed = int(random.random() * 100000)
    random.seed(seed)
    for _ in range(20):
        yield Point(random.randrange(100), random.randrange(100))
    random.seed(old_seed)


def create_watermark(seed, *, brightness, scale=2):
    graphic = SVGGraphic(100 * scale, 100 * scale)
    color = f"rgb({255 - brightness}, {255 - brightness / 2}, 0)"
    graphic.draw_line(0, 0, 10, 10, color)
    graphic.draw_line(0, 10, 10, 0, color)
    for x, y in get_watermark_points(seed):
        graphic.draw_rect(x * scale, y * scale, scale, scale, color, color)
    return str(graphic)
