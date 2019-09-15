from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph.vertex import Vertex
from manim_pathing.helpers import *

class Edge:

    CONFIG = {
        'color': WHITE,
        'stroke_width': DEFAULT_STROKE_WIDTH * 2,
    }

    WEIGHT_CONFIG = {
        'color': WHITE,
    }

    def __init__(self, v1: Vertex, v2: Vertex, weight=None, directed=False, **kwargs):
        self.v1 = v1
        self.v2 = v2
        self.weight = 1 if weight is None else weight
        self.directed = directed
        self.line_obj = None
        self.tmp_lines = []
        self.weight_text = TextMobject('', **self.WEIGHT_CONFIG)
        self.weight_text.next_to(self.midpoint, UP)

    @property
    def length(self):
        return np.sqrt(
            pow(self.v1.x - self.v2.x, 2) +
            pow(self.v1.y - self.v2.y, 2)
        )

    @property
    def midpoint(self):
        return (
            (self.v1.x + self.v2.x) / 2,
            (self.v1.y + self.v2.y) / 2,
            0,
        )

    @property
    def normal(self):
        return unit_vec((
            (self.v2.y - self.v1.y),
            (self.v1.x - self.v2.x),
            0
        ))

    def _gen_line_with_args(self, v1: Vertex, v2: Vertex, **kwargs) -> Line:
        config = dict(**self.CONFIG)
        config.update(kwargs)
        return Line(
            Point(
                v1.get_center() +
                unit_vec(v2.get_center() - v1.get_center()) *
                v1.radius * 0.99
            ),
            Point(
                v2.get_center() +
                unit_vec(v1.get_center() - v2.get_center()) *
                v2.radius * 0.99
            ),
            **config,
        )

    def draw(self, direction='f', **kwargs) -> Animation:
        if direction == 'f':
            self.line_obj = self._gen_line_with_args(self.v1, self.v2, **kwargs)
        elif direction == 'b':
            self.line_obj = self._gen_line_with_args(self.v1, self.v2, **kwargs)
        anim = ShowCreation(self.line_obj)
        return anim

    def draw_weight(self) -> Animation:
        new_weight = TextMobject(f'${to_text(self.weight)}$')
        new_weight.next_to(self.midpoint, self.normal)
        return Transform(self.weight_text, new_weight)

    def change_color(self, color, from_v=None, from_color=None, anim=False, class_mode=False, **kwargs) -> Animation:
        if not anim:
            if self.tmp_lines:
                return self.tmp_lines[-1].set_color(color)
            return self.line_obj.set_color(color)

        if from_v is None:
            original = self.line_obj if not self.tmp_lines else self.tmp_lines[-1]
            if from_color is not None:
                self.tmp_lines.append(original.copy())
                self.tmp_lines[-1].set_color(from_color)
                original = self.tmp_lines[-1]
            self.tmp_lines.append(original.copy())
            self.tmp_lines[-1].set_color(color)
            animation = Transform(original, self.tmp_lines[-1], **kwargs)
            if class_mode:
                return SuccessiveTransform, [self.tmp_lines[-2], self.tmp_lines[-1]], kwargs
        else:
            if from_v == self.v1:
                self.tmp_lines.append(self._gen_line_with_args(self.v1, self.v2, color=color))
            elif from_v == self.v2:
                self.tmp_lines.append(self._gen_line_with_args(self.v2, self.v1, color=color))
            else:
                raise ValueError('from_v must be an adjacent vertex.')
            animation = ShowCreation(self.tmp_lines[-1], **kwargs)
            if class_mode:
                raise NotImplementedError('Fix me')

        return animation

    def clean(self, scene: Scene):
        scene.remove(self.line_obj)
        if self.tmp_lines:
            scene.remove(*self.tmp_lines)
            self.line_obj = self.tmp_lines[-1]
            self.tmp_lines = []
        scene.add(self.line_obj)
