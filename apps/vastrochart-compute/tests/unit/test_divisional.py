"""Tests verify the STATED classical rules (which I'm confident about:
movable=same sign, fixed=9th-from-self, dual=5th-from-self, etc.), not
specific "well-known" worked examples from memory - caught myself nearly
using a misremembered example as a test oracle while writing these; the
arithmetic from the stated rule is what's trustworthy here, not isolated
recalled facts.
"""

from vastrochart_compute.compute.divisional import varga_longitude

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def _sign_of(longitude: float) -> str:
    return SIGNS[int(longitude // 30) % 12]


def test_d1_is_identity() -> None:
    assert varga_longitude(123.456, "D1") == 123.456


def test_d9_movable_sign_starts_from_itself() -> None:
    # Aries (movable) 0 deg -> navamsha part 0 -> starts from Aries itself.
    result = varga_longitude(0.0, "D9")
    assert _sign_of(result) == "Aries"


def test_d9_fixed_sign_starts_from_ninth_sign() -> None:
    # Taurus (fixed, index 1) part 0 -> 9th sign from Taurus, counted
    # inclusively: Taurus=1st,...,Capricorn=9th.
    taurus_start = 30.0
    result = varga_longitude(taurus_start, "D9")
    assert _sign_of(result) == "Capricorn"


def test_d9_dual_sign_starts_from_fifth_sign() -> None:
    # Gemini (dual, index 2) part 0 -> 5th sign from Gemini, counted
    # inclusively: Gemini=1st,Cancer=2nd,Leo=3rd,Virgo=4th,Libra=5th.
    gemini_start = 60.0
    result = varga_longitude(gemini_start, "D9")
    assert _sign_of(result) == "Libra"


def test_d9_all_nine_parts_of_a_movable_sign_cycle_through_consecutive_signs() -> None:
    # Aries's 9 navamsha parts should land in Aries, Taurus, ..., Sagittarius
    # (9 consecutive signs starting from Aries).
    part_size = 30 / 9
    results = [varga_longitude(part * part_size + 0.01, "D9") for part in range(9)]
    expected = [SIGNS[i % 12] for i in range(9)]
    assert [_sign_of(r) for r in results] == expected


def test_d12_always_starts_from_same_sign() -> None:
    for sign_index in range(12):
        longitude = sign_index * 30.0
        result = varga_longitude(longitude, "D12")
        assert _sign_of(result) == SIGNS[sign_index]


def test_d30_odd_sign_first_five_degrees_is_mars_aries() -> None:
    # Aries (odd/movable per D30's odd-sign table) 0-5 deg -> Mars -> Aries.
    result = varga_longitude(2.5, "D30")
    assert _sign_of(result) == "Aries"


def test_d30_even_sign_first_five_degrees_is_venus_taurus() -> None:
    # Taurus (even) 0-5 deg -> Venus -> Taurus.
    result = varga_longitude(32.5, "D30")
    assert _sign_of(result) == "Taurus"


def test_d30_covers_the_full_30_degrees_with_no_gap() -> None:
    # Every degree 0-30 in an odd sign must fall in exactly one of the 5
    # ranges - walking across the boundary should never raise or skip.
    for tenth_degree in range(0, 300):
        degree = tenth_degree / 10
        varga_longitude(degree, "D30")  # must not raise


def test_fractional_position_within_part_is_preserved_proportionally() -> None:
    # Exactly halfway through Aries's first navamsha part (0-3.333 deg)
    # should land exactly halfway through the resulting varga sign.
    part_size = 30 / 9
    result = varga_longitude(part_size / 2, "D9")
    sign_index = int(result // 30)
    degree_in_sign = result - sign_index * 30
    assert abs(degree_in_sign - 15.0) < 1e-9


def test_all_committed_vargas_are_computable_without_error() -> None:
    for varga in ["D1", "D9", "D10", "D12", "D16", "D20", "D24", "D30", "D60"]:
        for test_longitude in [0.0, 45.5, 179.99, 359.999]:
            result = varga_longitude(test_longitude, varga)
            assert 0.0 <= result < 360.0
