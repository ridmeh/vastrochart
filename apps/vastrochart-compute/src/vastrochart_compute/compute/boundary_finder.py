"""Generic Newton's-method root finder for 'when does this angle cross a
given boundary degree' - shared by panchang's tithi/nakshatra/nitya_yoga/
karana transition-time search. Same pattern as the solar return search
(compute/mudda.py): the angle is smooth and near-linear over the span of a
day, so this converges in a handful of iterations in practice.
"""

from collections.abc import Callable

# (angle_degrees, speed_degrees_per_day) at a given UT Julian day.
AngleFn = Callable[[float], tuple[float, float]]


def find_angle_crossing(angle_fn: AngleFn, jd_guess: float, target_angle: float) -> float:
    jd = jd_guess
    for _ in range(20):
        angle, speed = angle_fn(jd)
        diff = ((angle - target_angle + 180) % 360) - 180
        if abs(diff) < 1e-7:
            break
        jd -= diff / speed
    return jd
