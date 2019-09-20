from big_ol_pile_of_manim_imports import *
from manimlib.utils.color import hex_to_rgb, rgb_to_hex, color_to_rgb

INF = 100000001

def to_text(num):
    if num < INF:
        return str(num)
    return r'\infty'

def magnitude(vec):
    return np.sqrt(sum(pow(p, 2) for p in vec))

def unit_vec(vec):
    mag = magnitude(vec)
    return np.array([p/mag for p in vec])

def ratio_to_grad(c1, c2, ratio):
    col1 = hex_to_rgb(c1)
    col2 = hex_to_rgb(c2)
    mixed = [
        c1 + (c2 - c1) * ratio
        for (c1, c2) in zip(col1, col2)
    ]
    return rgb_to_hex(mixed)

# Successive animation helpers

class SuccessiveTransform(Transform):

    def interpolate_submobject(self, submob, start, target_copy, alpha):
        if alpha == 0:
            if not hasattr(submob, 'beginning_opacity'):
                submob.beginning_opacity = 1
                submob.set_opacity(0)
                submob.opacity_updated = False
                return
        else:
            if not submob.opacity_updated:
                submob.set_opacity(submob.beginning_opacity)
                submob.opacity_updated = True
            super().interpolate_submobject(submob, start, target_copy, alpha)

def change_rate_func(b_time, m_time, e_time, b_func, m_func, e_func):
    """
    Makes the animation do nothing for the first `ratio * run_time` seconds.
    """
    def new_rate_func(t):
        time_taken = t * (b_time + m_time + e_time)
        if time_taken < b_time:
            return b_func(time_taken / safe_division(b_time))
        if time_taken < b_time + m_time:
            return m_func((time_taken - b_time) / safe_division(m_time))
        return e_func((time_taken - b_time - m_time) / safe_division(e_time))
    return new_rate_func

def safe_division(num):
    return 1 / INF if num == 0 else num

def stay_end(t):
    return 1

def stay_start(t):
    return 0

# There is probably a better way to do these two.
def after_animation_separate(animation, *previous_anims):
    rate_func = change_rate_func(
        max(prev.get_run_time() for prev in previous_anims),
        (
            max(anim.get_run_time() for anim in animation.animations)
            if isinstance(animation, AnimationGroup)
            else animation.get_run_time()
        ),
        0,
        stay_start,
        (
            animation.animations[0].get_rate_func()
            if isinstance(animation, AnimationGroup)
            else animation.get_rate_func()
        ),
        stay_end,
    )
    run_time = (
        max(prev.get_run_time() for prev in previous_anims) +
        (
            max(anim.get_run_time() for anim in animation.animations)
            if isinstance(animation, AnimationGroup)
            else animation.get_run_time()
        )
    )
    if isinstance(animation, AnimationGroup):
        for anim in animation.animations:
            anim.set_rate_func(rate_func)
            anim.set_run_time(run_time)
    else:
        animation.set_rate_func(rate_func)
        animation.set_run_time(run_time)
    return animation


def after_animation_from_succession(anim_class, anim_args, anim_kwargs, *previous_anims):
    """
    Takes in a previous animation the next queued animation, and creates
    a new animation which waits for the previous animation to end before playing
    """
    reference_anim = anim_class(*anim_args, **anim_kwargs)

    rate_func = change_rate_func(
        max(prev.get_run_time() for prev in previous_anims),
        reference_anim.get_run_time(),
        0,
        stay_start,
        reference_anim.get_rate_func(),
        stay_end,
    )
    run_time = (
        max(prev.get_run_time() for prev in previous_anims) +
        reference_anim.get_run_time()
    )

    anim_kwargs.update({
        'rate_func': rate_func,
        'run_time': run_time,
    })

    return anim_class(*anim_args, **anim_kwargs)

# Generating polygons encasing points/sets.

def generate_hull_about_points(points, **kwargs):
    assert len(points) >= 3, "Cannot generate hull around < 3 points."
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

    return new_points

def generate_strict_enclosure_on_points(points, MAX_INNER_ANGLE=270, **kwargs):
    # First get the average of the points for the most natural radial search
    middle = np.array([
        sum(point[x] for point in points)/len(points)
        for x in range(3)
    ])
    # Order then radially (clockwise)
    q1, q2, q3, q4 = ([], [], [], [])
    for point in points:
        grad = (point[1] - middle[1]) / (point[0] - middle[0])
        if point[0] > middle[0] and point[1] > middle[1]:
            q1.append((point, grad))
        if point[0] < middle[0] and point[1] > middle[1]:
            q2.append((point, grad))
        if point[0] < middle[0] and point[1] < middle[1]:
            q3.append((point, grad))
        if point[0] > middle[0] and point[1] < middle[1]:
            q4.append((point, grad))
    q1.sort(key=lambda px: px[1])
    q2.sort(key=lambda px: px[1])
    q3.sort(key=lambda px: px[1])
    q4.sort(key=lambda px: px[1])
    # make clockwise
    sorted_points = list(map(lambda px: px[0], q1 + q2 + q3 + q4))[::-1]
    while True:
        wrapped = [sorted_points[-1]] + sorted_points + [sorted_points[0]]
        for index, (point1, point2, point3) in enumerate(zip(wrapped[:-2], wrapped[1:-1], wrapped[2:])):
            vec1 = unit_vec(point2 - point1)
            vec2 = unit_vec(point2 - point3)
            # sin = determinate, cos = dotproduct
            radians = np.arctan2(vec2[0]*vec1[1] - vec1[0]*vec2[1], np.dot(vec1, vec2))
            if radians > MAX_INNER_ANGLE:
                del sorted_points[index]
                break
        else:
            break
    return sorted_points

def buffer_polygon(points, BUFF_DIST=1.25, BUFF_SCALING=0.3, **kwargs):
    poly_points = []
    wrapped_points = [points[-1]] + points + [points[0]]
    for point1, point2, point3 in zip(wrapped_points[:-2], wrapped_points[1:-1], wrapped_points[2:]):
        vec1 = unit_vec(point2 - point1)
        vec2 = unit_vec(point2 - point3)
        combined = unit_vec(vec1 + vec2)
        sin = vec2[0]*vec1[1] - vec2[1]*vec1[0]
        if sin > 0:
            # Inward meeting, combined should exert.
            combined *= -1
        poly_points.append(
            point2 +  # Actual point
            combined * BUFF_DIST +  # Buffer out
            combined * BUFF_DIST * BUFF_SCALING * np.dot(vec1, vec2)  # Move further for tighter angles.
        )
    return poly_points

def generate_enclosure_on_points(points, method='strict', **kwargs):
    if len(points) == 1:
        circle = Circle(radius = kwargs.get('BUFF_DIST', 1.25))
        circle.move_to(points[0])
        return circle
    elif len(points) == 2:
        vec = unit_vec(points[1] - points[0])
        rot_90 = np.array([-vec[1], vec[0], 0]) * kwargs.get('BUFF_DIST', 1.25) / 2
        return generate_enclosure_on_points(np.array([
            points[0] + rot_90,
            points[0] - rot_90,
            points[1] + rot_90,
            points[1] - rot_90,
        ]), method=method, **kwargs)
    if method == 'strict':
        poly = Polygon(*buffer_polygon(generate_strict_enclosure_on_points(points, **kwargs), **kwargs))
        poly.round_corners()
        return poly
    elif method == 'convex':
        poly = Polygon(*buffer_polygon(generate_hull_about_points(points, **kwargs), **kwargs))
        poly.round_corners()
        return poly
