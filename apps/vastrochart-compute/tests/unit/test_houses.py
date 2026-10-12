from vastrochart_compute.compute.houses import compute_placidus_cusps, whole_sign_house
from vastrochart_compute.compute.planets import compute_ascendant_longitude
from vastrochart_compute.compute.time_utils import to_julian_day_ut


def test_whole_sign_lagna_is_house_one() -> None:
    # Lagna itself is always house 1, same sign.
    assert whole_sign_house(93.5, 93.5) == 1


def test_whole_sign_next_sign_is_house_two() -> None:
    # Lagna in Cancer (sign index 3); a planet in Leo (index 4) is house 2.
    lagna = 93.5  # Cancer
    planet_in_leo = 125.0
    assert whole_sign_house(planet_in_leo, lagna) == 2


def test_whole_sign_wraps_around_pisces_to_aries() -> None:
    lagna_in_pisces = 345.0  # sign index 11
    planet_in_aries = 5.0  # sign index 0
    assert whole_sign_house(planet_in_aries, lagna_in_pisces) == 2


def test_placidus_resolves_at_moderate_latitude() -> None:
    jd = to_julian_day_ut("2026-06-21", "12:00", "+00:00")
    result = compute_placidus_cusps(jd, 40.0, 10.0, "lahiri")
    assert result.cusps is not None
    assert len(result.cusps) == 12


def test_placidus_degenerates_at_deep_polar_latitude() -> None:
    # Empirically verified (ADR-022): pyswisseph raises past ~66-67 deg at
    # summer solstice for this longitude.
    jd = to_julian_day_ut("2026-06-21", "12:00", "+00:00")
    result = compute_placidus_cusps(jd, 75.0, 10.0, "lahiri")
    assert result.cusps is None


def test_ascendant_still_resolves_at_deep_polar_latitude() -> None:
    # Regression test (ADR-022 addendum): compute_ascendant_longitude used
    # to request Placidus just to read ascmc[0], which raised the same error
    # as the cusps computation and took down the whole request. It now uses
    # Whole-Sign, which resolves everywhere Placidus degenerates.
    jd = to_julian_day_ut("2026-06-21", "12:00", "+00:00")
    longitude = compute_ascendant_longitude(jd, 75.0, 10.0, "lahiri")
    assert 0.0 <= longitude < 360.0
