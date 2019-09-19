import heapq
from collections import defaultdict

from big_ol_pile_of_manim_imports import *
from manim_pathing.bases.graph import VisualGraph
from manim_pathing.helpers import *

class DijkstraGraph(VisualGraph):

    ANIMATE_HIGHLIGHT_EXPANDING = True
    ANIMATE_ANNOTATE_DISTANCE = True
    ANIMATE_DISCOVERY = True
    ANIMATE_ALL_EDGE_PROPOGATION = True
    ANIMATE_PROPOGATE_EDGES_AT_ONCE = True
    ANIMATE_EXPAND_AT_ONCE = False
    ANIMATE_EXPANDED_AREA = True
    ANIMATE_CHANGE_DISTANCE_NOT_EXPANDED = True

    DEFAULT_DISTANCE_STRING = '$\\infty$'

    def after_init(self):
        if self.ANIMATE_ANNOTATE_DISTANCE:
            for vertex in self.all_vertices:
                vertex.change_text(self.DEFAULT_DISTANCE_STRING, self.scene)
                self.scene.remove(vertex.text)
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

        for vertex in self.all_vertices:
            vertex.expanded = False
            vertex.distance = float('inf')

        self.predecessors = defaultdict(lambda: None)
        self.start.distance = 0
        self.expanding: List[Vertex] = [self.start]
        heapq.heapify(self.expanding)

        if self.ANIMATE_ANNOTATE_DISTANCE and self.ANIMATE_CHANGE_DISTANCE_NOT_EXPANDED:
            self.scene.play(self.start.change_text('$0$', self.scene, anim=True, fade_dir=DOWN))

    def search(self, anim=True):
        while not self.end.expanded:
            self.iteration += 1
            self.search_step(anim=anim)
        if anim:
            self.scene.play(ApplyMethod(self.end.set_fill, self.END_COLOR))

    def search_step(self, anim=True):
        pop_vertex = None
        while True:
            pop_vertex = heapq.heappop(self.expanding)
            if not pop_vertex.expanded:
                break
        success_verts = []
        for neighbour, weight in self.neighbours(pop_vertex, with_weights=True):
            if not neighbour.expanded:
                if neighbour.distance > pop_vertex.distance + weight:
                    neighbour.distance = pop_vertex.distance + weight
                    success_verts.append(neighbour)
                    self.predecessors[neighbour] = pop_vertex
                    heapq.heappush(self.expanding, neighbour)
        if self.ANIMATE_DISCOVERY and anim:
            success_anims = self.propogate_color_change(
                pop_vertex, success_verts, self.EDGE_DISCOVERY, at_once=self.ANIMATE_PROPOGATE_EDGES_AT_ONCE,
                end_color=self.DISCOVER_COLOR, on_hit_color=self.EDGE_SUCCESS_FLASH, after_hit_color=self.EDGE_SUCCESS,
                push_to_iterable=False,
            )
            combined_anims = {}
            for key in success_anims:
                combined_anims[key] = success_anims[key]
            if self.ANIMATE_ALL_EDGE_PROPOGATION:
                fail_anims = self.propogate_color_change(
                    pop_vertex, list(filter(lambda x: x not in success_verts, self.neighbours(pop_vertex))), self.EDGE_DISCOVERY, at_once=self.ANIMATE_PROPOGATE_EDGES_AT_ONCE,
                    on_hit_color=self.EDGE_FAIL_FLASH, after_hit_color=self.EDGE_FAIL,
                    push_to_iterable=False,
                )
                for key in fail_anims:
                    combined_anims[key] = combined_anims.get(key, []) + fail_anims[key]
            combined_anims[pop_vertex] = []
            pop_vertex.set_fill(self.EXPAND_COLOR)
            combined_anims[pop_vertex].append(pop_vertex.get_update_ring())
            if self.ANIMATE_ANNOTATE_DISTANCE and self.ANIMATE_CHANGE_DISTANCE_NOT_EXPANDED:
                for end in success_verts:
                    text_change = after_animation_separate(end.change_text(f'${end.distance}$', self.scene, anim=True, fade_dir=DOWN), combined_anims[end][0])
                    combined_anims[end].append(text_change)
            if self.ANIMATE_ANNOTATE_DISTANCE and not self.ANIMATE_CHANGE_DISTANCE_NOT_EXPANDED:
                text_change = pop_vertex.change_text(f'${pop_vertex.distance}$', self.scene, anim=True, fade_dir=DOWN)
                combined_anims[pop_vertex].append(text_change)
            if self.ANIMATE_HIGHLIGHT_EXPANDING:
                # This isn't expected to be used with EXPAND_AT_ONCE, so we can ignore timings.
                combined_anims[pop_vertex].append(ApplyMethod(self.highlight.next_to, pop_vertex, UP, rate_func=rush_from))
            iterable_anims = [
                animation
                for anim_set in combined_anims.values()
                for animation in anim_set
            ]
            self.scene.play(*iterable_anims, lag_ratio=0)
            for end in success_verts:
                end.set_fill(self.DISCOVER_COLOR)
            self.clean_edges()
        pop_vertex.expanded = True

    def vert_path(self):
        verts = [self.end]
        current = self.end
        while current != self.start:
            current = self.predecessors[current]
            verts.insert(0, current)
        return verts

class TestScene(Scene):

    def construct(self):
        c = DijkstraGraph('small.graph', self)
        c.after_init()
        c.draw_vertices()
        self.play(c.draw_edges())
        self.play(c.draw_edge_weights())

        c.search_init('F', 'C')
        c.search()
        self.play(*c.draw_path_propogation(
            c.vert_path(), YELLOW,
            after_hit=GREEN, vertex_color=PURPLE, push_to_iterable=True
        ))
