"""Vimshottari dasha: balance at birth, full mahadasha sequence, and the
nested MD -> AD -> PD -> Sookshma -> Prana active at a given date.

Rules (docs/02-domain-knowledge.md):
- Birth MD lord = nakshatra lord of natal Moon.
- Balance of birth MD = unused fraction of the Moon's natal nakshatra arc,
  times that lord's Vimshottari years.
- Each level's 9-fold proportional split restarts the fixed Vimshottari
  cyclic order from its own immediately-preceding lord's position - same
  rule as K.P. sub-lord, shared via compute/vimshottari.py.
- Period length convention: 1 year = 365.25 days exactly, for all real date
  arithmetic (prompts/starter-prompts.md's explicit convention). The
  mahadasha_sequence stays a fixed 9 entries (one full 120-year cycle);
  dates beyond it wrap modulo the cycle rather than extending the list
  (docs/09-output-schema.md).

Dates are formatted in the birth location's local time (the request's
tz_offset), not UT - matches how a caller specified dob/tob and how a
human reads dasha transition dates.

balance_formatted's Y/M/D breakdown uses decimal-year x 12 months, 30-day
leftover - a design choice, not an asserted universal convention (classical
software varies on this). Cross-check against golden data if available.

`balance_fraction`, `balance_truncated_segments`, `julian_day_local_midnight`,
and `jd_ut_to_local_string` are public (not underscore-prefixed) because
compute/mudda.py (Mudda/Varshaphal annual dasha, ADR-030) reuses them - same
birth-nakshatra balance basis and date-formatting logic, different time unit.
"""

from dataclasses import dataclass
from fractions import Fraction

import swisseph as swe

from vastrochart_compute.compute.constants import NAKSHATRAS, VIM_ORDER, VIM_YEARS
from vastrochart_compute.compute.formatting import parse_tz_offset
from vastrochart_compute.compute.time_utils import to_julian_day_ut
from vastrochart_compute.compute.vimshottari import Segment, locate_segment, proportion_segments

NAKSHATRA_ARC_FRACTION = Fraction(40, 3)  # 13 deg 20', exact
DAYS_PER_YEAR = Fraction(36525, 100)  # 365.25 exactly
DEPTH_ORDER = ["md", "ad", "pd", "sookshma", "prana"]
_RESULT_KEYS = {
    "md": "mahadasha",
    "ad": "antardasha",
    "pd": "pratyantardasha",
    "sookshma": "sookshma",
    "prana": "prana",
}


@dataclass(frozen=True)
class BalanceAtBirth:
    lord: str
    balance_years: float
    balance_formatted: str


@dataclass(frozen=True)
class MahadashaPeriod:
    lord: str
    start: str
    end: str
    age_at_start: float
    age_at_end: float


def balance_fraction(moon_sidereal_longitude: float) -> tuple[str, Fraction]:
    longitude = Fraction(moon_sidereal_longitude % 360)
    nakshatra_index = int(longitude // NAKSHATRA_ARC_FRACTION) % 27
    lord = NAKSHATRAS[nakshatra_index][1]
    offset_in_nakshatra = longitude - nakshatra_index * NAKSHATRA_ARC_FRACTION
    elapsed_fraction = offset_in_nakshatra / NAKSHATRA_ARC_FRACTION
    remaining_years = (1 - elapsed_fraction) * VIM_YEARS[lord]
    return lord, remaining_years


def _format_balance_ymd(years: Fraction) -> str:
    whole_years = int(years)
    total_months = (years - whole_years) * 12
    whole_months = int(total_months)
    days = round(float((total_months - whole_months) * 30))
    # Rounding the leftover days can hit exactly 30 (a full month in this
    # 30-day-month convention) when whole_months truncated away almost a
    # full month - carry it forward rather than displaying "30d".
    if days >= 30:
        days -= 30
        whole_months += 1
    if whole_months >= 12:
        whole_months -= 12
        whole_years += 1
    return f"{whole_years}y {whole_months}m {days}d"


def compute_balance_at_birth(moon_sidereal_longitude: float) -> BalanceAtBirth:
    lord, years = balance_fraction(moon_sidereal_longitude)
    return BalanceAtBirth(
        lord=lord,
        balance_years=round(float(years), 4),
        balance_formatted=_format_balance_ymd(years),
    )


def balance_truncated_segments(
    moon_sidereal_longitude: float, days_per_unit: Fraction = DAYS_PER_YEAR
) -> list[Segment]:
    """[(lord, start_days_from_anchor, end_days_from_anchor)] for the 9
    segments of one full 120-unit Vimshottari cycle - first entry is the
    birth-nakshatra balance (partial). `days_per_unit` converts Vimshottari
    "year" units into real days: 365.25 for natal dasha (1 unit = 1 real
    year), ~3.04 for Mudda dasha (120 units = 1 real solar year)."""
    lord_of_balance, balance_units = balance_fraction(moon_sidereal_longitude)
    start_index = VIM_ORDER.index(lord_of_balance)
    segments: list[Segment] = []
    cursor = Fraction(0)
    first_duration = balance_units * days_per_unit
    segments.append((lord_of_balance, cursor, cursor + first_duration))
    cursor += first_duration
    for offset in range(1, 9):
        lord = VIM_ORDER[(start_index + offset) % 9]
        duration = Fraction(VIM_YEARS[lord]) * days_per_unit
        segments.append((lord, cursor, cursor + duration))
        cursor += duration
    return segments


def julian_day_local_midnight(date_str: str) -> Fraction:
    year, month, day = (int(part) for part in date_str.split("-"))
    return Fraction(swe.julday(year, month, day, 0.0))


def jd_ut_to_local_string(jd_ut: Fraction, tz_offset_hours: Fraction, as_datetime: bool) -> str:
    local_jd = float(jd_ut + tz_offset_hours / 24)
    year, month, day, hour_frac = swe.revjul(local_jd)
    if not as_datetime:
        return f"{year:04d}-{month:02d}-{day:02d}"
    total_seconds = round(hour_frac * 3600)
    hour, remainder = divmod(total_seconds, 3600)
    minute, second = divmod(remainder, 60)
    sign = "+" if tz_offset_hours >= 0 else "-"
    offset_h = int(abs(tz_offset_hours))
    offset_m = round((abs(tz_offset_hours) - offset_h) * 60)
    return (
        f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        f"{sign}{offset_h:02d}:{offset_m:02d}"
    )


def compute_mahadasha_sequence(
    moon_sidereal_longitude: float, dob: str, tob: str, tz_offset: str
) -> list[MahadashaPeriod]:
    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    birth_jd_ut = birth_jd_ut_for(dob, tob, tz_offset)
    segments = balance_truncated_segments(moon_sidereal_longitude)
    return [
        MahadashaPeriod(
            lord=lord,
            start=jd_ut_to_local_string(birth_jd_ut + start_days, tz_hours, False),
            end=jd_ut_to_local_string(birth_jd_ut + end_days, tz_hours, False),
            age_at_start=round(float(start_days / DAYS_PER_YEAR), 2),
            age_at_end=round(float(end_days / DAYS_PER_YEAR), 2),
        )
        for lord, start_days, end_days in segments
    ]


def birth_jd_ut_for(dob: str, tob: str, tz_offset: str) -> Fraction:
    # Wraps the existing float conversion (time_utils.py) rather than
    # duplicating it - exact from this point on, since everything downstream
    # is Fraction arithmetic; only this single starting value is float-derived.
    return Fraction(to_julian_day_ut(dob, tob, tz_offset))


def _active_md_segment(moon_sidereal_longitude: float, elapsed_days: Fraction) -> Segment:
    """The birth-balance-truncated first pass (mahadasha_sequence) sums to
    LESS than 120 years whenever the Moon isn't exactly at its nakshatra's
    start (it's short by exactly the pre-birth-elapsed portion of the natal
    lord's period). So the true repeating Vimshottari cycle is NOT that
    truncated total - it's the full 120 years, which only applies starting
    AFTER the first pass completes (every full pass after that gives each
    lord its complete fixed years). Extrapolated for extreme old age (>120
    years), a case classical texts don't practically address - a reasoned
    interpretation, not a verified convention."""
    first_pass = balance_truncated_segments(moon_sidereal_longitude)
    first_pass_total = first_pass[-1][2]
    if elapsed_days < first_pass_total:
        return locate_segment(elapsed_days, first_pass)

    lord_of_balance = first_pass[0][0]
    full_cycle_days = Fraction(120) * DAYS_PER_YEAR
    full_cycle = proportion_segments(lord_of_balance, full_cycle_days)
    remaining_elapsed = elapsed_days - first_pass_total
    cycle_number = remaining_elapsed // full_cycle_days
    elapsed_in_cycle = remaining_elapsed - cycle_number * full_cycle_days
    lord, seg_start, seg_end = locate_segment(elapsed_in_cycle, full_cycle)
    offset = first_pass_total + cycle_number * full_cycle_days
    return lord, seg_start + offset, seg_end + offset


def _period_dict(
    lord: str,
    start_days: Fraction,
    end_days: Fraction,
    elapsed_days: Fraction,
    birth_jd_ut: Fraction,
    tz_hours: Fraction,
    include_years_remaining: bool,
    as_datetime: bool,
) -> dict[str, str | float]:
    duration = end_days - start_days
    percent_elapsed = (elapsed_days - start_days) / duration * 100
    result: dict[str, str | float] = {
        "lord": lord,
        "start": jd_ut_to_local_string(birth_jd_ut + start_days, tz_hours, as_datetime),
        "end": jd_ut_to_local_string(birth_jd_ut + end_days, tz_hours, as_datetime),
        "percent_elapsed": round(float(percent_elapsed), 1),
    }
    if include_years_remaining:
        result["years_remaining"] = round(float((end_days - elapsed_days) / DAYS_PER_YEAR), 2)
    return result


def compute_active_dasha(
    moon_sidereal_longitude: float,
    dob: str,
    tob: str,
    tz_offset: str,
    as_of_date: str,
    depth: str = "sookshma",
) -> dict[str, dict[str, str | float]]:
    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    birth_jd_ut = birth_jd_ut_for(dob, tob, tz_offset)
    as_of_jd_ut = julian_day_local_midnight(as_of_date) - tz_hours / 24
    elapsed = as_of_jd_ut - birth_jd_ut
    depth_index = DEPTH_ORDER.index(depth)

    result: dict[str, dict[str, str | float]] = {}

    lord, start, end = _active_md_segment(moon_sidereal_longitude, elapsed)
    result["mahadasha"] = _period_dict(
        lord, start, end, elapsed, birth_jd_ut, tz_hours, True, False
    )
    if depth_index < 1:
        return result

    parent_lord, parent_start = lord, start
    level_specs = [
        ("ad", True, False),
        ("pd", False, False),
        ("sookshma", False, False),
        ("prana", False, True),
    ]
    for level_index, (level, include_years_remaining, as_datetime) in enumerate(level_specs):
        child_lord, child_start_rel, child_end_rel = locate_segment(
            elapsed - parent_start, proportion_segments(parent_lord, end - start)
        )
        child_start = parent_start + child_start_rel
        child_end = parent_start + child_end_rel
        result[_RESULT_KEYS[level]] = _period_dict(
            child_lord,
            child_start,
            child_end,
            elapsed,
            birth_jd_ut,
            tz_hours,
            include_years_remaining,
            as_datetime,
        )
        if depth_index < level_index + 2:
            return result
        parent_lord, parent_start, start, end = child_lord, child_start, child_start, child_end

    return result
