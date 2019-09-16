from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph.edge import Edge
from manim_pathing.bases.graph.vertex import Vertex
from manim_pathing.helpers import *

class TestScene(Scene):

    def construct(self):
        v1 = Vertex('A', (-2, 0, 0), True)
        v2 = Vertex('B', (2, 0, 0), False)
        v3 = Vertex('C', (0, -2, 0), fill_color=RED)

        e1 = Edge(v1, v2, weight=4)
        e2 = Edge(v2, v3, weight=INF)
        e3 = Edge(v3, v1)

        self.play(
            v1.draw_border(),
            v2.draw_border(),
            v3.draw_border(),
        )

        self.play(
            v1.fill_in_with_text(),
            v2.fill_in_with_text(),
            v3.fill_in_with_text(),
        )

        self.play(
            e1.draw(),
            e2.draw(),
            e3.draw(),
        )

        self.play(
            e1.draw_weight(),
            e2.draw_weight(),
            e3.draw_weight(),
        )

        v1.set_fill(RED)
        self.play(
            v1.get_update_ring(RED),
            e1.change_color(PURPLE, from_v=v1, anim=True),
        )

        v2.set_fill(RED)
        e1.clean(self)
        self.play(
            v2.get_update_ring(RED),
            e2.change_color(PURPLE, from_v=v2, anim=True),
        )
