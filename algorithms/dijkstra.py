import heapq
import numpy as np
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
    ANIMATE_HIGHLIGHT_EXPANDED = True

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
            combined_anims[pop_vertex] = combined_anims.get(pop_vertex, [])
            if self.ANIMATE_HIGHLIGHT_EXPANDED:
                if pop_vertex == self.start:
                    self.enclosing = Polygon(
                        pop_vertex.get_center() + UP * 0.3,
                        pop_vertex.get_center() + RIGHT * 0.3,
                        pop_vertex.get_center() + DOWN * 0.3,
                        pop_vertex.get_center() + LEFT * 0.3,
                    )
                    self.enclosing.round_corners()
                    self.enclosing.set_stroke(color=BLUE, width=4 * DEFAULT_STROKE_WIDTH)
                    self.enclosing.scale_about_point(1.8, self.enclosing.get_center())
                    self.tn_text = TextMobject("$T_n$", color=BLUE)
                    self.tn_text.next_to(self.start, LEFT)
                    combined_anims[pop_vertex].extend([
                        ShowCreation(self.enclosing),
                        ShowCreation(self.tn_text),
                    ])
                else:
                    points = np.array(list(map(lambda x: x.get_center(), [pop_vertex] + list(filter(lambda x: x.expanded, self.all_vertices)))))
                    new_enclosing = self.generate_enclosing_polygon(points)
                    new_enclosing.round_corners()
                    new_enclosing.set_stroke(color=BLUE, width=4 * DEFAULT_STROKE_WIDTH)
                    combined_anims[pop_vertex].append(Transform(self.enclosing, new_enclosing))

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

    def generate_enclosing_polygon(self, points, BUFF_DIST=1):
        if len(points) == 1:
            # return a circle around the point.
            enclosing = Circle()
            enclosing.move_to(Point(*points))
            return enclosing
        if len(points) == 2:
            diff = unit_vec([points[1][x] - points[0][x] for x in range(3)])
            # rotate left 90
            diff_r90 = np.array([
                -diff[1],
                diff[0],
                0
            ])
            new_enclosing = Polygon(
                diff_r90 + points[0],
                -diff_r90 + points[0],
                -diff_r90 + points[1],
                diff_r90 + points[1],
            )
            return new_enclosing
        # Start from the leftmost point. Then move to the next point with the least change in slope
        # (Clockwise)
        # This sucks on complexity but who cares.
        left = (points[0], 0)
        right = (points[0], 0)
        down = (points[0], 0)
        up = (points[0], 0)
        for index, point in enumerate(points[1:], start=1):
            if point[0] < left[0][0]:
                left = (point, index)
            if point[0] > right[0][0]:
                right = (point, index)
            if point[1] > up[0][1]:
                up = (point, index)
            if point[1] < down[0][1]:
                down = (point, index)
        start_point = left[0]
        current_point = start_point
        new_points = []
        first = True
        l, u, r, d = range(4)
        current_mode = l
        current_slope = INF
        while first or (current_point != start_point).any():
            first = False
            if current_mode == l and (current_point == up[0]).all():
                current_mode = u
                # New slope we are trying to best is flat.
                current_slope = 0
            if current_mode == u and (current_point == right[0]).all():
                current_mode = r
                # New slope we are trying to best is down.
                current_slope = INF
            if current_mode == r and (current_point == down[0]).all():
                current_mode = d
                # New slope we are trying to best is down.
                current_slope = 0
            new_point = None
            new_slope = None
            current_diff = float('inf')
            considering = []
            for point in points:
                if not np.any([(point1 == point).all() for point1 in new_points]):
                    if current_mode == l:
                        # Only select points in quadrant 1.
                        if point[0] > current_point[0] and point[1] > current_point[1]:
                            considering.append(point)
                    elif current_mode == u:
                        # Quadrant 4
                        if point[0] > current_point[0] and point[1] < current_point[1]:
                            considering.append(point)
                    elif current_mode == r:
                        # Quadrant 3
                        if point[0] < current_point[0] and point[1] < current_point[1]:
                            considering.append(point)
                    elif current_mode == d:
                        # Quadrant 2
                        if point[0] < current_point[0] and point[1] > current_point[1]:
                            considering.append(point)
            for point in considering:
                slope = (point[1] - current_point[1]) / (point[0] - current_point[0])
                diff = np.abs(current_slope - slope)
                if diff < current_diff:
                    current_diff = diff
                    new_point = point
                    new_slope = slope
            current_point = new_point
            current_slope = new_slope
            new_points.append(current_point)

        # Solve buffer problem.
        poly_points = []
        wrapped_points = [new_points[-1]] + new_points + [new_points[0]]
        for point1, point2, point3 in zip(wrapped_points[:-2], wrapped_points[1:-1], wrapped_points[2:]):
            vec1 = unit_vec(point2 - point1)
            vec2 = unit_vec(point2 - point3)
            combined = unit_vec(vec1 + vec2)
            poly_points.append(point2 + combined * BUFF_DIST)

        enclosing = Polygon(*poly_points)
        return enclosing

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
