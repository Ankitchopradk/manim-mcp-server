from manim import *


class Simple3D(ThreeDScene):
    """Lightweight 3D scene: a cube and a sphere with camera rotation."""

    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES)
        cube = Cube(side_length=1.5, fill_opacity=0.6, fill_color=BLUE)
        sphere = Sphere(radius=0.6, resolution=(12, 12)).shift(RIGHT * 2.5)
        self.play(Create(cube), Create(sphere))
        self.begin_ambient_camera_rotation(rate=0.4)
        self.wait(2)
        self.stop_ambient_camera_rotation()
