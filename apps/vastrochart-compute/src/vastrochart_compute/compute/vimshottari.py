"""Shared Vimshottari proportional-segment logic.

Both K.P. sub-lord (compute/kp_sublord.py, degree-based) and Vimshottari
dasha (compute/dasha.py, day-based) subdivide a span into 9 segments,
proportioned by VIM_YEARS, in the fixed cyclic VIM_ORDER starting from a
given lord. One implementation, one source of truth for that rule, so the
two can't silently diverge.

Uses exact rational arithmetic (fractions.Fraction) throughout - proportional
division never drifts a boundary from accumulated float rounding, which
matters across multiple nested levels (MD -> AD -> PD -> Sookshma -> Prana).
"""

from fractions import Fraction

from vastrochart_compute.compute.constants import VIM_ORDER, VIM_YEARS

TOTAL_VIM_YEARS = 120

Segment = tuple[str, Fraction, Fraction]  # (lord, segment_start, segment_end)


def proportion_segments(start_lord: str, span: Fraction) -> list[Segment]:
    """9 segments spanning [0, span), Vimshottari cyclic order from start_lord."""
    start_index = VIM_ORDER.index(start_lord)
    segments: list[Segment] = []
    cursor = Fraction(0)
    for offset in range(9):
        lord = VIM_ORDER[(start_index + offset) % 9]
        length = span * VIM_YEARS[lord] / TOTAL_VIM_YEARS
        segments.append((lord, cursor, cursor + length))
        cursor += length
    return segments


def locate_segment(offset: Fraction, segments: list[Segment]) -> Segment:
    for segment in segments:
        if offset < segment[2]:
            return segment
    return segments[-1]  # offset exactly at the end of the span
