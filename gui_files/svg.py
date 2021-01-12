
class SVGRect():

    def __init__(self, x, y, width, height, fill):
        self.x = x 
        self.y = y 
        self.width = width 
        self.height = height
        self.fill = fill

    def __str__(self):
        return """<rect x="{0}" y="{1}" width="{2}" height="{3}" fill="{4}" />""".format(
            self.x, self.y, self.width, self.height, self.fill)

class SVGCircle():

    def __init__(self, x, y, radius, fill):
        self.x = x 
        self.y = y 
        self.radius = radius
        self.fill = fill

    def __str__(self):
        return """<circle cx="{0}" cy="{1}" r="{2}" fill="{3}" />""".format(
            self.x, self.y, self.radius, self.fill)

class SVGText():

    def __init__(self, x, y, text, fill):
        self.x = x 
        self.y = y 
        self.text = text 
        self.fill = fill

    def __str__(self):
        return """<text x="{0}" y="{1}" fill="{2}">{3}</text>""".format(
            self.x, self.y, self.fill, self.text)

class SVGGraphic():

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shapes = []

    def draw_rect(self, x, y, width, height, fill):
        self.shapes.append(SVGRect(x, y, width, height, fill))

    def draw_circle(self, x, y, radius, fill):
        self.shapes.append(SVGCircle(x, y, radius, fill))

    def write_text(self, x, y, text, fill):
        self.shapes.append(SVGText(x, y, text, fill))
        
    def __str__(self):
        shapes = "".join(str(shape) for shape in self.shapes)
        return """
        <svg width="{0}" height="{1}" xmlns="http://www.w3.org/2000/svg">
            {2}
        </svg>
        """.format(self.width, self.height, shapes)
    
def create_graphic(width, height):
    return SVGGraphic(width, height)

def draw_rect(graphic, x, y, width, height, fill="black"):
    graphic.draw_rect(x, y, width, height, fill)

def draw_circle(graphic, x, y, radius, fill="black"):
    graphic.draw_circle(x, y, radius, fill)

def write_text(graphic, x, y, text, fill="black"):
    graphic.write_text(x, y, text, fill)
