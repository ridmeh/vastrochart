"""Unit tests for compute/transits.py, verified against real ephemeris
output computed and hand-checked before being hardcoded here - same
approach as the yoga detector tests (ADR-035).

Ground truth: the project's existing reference chart (dob 1990-01-15,
14:30 +05:30, Delhi, Lahiri - Lagna sidereal longitude 47.4127 deg).
Moon's sidereal month is ~27.32 days, so a year should show either 13 or
14 Moon-Lagna conjunctions depending on phase alignment at the start of
the window - this also regression-tests a real bug caught while building
this: the wrapped-difference bracket detector was firing a false crossing
at the *antipode* of the target (where the +-180 deg wrap discontinuity
sits), doubling every count to ~27 before the fix.
"""

from vastrochart_compute.compute.transits import (
    ASPECT_OFFSETS,
    DEFAULT_ASPECT_TYPES,
    DEFAULT_TRANSIT_PLANETS,
    _wrapped_diff,
    compute_transits,
)

REFERENCE_BODY = {
    "dob": "1990-01-15",
    "tob": "14:30",
    "tz_offset": "+05:30",
    "lat": 28.6139,
    "lon": 77.2090,
    "ayanamsa": "lahiri",
    "node_type": "true",
}


def _lagna_moon_conjunctions(start_date: str, end_date: str, orb_degrees: float = 1.0) -> list:
    hits = compute_transits(
        **REFERENCE_BODY,
        start_date=start_date,
        end_date=end_date,
        planets=["Moon"],
        aspect_types=["conjunction"],
        orb_degrees=orb_degrees,
    )
    return [hit for hit in hits if hit.natal_point == "Lagna"]


def test_wrapped_diff_stays_in_plus_minus_180() -> None:
    for value in [0.0, 90.0, 179.9, 180.1, 270.0, 359.9]:
        assert -180 < _wrapped_diff(value, 47.4127) <= 180


def test_aspect_offsets_cover_the_five_classical_types() -> None:
    assert set(ASPECT_OFFSETS) == {"conjunction", "opposition", "trine", "square", "sextile"}
    assert ASPECT_OFFSETS["conjunction"] == (0.0,)
    assert ASPECT_OFFSETS["opposition"] == (180.0,)
    assert len(ASPECT_OFFSETS["sextile"]) == 2
    assert len(ASPECT_OFFSETS["square"]) == 2
    assert len(ASPECT_OFFSETS["trine"]) == 2


def test_default_transit_planets_is_nine_grahas() -> None:
    assert set(DEFAULT_TRANSIT_PLANETS) == {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    }


def test_default_aspect_types_matches_registry() -> None:
    assert set(DEFAULT_ASPECT_TYPES) == set(ASPECT_OFFSETS)


def test_narrow_window_finds_exactly_one_conjunction() -> None:
    hits = _lagna_moon_conjunctions("2025-12-28", "2026-01-05")
    assert len(hits) == 1
    hit = hits[0]
    assert hit.exact_date == "2026-01-01T07:51:54Z"
    assert hit.orb_entry_date == "2026-01-01"
    assert hit.orb_exit_date == "2026-01-01"
    assert abs(hit.transit_longitude_at_exact - hit.natal_point_longitude) < 1e-3


def test_full_year_conjunction_count_matches_sidereal_month_not_doubled() -> None:
    # Regression test for the antipode-wraparound false-bracket bug - a
    # naive sign-flip-only detector returned 27 hits here (every real
    # crossing duplicated with a phantom one ~13.6 days off), not ~13-14.
    hits = _lagna_moon_conjunctions("2026-01-01", "2026-12-31")
    assert 13 <= len(hits) <= 14
    dates = [hit.exact_date for hit in hits]
    assert len(dates) == len(set(dates))  # no duplicate timestamps


def test_wider_orb_widens_the_entry_exit_window() -> None:
    narrow = _lagna_moon_conjunctions("2026-01-01", "2026-12-31", orb_degrees=0.1)[0]
    wide = _lagna_moon_conjunctions("2026-01-01", "2026-12-31", orb_degrees=5.0)[0]
    assert wide.orb_entry_date <= narrow.orb_entry_date
    assert wide.orb_exit_date >= narrow.orb_exit_date


def test_hits_are_sorted_chronologically() -> None:
    hits = compute_transits(
        **REFERENCE_BODY,
        start_date="2026-01-01",
        end_date="2026-03-31",
        planets=None,
        aspect_types=["conjunction"],
        orb_degrees=1.0,
    )
    dates = [hit.exact_date for hit in hits]
    assert dates == sorted(dates)
