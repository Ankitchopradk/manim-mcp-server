from manim import *


class FunctionGraph(Scene):
    """Axes with a parabola and a dot moving along it (no LaTeX needed)."""

    def construct(self):
        axes = Axes(x_range=[-3, 3, 1], y_range=[0, 9, 3], x_length=6, y_length=4)
        curve = axes.plot(lambda x: x**2, color=YELLOW)
        dot = Dot(axes.c2p(-3, 9), color=RED)

        self.play(Create(axes))
        self.play(Create(curve))
        self.add(dot)
        self.play(MoveAlongPath(dot, curve), run_time=3)
        self.wait(0.5)
