import math


class Shape:
    def area(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

class Square(Rectangle):
    def __init__(self, side_length):
        super().__init__(side_length, side_length)

class Ellipse(Shape):
    def __init__(self, semi_major, semi_minor):
        self.semi_major = semi_major
        self.semi_minor = semi_minor

    def area(self):
        area = math.pi * self.semi_major * self.semi_minor
        return area

class Circle(Ellipse):
    def __init__(self, radius):
        super().__init__(radius, radius)

def calculate_total_area(shapes):
    return sum(shape.area() for shape in shapes if isinstance(shape, Shape))

def main():
    shapes = [Square(4), Rectangle(3, 5), Circle(3)]
    total_area = calculate_total_area(shapes)
    print("Total Area of Shapes:", total_area)

main()
