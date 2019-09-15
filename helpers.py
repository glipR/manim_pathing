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
