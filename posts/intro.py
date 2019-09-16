from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph import VisualGraph

class GenericGraphPath(Scene):

    path_vertices = [
        (-2.5, -1.5, 0),
        (-3, -0.3, 0),
        (-0.5, -0.6, 0),
        (1, -2.4, 0),
        (2.1, -1, 0),
        (-1, 1.3, 0),
        (1.8, 1.5, 0),
        (3.1, 0.5, 0),
    ]

    def construct(self):
        self.step1()
        self.step2()

    def step1(self):
        self.start = Circle(
            color=GREEN,
            stroke_width=3,
            opacity=1,
            fill_opacity=1,
            radius=0.3,
        )
        self.start.move_to(self.path_vertices[0])
        self.end = Circle(
            color=RED,
            stroke_width=3,
            opacity=1,
            fill_opacity=1,
            radius=0.3,
        )
        self.end.move_to(self.path_vertices[-1])

        self.add_foreground_mobjects(self.start, self.end)

        self.play(
            ShowCreation(self.start),
            ShowCreation(self.end),
        )

        self.p = Polygon(
            *self.path_vertices,
            *self.path_vertices[-2::-1],  # This is just a line in two directions.
            color=YELLOW,
            stroke_width=DEFAULT_STROKE_WIDTH * 2,
        )
        self.play(ShowCreation(self.p), run_time=2, rate_func=lambda t: t/2)

        anims = []
        self.vertices = [self.start, ]
        for vertex in self.path_vertices[1:-1]:
            dot = Circle(
                fill_color='#306998',
                color='#FFE873',
                stroke_width=3,
                opacity=1,
                fill_opacity=1,
                radius=0.3,
            )
            dot.move_to(vertex)
            self.vertices.append(dot)
            anims.append(ShowCreation(dot))

        self.vertices.append(self.end)
        self.play(LaggedStart(*anims))

        self.play(LaggedStart(*(ApplyMethod(obj.scale, 1.5) for obj in self.vertices)))

        self.play(LaggedStart(*(ApplyMethod(obj.scale, 2/3) for obj in self.vertices)))
        self.add_foreground_mobjects(self.p)
        self.add_foreground_mobjects(*self.vertices)

    def step2(self):
        self.graph = VisualGraph(
            'video1.graph',
            self,
            show_key=False,
            radius=0.3,
        )
        # Only move some vertices to the front.
        anim1, anim2 = self.graph.draw_vertices(play=False)
        self.play(anim1)
        self.add_foreground_mobjects(*(
            vertex
            for vertex in self.graph.all_vertices
            if vertex.key not in 'ABCDEFGH'
        ))
        self.play(anim2)
        self.play(self.graph.draw_edges())
