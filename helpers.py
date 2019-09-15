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
