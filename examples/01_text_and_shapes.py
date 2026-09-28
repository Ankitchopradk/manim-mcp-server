from manim import *


class TextAndShapes(Scene):
    def construct(self):
        title = Text("Hello, Manim MCP!")
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))

        circle = Circle(color=BLUE)
        square = Square(color=GREEN)
        self.play(Create(circle))
        self.play(Transform(circle, square))
        self.wait(0.5)
