import itertools
import os
from collections import defaultdict
from typing import Dict, DefaultDict, Optional, Union, Tuple, List, Iterable
from big_ol_pile_of_manim_imports import *
import manim_pathing.bases.grid as grid
from manim_pathing.helpers import *

class VisualGrid:

    EMPTY_TYPE, WALL_TYPE, START_TYPE, END_TYPE = (
        '.','wT@','s','e',
    )

    TILES = 'tiles'
    OCTAL = 'octal'
    OCTAL_NO_CORNERS = 'octal_no_corners'

    TRAVERSAL_METHOD = OCTAL_NO_CORNERS

    DIAG_DIST = round(np.sqrt(2), 4)

    def __init__(self, filename, scene, **kwargs):
        self.scene: Scene = scene
        lines = list(open(os.path.join('manim_pathing/maps/', filename), 'r').readlines())
        for index in range(len(lines)):
            if lines[index].startswith('map'):
                lines = lines[index+1:]
                break

        lines = [line.strip('\n') for line in lines]
        for index in range(len(lines)-1, -1, -1):
            if lines[index]:
                break
            del lines[index]

        map_vals = lines
        height_dim = len(map_vals)
        width_dim = len(map_vals[0])
        length_height = kwargs.get('height', 5) / height_dim
        length_width = kwargs.get('width', 9) / width_dim
        self.side_length = min(length_height, length_width)

        self.squares = [
            [
                grid.Vertex((x, y), side_length=self.side_length)
                for y in range(width_dim)
            ]
            for x in range(height_dim)
        ]
        self.edges = defaultdict(lambda: defaultdict(lambda: None))

        for x in range(height_dim):
            for y in range(width_dim):
                self[x, y].set_gridtype(map_vals[x][y])

        for square in self.all_squares:
            for (square2, dist) in self.gen_neigbours(square, with_weights=True):
                if square.key < square2.key:
                    self[square, square2] = grid.Edge(square, square2, dist)

    # Properties and method overrides
    @property
    def all_squares(self) -> Iterable[grid.Vertex]:
        return itertools.chain(*self.squares)

    @property
    def all_edges(self) -> Iterable[grid.Edge]:
        return (
            self[x, y]
            for x in self.all_squares
            for y in self.all_squares
            if self[x, y] is not None
            if x.key > y.key
        )

    def __getitem__(self, key) -> Union[grid.Vertex, Optional[grid.Edge]]:
        if isinstance(key, list) or isinstance(key, tuple):
            if isinstance(key[0], int):
                return self.squares[key[0]][key[1]]
            if isinstance(key[0], grid.Vertex):
                v1 = key[0]
                v2 = key[1]
                if v1.key < v2.key:
                    return self.edges[v1][v2]
                return self.edges[v2][v1]
            if isinstance(key[0], str):
                return self[self[key[0]], self[key[1]]]
        if isinstance(key, grid.Vertex):
            return key
        if isinstance(key, str):
            return self[list(map(int, key[1:-1].split(',')))]

    def __setitem__(self, key, value):
        if isinstance(key, list) or isinstance(key, tuple):
            if isinstance(key[0], int):
                self.squares[key[0]][key[1]] = value
            if isinstance(key[0], str):
                self.edges[self[key[0]]][self[key[1]]] = value
            if isinstance(key[0], grid.Vertex):
                v1 = key[0]
                v2 = key[1]
                if v1.key < v2.key:
                    self.edges[v1][v2] = value
                else:
                    self.edges[v2][v1] = value
        if isinstance(key, str):
            x, y = list(map(int, key[1:-1].split(',')))
            self.squares[x][y] = value

    # Generic Animation
    def draw_vertices(self, anim_class=FadeInFromDown, **kwargs) -> Iterable[Animation]:
        return (
            anim_class(grid.vertex, **kwargs)
            for grid.vertex in self.all_squares
        )

    def destroy(self, anim_class=Uncreate, **kwargs) -> Animation:
        anim1 = [anim_class(e.line_obj) for e in self.all_edges if e.line_obj]
        anim2 = [anim_class(v) for v in self.all_squares]
        return AnimationGroup(*anim1, *anim2)

    def search_init(self, start, end):
        self.iteration = 0
        self.start = self[start]
        self.end = self[end]

        self.scene.play(
            self.start.set_gridtype(self.START_TYPE, anim=True),
            self.end.set_gridtype(self.END_TYPE, anim=True),
        )

    # Computation Helpers
    def dist(self, sq1: grid.Vertex, sq2: grid.Vertex):
        diag = min(np.abs(sq1.x - sq2.x), np.abs(sq1.y - sq2.y))
        horizontal = max(np.abs(sq1.x - sq2.x), np.abs(sq1.y - sq2.y)) - diag
        return horizontal + diag * self.DIAG_DIST

    def gen_neigbours(self, key, with_weights=False, exclude_nontraversable=True):
        square: grid.Vertex = self[key]
        points = [
            (square.x + 1, square.y),
            (square.x - 1, square.y),
            (square.x, square.y + 1),
            (square.x, square.y - 1),
        ]
        points = list(filter(lambda key: (
            0 <= key[0] < len(self.squares) and
            0 <= key[1] < len(self.squares[0])
        ), points))
        for x_change in (-1, 1):
            for y_change in (-1, 1):
                if (
                    0 <= square.x + x_change < len(self.squares) and
                    0 <= square.y + y_change < len(self.squares[0])
                ):
                    if (
                        self.TRAVERSAL_METHOD == self.OCTAL or
                        (
                            self.TRAVERSAL_METHOD == self.OCTAL_NO_CORNERS and
                            self[square.x + x_change, square.y].traversable and
                            self[square.x, square.y + y_change].traversable
                        )
                    ) or not exclude_nontraversable:
                        points.append((square.x + x_change, square.y + y_change))
        return [
            (
                self[x, y],
                self.dist(square, self[x, y])
            ) if with_weights else self[x, y]
            for x, y in points
            if (self[x, y].traversable or not exclude_nontraversable)
        ]

    # Pathfinding/General Propogation Animations
    def propogate_color_change(
        self, start, ends, edge_color,
        at_once=True, on_hit_color=None, after_hit_color=None,
        end_type=None, push_to_iterable=False, **edge_kwargs,
    ):
        if not ends:
            return [] if push_to_iterable else {}
        edges: List[Edge] = [self[start, end] for end in ends]
        assert None not in edges, "Disconnect grid.vertex in ends."

        # Map vertices to animations
        extension_dict = {}
        store_old_color = {}
        store_on_hit_color = {}
        store_after_hit_color = {}
        for end, edge in zip(ends, edges):
            edge.clean(self.scene)
            store_old_color[edge] = edge.line_obj.get_color() if edge.line_obj else 'draw'
            if not on_hit_color:
                store_on_hit_color[edge] = edge_color
            else:
                store_on_hit_color[edge] = (
                    store_old_color[edge]
                    if on_hit_color=='previous'
                    else on_hit_color
                )
            store_after_hit_color[edge] = (
                store_old_color[edge]
                if after_hit_color=='previous'
                else after_hit_color
            )
            # Original line color change
            extension_dict[end] = [edge.change_color(
                edge_color,
                from_v=start,
                anim=True,
                run_time=self.PROPOGATION_SPEED * (
                    1 if at_once else edge.length / self.max_length
                ),
                **edge_kwargs,
            ) if store_old_color[edge] != 'draw' else edge.draw(
                direction=('f' if edge.v1 == start else 'b'),color=edge_color,
            )]
            # After edge propogation hits end
            next_step = []
            if end_type:
                next_step.append(after_animation_separate(
                    end.set_gridtype(end_type, anim=True),
                    *extension_dict[end],
                ))
            anim_cls, args, kwargs = edge.change_color(
                store_after_hit_color[edge] or edge_color,
                from_color=store_on_hit_color[edge],
                anim=True,
                class_mode=True,
            )
            kwargs.update({'rate_func': rush_into})
            next_step.append(after_animation_from_succession(
                anim_cls, args, kwargs, *extension_dict[end],
            ))

            extension_dict[end].extend(next_step)

        if push_to_iterable:
            anims = [
                anim
                for anim_set in extension_dict.values()
                for anim in anim_set
            ]
            return anims
        return extension_dict

    # Misc animation helpers
    def update_foreground(self):
        self.scene.add_foreground_mobjects(*(
            e.line_obj
            for e in self.all_edges
            if e.line_obj
        ))

    def clean_edges(self):
        for edge in self.all_edges:
            edge.clean(self.scene)

class TestScene(Scene):

    def construct(self):
        a = VisualGrid('easy.map', self)
        self.play(*a.draw_vertices())
        a.search_init((1, 7), (3, 5))
        self.play(*a.propogate_color_change(
            a[1, 4], a.gen_neigbours((1, 4)), YELLOW,
            on_hit_color=GREEN,
            after_hit_color=PURPLE,
            at_once=False, push_to_iterable=True,
        ))

        a.clean_edges()
        a.update_foreground()

        self.play(a.destroy())
