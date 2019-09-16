from collections import defaultdict
from typing import List

from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph import VisualGraph, Vertex
from manim_pathing.helpers import *

class BFSGraph(VisualGraph):

    ANIMATE_HIGHLIGHT_EXPANDING = True
    ANIMATE_ANNOTATE_DISTANCE = True
    ANIMATE_DISCOVERY = True
    ANIMATE_ALL_EDGE_PROPOGATION = True
    ANIMATE_PROPOGATE_EDGES_AT_ONCE = True
    ANIMATE_EXPAND_WHILE_PROPOGATING = True
    ANIMATE_EXPAND_AT_ONCE = False

    def after_init(self):
        if self.ANIMATE_ANNOTATE_DISTANCE:
            for vertex in self.all_vertices:
                vertex.change_text('', self.scene)
            self.update_foreground()
        if self.ANIMATE_HIGHLIGHT_EXPANDING:
            self.highlight = Polygon(
                (-0.2, 0.2, 0),
                (0, 0, 0),
                (0.2, 0.2, 0),
                (0, 0, 0),
                color=WHITE,
            )

    def search_init(self, start, end):
        super().search_init(start, end)

        if self.ANIMATE_HIGHLIGHT_EXPANDING:
            self.highlight.next_to(self.start, UP)
            self.scene.add_foreground_mobjects(self.highlight)
            self.scene.play(ShowCreation(self.highlight))

        self.predecessors = defaultdict(lambda: None)
        self.distances = defaultdict(lambda: None)
        self.distances[self.start] = 0
        self.expanding: List[Vertex] = [self.start]

        if self.ANIMATE_ANNOTATE_DISTANCE:
            self.scene.play(self.start.change_text('$0$', self.scene, anim=True, fade_dir=DOWN))

    def search(self, anim=True):
        while self.predecessors[self.end] is None:
            self.iteration += 1
            self.search_step(anim=anim)
            if self.predecessors[self.end] is None and anim:
                # Slightly tint the next set of vertices.
                self.scene.play(*(
                    ApplyMethod(vert.set_fill, self.CURRENT_VERTS)
                    for vert in self.expanding
                ))
        if anim:
            self.scene.play(ApplyMethod(self.end.set_fill, self.END_COLOR))

    def search_step(self, anim=True):
        new_expanding = []
        all_anims = []
        for vertex in self.expanding:
            success_function = (
                lambda vert:
                self.predecessors[vert] is None and vert != self.start  # Vertex hasn't been looked at
            )
            end_vertices = list(filter(success_function, self.neighbours(vertex)))
            if self.ANIMATE_DISCOVERY and anim:
                success_anims = self.propogate_color_change(
                    vertex, end_vertices, self.EDGE_DISCOVERY, at_once=self.ANIMATE_PROPOGATE_EDGES_AT_ONCE,
                    end_color=self.DISCOVER_COLOR, on_hit_color=self.EDGE_SUCCESS_FLASH, after_hit_color=self.EDGE_SUCCESS,
                    push_to_iterable=False,
                )
                combined_anims = {}
                for key in success_anims:
                    combined_anims[key] = success_anims[key]
                if self.ANIMATE_ALL_EDGE_PROPOGATION:
                    fail_anims = self.propogate_color_change(
                        vertex, list(filter(lambda x: not success_function(x), self.neighbours(vertex))), self.EDGE_DISCOVERY, at_once=self.ANIMATE_PROPOGATE_EDGES_AT_ONCE,
                        on_hit_color=self.EDGE_FAIL_FLASH, after_hit_color=self.EDGE_FAIL,
                        push_to_iterable=False,
                    )
                    for key in fail_anims:
                        combined_anims[key] = combined_anims.get(key, []) + fail_anims[key]
                combined_anims[vertex] = []
                if self.ANIMATE_EXPAND_WHILE_PROPOGATING and vertex != self.start:
                    vertex.set_fill(self.EXPAND_COLOR)
                    combined_anims[vertex].append(vertex.get_update_ring())
                if self.ANIMATE_ANNOTATE_DISTANCE:
                    for end in end_vertices:
                        text_change = after_animation_separate(end.change_text(f'${self.iteration}$', self.scene, anim=True, fade_dir=DOWN), combined_anims[end][0])
                        combined_anims[end].append(text_change)
                    self.update_foreground()
                if self.ANIMATE_HIGHLIGHT_EXPANDING:
                    # This isn't expected to be used with EXPAND_AT_ONCE, so we can ignore timings.
                    combined_anims[vertex].append(ApplyMethod(self.highlight.next_to, vertex, UP, rate_func=rush_from))
                iterable_anims = [
                    animation
                    for anim_set in combined_anims.values()
                    for animation in anim_set
                ]
                if not self.ANIMATE_EXPAND_AT_ONCE:
                    self.scene.play(*iterable_anims, lag_ratio=0)
                    for end in end_vertices:
                        end.set_fill(self.DISCOVER_COLOR)
                else:
                    all_anims.extend(iterable_anims)

            if not self.ANIMATE_EXPAND_AT_ONCE:
                self.clean_edges()

            for end in end_vertices:
                self.predecessors[end] = vertex
                new_expanding.append(end)
                self.distances[end] = self.iteration

            if anim and vertex != self.start and not self.ANIMATE_EXPAND_WHILE_PROPOGATING:
                    self.scene.play(ApplyMethod(vertex.set_fill, self.EXPAND_COLOR))

        self.expanding = new_expanding
        if anim and self.ANIMATE_DISCOVERY and self.ANIMATE_EXPAND_AT_ONCE:
            self.scene.play(*all_anims, lag_ratio=0)

    def vert_path(self):
        verts = [self.end]
        current = self.end
        while current != self.start:
            current = self.predecessors[current]
            verts.insert(0, current)
        return verts


class TestScene(Scene):

    def construct(self):
        c = BFSGraph('small.graph', self)
        c.after_init()
        c.draw_vertices()
        self.play(c.draw_edges())

        c.search_init('F', 'C')
        c.search()
        self.play(*c.draw_path_propogation(
            c.vert_path(), YELLOW,
            after_hit=GREEN, vertex_color=PURPLE, push_to_iterable=True
        ))
