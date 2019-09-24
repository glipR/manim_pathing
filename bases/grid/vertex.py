from big_ol_pile_of_manim_imports import *
import manim_pathing.bases.grid as grid

class Vertex(Square):

    VERTEX_CONFIG = {
        'length': 0.5,
        'fill_opacity': 1,
        'stroke_width': 0,
    }

    SIDE_MARGIN = 0.05

    def __init__(self, pos, **kwargs):
        new_kwargs = self.VERTEX_CONFIG
        new_kwargs.update(kwargs)
        length = new_kwargs['length']
        new_kwargs['side_length'] = length - length * self.SIDE_MARGIN * 2
        super().__init__(**new_kwargs)
        self.shift((RIGHT + DOWN) * length * self.SIDE_MARGIN)
        self.pos = pos
        self.move_to(
            DOWN * self.x * length +
            RIGHT * self.y * length
        )
        self.gridtype = None

    def __str__(self):
        return self.key

    @property
    def key(self):
        return f'({self.x}, {self.y})'

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    def get_update_ring(self, color=None, **kwargs):
        copy = self.copy()
        if color is not None:
            copy.set_fill(color)
        defaults = {
            'scale_factor': 1.7,
            'rate_func': rush_from,
        }
        defaults.update(kwargs)
        return FadeOutToLarge(copy, **defaults)

    def set_gridtype(self, gridtype, anim=False):
        if self.gridtype == gridtype:
            return
        if gridtype in grid.VisualGrid.EMPTY_TYPE:
            self.traversable = True
            self.color = WHITE
        elif gridtype in grid.VisualGrid.WALL_TYPE:
            self.traversable = False
            self.color = BLACK
        elif gridtype in grid.VisualGrid.START_TYPE:
            self.traversable = True
            self.color = GREEN
        elif gridtype in grid.VisualGrid.END_TYPE:
            self.traversable = True
            self.color = RED

        self.gridtype = gridtype

        if anim:
            return AnimationGroup(
                ApplyMethod(self.set_fill, self.color),
                self.get_update_ring(self.color),
            )
        self.set_fill(self.color)
