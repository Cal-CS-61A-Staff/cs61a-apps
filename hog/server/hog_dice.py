from gui_files.svg import create_graphic, draw_rect, draw_circle, draw_line, draw_triangle, write_text

def draw_dice(num):
    x = 0
    y = 0
    width = 100
    height = 100
    graphic = create_graphic(width, height)
    draw_rect(graphic, x, y, width, height, stroke="pink", fill="white")
    spacing = width / (1 + num)
    for _ in range(0, num):
        x += spacing
        y += spacing
        draw_circle(graphic, x, y, 30)
    return graphic