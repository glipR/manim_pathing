from big_ol_pile_of_manim_imports import *
from manim_pathing.helpers import *
from typing import Optional

class Vertex(Circle):

    VERTEX_CONFIG = {
        'fill_color': '#306998',
        'color': '#FFE873',
        'stroke_width': 3,
        'radius': 0.5,
        'opacity': 1,
        'fill_opacity': 1,
    }

    TEXT_CONFIG = {
        'color': WHITE,
    }

    def __init__(self, key, pos, show_key=True, **kwargs):
        self.key = key
        self.pos = pos
        new_kwargs = self.VERTEX_CONFIG
        new_kwargs.update(kwargs)
        super().__init__(**new_kwargs)
        self.text = None
        self.move_to(pos)
        if show_key:
            self.text = TextMobject(key, **self.TEXT_CONFIG)
            self.text.move_to(pos)

    def __str__(self):
        return f"Vertex({self.key})"

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    def change_text(self, text, scene: Scene, anim=False, fade_dir=None, **kwargs):
        old_text = self.text
        new_text = TextMobject(text, **self.TEXT_CONFIG)
        new_text.move_to(self)
        if not anim:
            scene.remove_foreground_mobject(self.text)
            scene.add_foreground_mobject(new_text)
            self.text = new_text
        if fade_dir is not None:
            anim = AnimationGroup(
                FadeInFrom(new_text, fade_dir * -1),
                FadeOutAndShiftDown(self.text, fade_dir),
            )
            scene.add_foreground_mobject(new_text)
            self.text = new_text
        else:
            anim = Transform(self.text, new_text)
        return anim

    def get_update_ring(self, color=None, **kwargs) -> Animation:
        copy = self.copy()
        if color is not None:
            copy.set_fill(color)
        copy.set_stroke(opacity=0)
        defaults = {
            'scale_factor': 1.7,
            'rate_func': rush_from,
        }
        defaults.update(kwargs)
        return FadeOutToLarge(copy, **defaults)

    def draw_border(self) -> Animation:
        self.set_fill(opacity=0)
        return ShowCreation(self)

    def fill_in_with_text(self):
        anim = ApplyMethod(self.set_fill, {'opacity': 1})

        if self.text is not None:
            # self.text.add_updater(lambda t: t.move_to(self))
            anim = AnimationGroup(anim, ShowCreation(self.text))

        return anim
