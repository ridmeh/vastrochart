from fractions import Fraction

from vastrochart_compute.compute.constants import NAKSHATRAS, VIM_ORDER, VIM_YEARS
from vastrochart_compute.compute.kp_sublord import (
    NAKSHATRA_ARC_FRACTION,
    compute_kp_sub_lords,
)

NAKSHATRA_ARC_DEG = float(NAKSHATRA_ARC_FRACTION)  # 13 deg 20'


def _nakshatra_start_deg(index: int) -> float:
    # Nudged a hair inside the boundary: round-tripping the exact mathematical
    # boundary through a float can land on either side depending on the index
    # (confirmed empirically - float(40/3) itself rounds up, but not every
    # multiple does). Real ephemeris longitudes never land exactly on a
    # boundary either, so testing "just inside" is the realistic case; the
    # exact-boundary transition itself is covered separately (sandhi test).
    return float(index * NAKSHATRA_ARC_FRACTION) + 1e-9


def test_start_of_every_nakshatra_sub_lord_equals_nakshatra_lord() -> None:
    # At offset 0, the first sub segment belongs to the nakshatra lord itself,
    # and the first sub-sub segment within it belongs to that same lord again.
    for index, (_name, lord) in enumerate(NAKSHATRAS):
        result = compute_kp_sub_lords(_nakshatra_start_deg(index))
        assert result.nakshatra_lord == lord
        assert result.sub_lord == lord, f"nakshatra {index} ({lord})"
        assert result.sub_sub_lord == lord, f"nakshatra {index} ({lord})"


def test_sub_lord_sequence_follows_vimshottari_order_from_nakshatra_lord() -> None:
    # Ashwini (index 0, lord Ketu): VIM_ORDER starting at Ketu is
    # Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury.
    # Walk through each sub segment's midpoint and confirm the expected lord.
    start_index = VIM_ORDER.index("Ketu")
    cursor = Fraction(0)
    for offset in range(9):
        planet = VIM_ORDER[(start_index + offset) % 9]
        segment = NAKSHATRA_ARC_FRACTION * VIM_YEARS[planet] / 120
        midpoint = float(cursor + segment / 2)
        result = compute_kp_sub_lords(midpoint)
        assert result.sub_lord == planet, (
            f"segment {offset} expected {planet}, got {result.sub_lord}"
        )
        cursor += segment


def test_sub_boundary_flip_at_exact_arithmetic_edge() -> None:
    # Ashwini's first sub (Ketu, 7/120 of the nakshatra arc) ends exactly at
    # this offset; just before it's still Ketu, at/after it's Venus (next in
    # VIM_ORDER after Ketu).
    boundary = NAKSHATRA_ARC_FRACTION * Fraction(7, 120)
    just_before = float(boundary) - 1e-9
    at_boundary = float(boundary)
    assert compute_kp_sub_lords(just_before).sub_lord == "Ketu"
    assert compute_kp_sub_lords(at_boundary).sub_lord == "Venus"


def test_nakshatra_sandhi_sub_lord_resets_to_next_nakshatra_lord() -> None:
    # Ashwini/Bharani boundary at 13 deg 20' exactly.
    ashwini_end = NAKSHATRA_ARC_DEG - 1e-9
    bharani_start = NAKSHATRA_ARC_DEG
    before = compute_kp_sub_lords(ashwini_end)
    after = compute_kp_sub_lords(bharani_start)
    assert before.nakshatra_lord == "Ketu"  # Ashwini
    assert after.nakshatra_lord == "Venus"  # Bharani
    assert after.sub_lord == "Venus"  # resets to the new nakshatra's own lord


def test_wraps_correctly_near_360_degrees() -> None:
    # Revati (last nakshatra, lord Mercury) ends at 360 deg = wraps to Ashwini.
    just_before_360 = 360.0 - 1e-6
    at_zero = 0.0
    assert compute_kp_sub_lords(just_before_360).nakshatra_lord == "Mercury"
    assert compute_kp_sub_lords(at_zero).nakshatra_lord == "Ketu"


def test_sub_arc_lengths_sum_to_full_nakshatra_arc() -> None:
    total = sum(Fraction(years, 120) for years in VIM_YEARS.values()) * NAKSHATRA_ARC_FRACTION
    assert total == NAKSHATRA_ARC_FRACTION
