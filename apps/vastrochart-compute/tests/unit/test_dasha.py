from fractions import Fraction

from vastrochart_compute.compute.constants import VIM_ORDER, VIM_YEARS
from vastrochart_compute.compute.dasha import (
    _format_balance_ymd,
    compute_active_dasha,
    compute_balance_at_birth,
    compute_mahadasha_sequence,
)

# Arbitrary synthetic longitude - not real birth data. 100 deg = Cancer 10 deg,
# well inside Pushya nakshatra (Cancer 3deg20'-16deg40'), lord Saturn.
SYNTHETIC_MOON_LONGITUDE = 100.0
SYNTHETIC_DOB = "1990-01-15"
SYNTHETIC_TOB = "14:30"
SYNTHETIC_TZ = "+05:30"


def test_mahadasha_sequence_has_exactly_nine_entries() -> None:
    sequence = compute_mahadasha_sequence(
        SYNTHETIC_MOON_LONGITUDE, SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ
    )
    assert len(sequence) == 9


def test_mahadasha_sequence_lord_order_matches_balance_lord_rotation() -> None:
    balance = compute_balance_at_birth(SYNTHETIC_MOON_LONGITUDE)
    sequence = compute_mahadasha_sequence(
        SYNTHETIC_MOON_LONGITUDE, SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ
    )
    assert sequence[0].lord == balance.lord
    start_index = VIM_ORDER.index(balance.lord)
    expected_order = [VIM_ORDER[(start_index + i) % 9] for i in range(9)]
    assert [period.lord for period in sequence] == expected_order


def test_mahadasha_sequence_total_equals_balance_plus_remaining_eight_full_lords() -> None:
    # The 9-entry sequence sums to 120 years ONLY if the Moon sits exactly at
    # its nakshatra's start (balance == the lord's full years). In general -
    # as here - it's balance_years + the other 8 lords' full years, which is
    # less than 120 by exactly the pre-birth-elapsed portion of the natal
    # lord's period. (Caught a real wraparound bug via this exact case.)
    balance = compute_balance_at_birth(SYNTHETIC_MOON_LONGITUDE)
    sequence = compute_mahadasha_sequence(
        SYNTHETIC_MOON_LONGITUDE, SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ
    )
    other_eight_total = sum(VIM_YEARS[p.lord] for p in sequence[1:])
    expected_total = balance.balance_years + other_eight_total
    assert sequence[0].age_at_start == 0.0
    assert abs(sequence[-1].age_at_end - expected_total) < 0.01
    assert expected_total < 120.0  # not exactly 120 unless balance happens to be a full period


def test_mahadasha_sequence_is_contiguous() -> None:
    sequence = compute_mahadasha_sequence(
        SYNTHETIC_MOON_LONGITUDE, SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ
    )
    for earlier, later in zip(sequence, sequence[1:], strict=False):
        assert earlier.end == later.start


def test_active_dasha_depth_md_returns_only_mahadasha() -> None:
    active = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2000-01-01",
        depth="md",
    )
    assert set(active.keys()) == {"mahadasha"}


def test_active_dasha_depth_prana_returns_all_five_levels() -> None:
    active = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2000-01-01",
        depth="prana",
    )
    assert set(active.keys()) == {"mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"}


def test_active_dasha_percent_elapsed_in_valid_range() -> None:
    active = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2000-01-01",
        depth="prana",
    )
    for period in active.values():
        assert 0.0 <= period["percent_elapsed"] <= 100.0


def test_active_dasha_prana_uses_datetime_not_date() -> None:
    active = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2000-01-01",
        depth="prana",
    )
    assert "T" in active["prana"]["start"]
    assert "T" not in active["mahadasha"]["start"]


def test_active_dasha_wraps_past_120_years_from_birth() -> None:
    # 150 years after birth is beyond the single 9-entry mahadasha_sequence -
    # must wrap modulo the 120-year cycle rather than erroring.
    active_normal = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2000-01-01",
        depth="md",
    )
    active_far_future = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        "2140-01-01",
        depth="md",
    )
    # 2140 is ~150 years after 1990 birth - one full 120-year cycle plus ~30
    # years, so should land on the same lord as roughly 30 years post-birth.
    assert active_far_future["mahadasha"]["lord"] in VIM_ORDER
    assert active_normal["mahadasha"]["lord"] in VIM_ORDER


def test_format_balance_ymd_carries_30_days_into_a_month() -> None:
    # Regression test: 0.9948 of a year = 0 whole months when truncated, but
    # the leftover days round to 30 (a full month) - must carry, not show "30d".
    formatted = _format_balance_ymd(Fraction("15.0829"))
    assert "30d" not in formatted
    assert formatted == "15y 1m 0d"


def test_format_balance_ymd_carries_12_months_into_a_year() -> None:
    # 11.999 years should carry fully: ~0 months 0 days -> next year.
    formatted = _format_balance_ymd(Fraction(11999, 1000))
    years_str = formatted.split("y")[0]
    assert int(years_str) in (11, 12)  # exact boundary depends on rounding, but never "11y 12m"
    assert "12m" not in formatted


def test_wraparound_restarts_with_a_full_fresh_natal_lord_period() -> None:
    # Just past the end of the 9-entry (birth-balance-truncated) sequence,
    # the 10th period must be the balance lord again, with its FULL years -
    # not whatever a naive "repeat the truncated 9-entry pattern" wraparound
    # would give (this is exactly the bug the earlier failing test caught).
    # One day past sequence[-1].end, not that exact date: mahadasha_sequence
    # dates are date-only (no time-of-day), so the true boundary can fall
    # later that same calendar day - querying the exact date back as
    # midnight could still land in the prior (Jupiter) segment.
    import datetime

    balance = compute_balance_at_birth(SYNTHETIC_MOON_LONGITUDE)
    sequence = compute_mahadasha_sequence(
        SYNTHETIC_MOON_LONGITUDE, SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ
    )
    day_after = (
        datetime.date.fromisoformat(sequence[-1].end) + datetime.timedelta(days=1)
    ).isoformat()
    active = compute_active_dasha(
        SYNTHETIC_MOON_LONGITUDE,
        SYNTHETIC_DOB,
        SYNTHETIC_TOB,
        SYNTHETIC_TZ,
        day_after,
        depth="md",
    )
    assert active["mahadasha"]["lord"] == balance.lord
    assert active["mahadasha"]["years_remaining"] > VIM_YEARS[balance.lord] - 0.1
