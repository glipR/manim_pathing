import os
import re
from collections import defaultdict
from typing import Dict, DefaultDict, Optional, Union, Tuple

from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph.edge import Edge
from manim_pathing.bases.graph.vertex import Vertex
from manim_pathing.helpers import *

class VisualGraph:

    VERTEX_DEFAULTS = {}

    vertex_matcher = re.compile(r'(?P<key>\S+), \((?P<x>\S+), (?P<y>\S+)\)')
    edge_matcher = re.compile(r'(?P<key1>\S+) (?P<direction>(>|<|-))(?P<weight>((\S+)|-|>|<))(>|<|-) (?P<key2>\S+)')

    PROPOGATION_SPEED = 1

    def __init__(self, filename, scene: Scene, **kwargs):
        defaults = self.VERTEX_DEFAULTS
        defaults.update(kwargs)
        vertex_info = []
        edge_info = []
        for line in open(os.path.join('manim_pathing/maps/', filename), 'r').readlines():
            vmatch = self.vertex_matcher.match(line.strip())
            ematch = self.edge_matcher.match(line.strip())
            if vmatch is not None:
                info = vmatch.groupdict()
                vertex_info.append((info['key'], (float(info['x']), float(info['y']), 0)))
            if ematch is not None:
                info = ematch.groupdict()
                kwargs = {}
                if info['direction'] in '><':
                    kwargs['directed'] = True
                if info['weight'].isnumeric():
                    kwargs['weight'] = float(info['weight'])
                    if int(kwargs['weight']) == kwargs['weight']:
                        kwargs['weight'] = int(kwargs['weight'])
                if info['direction'] == '<':
                    args = [info['key2'], info['key1']]
                else:
                    args = [info['key1'], info['key2']]
                edge_info.append((args, kwargs))
        self.vertices: Dict[str, Vertex] = {}
        self.edges: DefaultDict[Vertex, DefaultDict[Vertex, Optional[Edge]]] = defaultdict(lambda: defaultdict(lambda: None))

        for vertex in vertex_info:
            vobj = Vertex(*vertex, scene, **defaults)
            self.vertices[vobj.key] = vobj
        for args, kwargs in edge_info:
            args[0] = self[args[0]]
            args[1] = self[args[1]]
            edge = Edge(*args, **kwargs)
            self[args[0:2]] = edge
            if not kwargs.get('directed', False):
                self[args[1::-1]] = edge

        self.max_length = max(edge.length for edge in self.all_edges)
        self.scene: Scene = scene

    # Properties and method overrides
    @property
    def all_vertices(self):
        return self.vertices.values()

    @property
    def all_edges(self):
        for v1 in self.all_vertices:
            for v2 in self.all_vertices:
                if v1.key < v2.key:
                    if self[v1, v2]:
                        yield self[v1, v2]

    def __getitem__(self, key) -> Union[Vertex, Optional[Edge]]:
        """Get vertex/edge by key/vertex"""
        if isinstance(key, list) or isinstance(key, tuple):
            return self.edges[self[key[0]]][self[key[1]]]
        if isinstance(key, Vertex):
            return key
        return self.vertices[key]

    def __setitem__(self, key, value):
        """Set vertex/edge by key/vertex"""
        if isinstance(key, list) or isinstance(key, tuple):
            self.edges[self[key[0]]][self[key[1]]] = value
        else:
            self.vertices[key] = value

    # Generic Animation
    def draw_vertices(self, play=True, **kwargs) -> Tuple[Animation]:
        anim1 = AnimationGroup(*(v.draw_border() for v in self.all_vertices))
        anim2 = AnimationGroup(*(v.fill_in_with_text() for v in self.all_vertices))

        if play:
            self.scene.play(anim1, **kwargs)
            self.update_foreground()
            self.scene.play(anim2, **kwargs)
        return anim1, anim2

    def draw_edges(self, **kwargs) -> Animation:
        return AnimationGroup(*(e.draw(**kwargs) for e in self.all_edges))

    def draw_edge_weights(self, **kwargs) -> Animation:
        return AnimationGroup(*(e.draw_weight(**kwargs) for e in self.all_edges))

    def destroy(self, anim_class=Uncreate, **kwargs) -> Animation:
        anim1 = [anim_class(e.line_object, **kwargs) for e in self.all_edges]
        anim2 = [anim_class(v, **kwargs) for v in self.all_vertices]
        anim3 = [anim_class(v.text, **kwargs) for v in self.all_vertices]
        anims = AnimationGroup(*anim1, *anim2, *anim3)

        return anims

    # Computation helpers
    def neighbours(self, vertex: Union[Vertex, str], with_weights=False):
        vertex = self[vertex] # If key, make vert
        if not with_weights:
            return [
                end
                for end in self.all_vertices
                if self[vertex, end] is not None
            ]
        return [
            (end, self[vertex, end].weight)
            for end in self.all_vertices
            if self[vertex, end] is not None
        ]

    # Pathfinding/General Propogation Animations - Fun part
    def propogate_color_change(
        self, start, ends, edge_color,
        at_once=True, on_hit_color=None, after_hit_color=None, end_color=None,
        end_texts=None, push_to_iterable=False, **edge_kwargs
    ):
        if not ends:
            return [] if push_to_iterable else {}
        edges = [self[start, end] for end in ends]
        assert None not in edges, "Disconnected vertex in ends."

        # Map vertices to animations
        extension_dict = {}
        store_old_color = {}
        store_on_hit_color = {}
        store_after_hit_color = {}
        for end, edge in zip(ends, edges):
            edge.clean(self.scene)
            store_old_color[edge] = edge.line_obj.get_color()
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
                if after_hit_color == 'previous'
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
            )]
            # next step occurs when the edge propogation hits end.
            next_step = []
            next_step.append(after_animation_separate(
                end.get_update_ring(color=end_color),
                *extension_dict[end],
            ))
            if end_color:
                # Change end vertex color
                next_step.append(after_animation_separate(
                    ApplyMethod(end.set_fill, end_color),
                    *extension_dict[end],
                ))
            if end_texts:
                next_step.append(after_animation_separate(
                    end.change_text(end_texts[end], anim=True, fade_dir=DOWN),
                    *extension_dict[end],
                ))
            # Edge on hit animations - This isn't the first time, so use successive animations.
            anim_cls, args, kwargs, = edge.change_color(
                store_after_hit_color[edge] or edge_color,
                from_color=store_on_hit_color[edge],
                anim=True,
                class_mode=True,
            )
            kwargs.update({'rate_func': rush_into})
            next_step.append(after_animation_from_succession(
                anim_cls,
                args,
                kwargs,
                *extension_dict[end],
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

    def propogate_from_predecessor_map(
        self, start, predecessor_map, edge_color,
        on_hit_success=None, on_hit_fail=None, after_hit_success=None, after_hit_fail=None, vertex_color=None,
        at_once=True, include_failing_edges=False, vertex_texts=None, push_to_iterable=False,
    ):
        """Propogate throughout the all predecessors using propogate_color_change."""

        # reverse the mapping
        children = defaultdict(lambda: [])
        for child, parent in predecessor_map.items():
            children[parent].append(child)

        # BFS search
        animations = {}
        vertices = [start, ]
        while vertices:
            for vertex in vertices:
                success_anims = self.propogate_color_change(
                    vertex,
                    children[vertex],
                    edge_color,
                    at_once=at_once,
                    on_hit_color=on_hit_success,
                    after_hit_color=after_hit_success,
                    end_color=vertex_color,
                    end_texts=vertex_texts,
                    rate_func=linear,
                )
                for key in success_anims:
                    base_anims = animations.get(key, [])
                    timing_anims = animations.get(predecessor_map[key], [])
                    animations[key] = (
                        base_anims + [
                            after_animation_separate(anim, timing_anims[0]) if timing_anims else anim
                            for anim in new_animations[key]
                        ]
                    )
                if include_failing_edges:
                    failure_anims = self.propogate_color_change(
                        vertex,
                        [
                            neighbour
                            for neighbour in self.neighbours(vertex)
                            if neighbour not in children[vertex]
                        ],
                        edge_color,
                        at_once=at_once,
                        on_hit_color=on_hit_fail,
                        after_hit_color=after_hit_fail,
                        rate_func=linear,
                    )
                    for key in failure_anims:
                        base_anims = animations.get(key, [])
                        timing_anims = animations.get(predecessor_map[key], [])
                        animations[key] = (
                            base_anims + [
                                after_animation_separate(anim, timing_anims[0]) if timing_anims else anim
                                for anim in failure_anims[key]
                            ]
                        )
            vertices = [
                child
                for vertex in vertices
                for child in children[vertex]
            ]

        if push_to_iterable:
            anims = [
                anim
                for anim_set in animations.values()
                for anim in anim_set
            ]
            return anims
        return animations

    # Misc animation helpers
    def update_foreground(self):
        self.scene.add_foreground_mobjects(
            *(v for v in self.all_vertices),
            *(v.text for v in self.all_vertices),
        )

    def clean_edges(self):
        for edge in self.all_edges:
            edge.clean(self.scene)


class TestScene(Scene):

    def construct(self):
        c = VisualGraph('small.graph', self)
        c.draw_vertices()
        self.play(c.draw_edges())
        self.play(c.draw_edge_weights())

        c['F'].set_fill(RED)
        self.play(c['F'].get_update_ring())
        self.play(*c.propogate_color_change(
            c['F'], c.neighbours('F'), YELLOW,
            on_hit_color=GREEN,
            after_hit_color=PURPLE,
            at_once=False, push_to_iterable=True,
        ))

        c.clean_edges()

        c['C'].set_fill(GREEN)
        self.play(c['C'].get_update_ring())
        self.play(*c.propogate_color_change(
            c['C'], c.neighbours('C'), YELLOW,
            on_hit_color=GREEN,
            after_hit_color=PURPLE,
            at_once=True, push_to_iterable=True,
        ))

        self.wait(0.2)
