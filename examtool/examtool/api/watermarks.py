import random

from examtool.gui_files.svg import SVGGraphic


def create_watermark(seed):
    if isinstance(seed, dict):
        seed = seed["entropy"][0]

    old_seed = int(random.random() * 100000)
    random.seed(seed)
    graphic = SVGGraphic(100, 100)
    for _ in range(20):
        x, y = random.randrange(100), random.randrange(100)
        graphic.draw_rect(x, y, 1, 1, "yellow", "yellow")
    random.seed(old_seed)
    return str(graphic)
