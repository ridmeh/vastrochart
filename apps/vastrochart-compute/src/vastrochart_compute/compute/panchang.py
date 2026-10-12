"""Panchang: five limbs of a day from local sunrise, with transition times.

Tithi/nakshatra/nitya_yoga/karana transition times found via Newton's
method on each limb's defining angle - see compute/boundary_finder.py.
Classical name/lord/nature tables are in compute/panchang_tables.py, with
per-table confidence notes - see that module's docstring. The astronomical
math here (angles, transition times) is exact; only the classical naming
tables carry cross-verification risk.

Sunrise uses the classical Hindu rising definition (swe.BIT_HINDU_RISING),
not generic civil sunrise - verified to differ by several minutes
(compute/sun_events.py).

No ayanamsa input in the locked schema (docs/09-output-schema.md) - panchang
is inherently a Vedic/sidereal construct, defaults to Lahiri internally,
consistent with the project default everywhere else (ADR-003).
"""

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

import swisseph as swe

from vastrochart_compute.compute import panchang_tables as tables
from vastrochart_compute.compute.boundary_finder import find_angle_crossing
from vastrochart_compute.compute.constants import AYANAMSA_MODES, NAKSHATRA_ARC_DEG, NAKSHATRAS
from vastrochart_compute.compute.dasha import jd_ut_to_local_string
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.formatting import parse_tz_offset
from vastrochart_compute.compute.sun_events import find_sunrise_jd_ut, find_sunset_jd_ut


@dataclass(frozen=True)
class PanchangResult:
    date_local: str
    sunrise_local: str
    sunset_local: str
    vara: dict[str, str]
    tithi: list[dict[str, object]]
    nakshatra: list[dict[str, object]]
    nitya_yoga: list[dict[str, object]]
    karana: list[dict[str, object]]
    muhurta_flags: dict[str, dict[str, str]]


def _sun_moon(jd_ut: float) -> tuple[float, float, float, float]:
    swe.set_sid_mode(AYANAMSA_MODES["lahiri"])
    sun_vals, _flags = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    moon_vals, _flags = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return sun_vals[0], sun_vals[3], moon_vals[0], moon_vals[3]


def _elongation_angle(jd_ut: float) -> tuple[float, float]:
    sun_long, sun_speed, moon_long, moon_speed = _sun_moon(jd_ut)
    return (moon_long - sun_long) % 360, moon_speed - sun_speed


def _nakshatra_angle(jd_ut: float) -> tuple[float, float]:
    _sun_long, _sun_speed, moon_long, moon_speed = _sun_moon(jd_ut)
    return moon_long % 360, moon_speed


def _nitya_yoga_angle(jd_ut: float) -> tuple[float, float]:
    sun_long, sun_speed, moon_long, moon_speed = _sun_moon(jd_ut)
    return (sun_long + moon_long) % 360, sun_speed + moon_speed


def _find_segments(
    angle_fn: Callable[[float], tuple[float, float]],
    step_degrees: float,
    window_start: float,
    window_end: float,
) -> list[tuple[int, float, float]]:
    """[(number, start_jd, end_jd)] - number is 1-indexed (floor(angle/step)+1),
    segments clipped to the window."""
    segments = []
    jd = window_start
    angle, speed = angle_fn(jd)
    number = int(angle // step_degrees) + 1
    guard = 0
    while jd < window_end and guard < 10:
        guard += 1
        boundary_angle = (number * step_degrees) % 360
        remaining_degrees = (boundary_angle - angle) % 360 or 360.0
        guess = jd + remaining_degrees / speed if speed > 0 else jd + 1.0
        crossing = find_angle_crossing(angle_fn, guess, boundary_angle)
        if crossing <= jd:
            crossing = jd + 0.01
        if crossing >= window_end:
            segments.append((number, jd, window_end))
            break
        segments.append((number, jd, crossing))
        jd = crossing
        angle, speed = angle_fn(jd)
        number += 1
    return segments


def compute_panchang(date: str, lat: float, lon: float, tz_offset: str) -> PanchangResult:
    configure_ephemeris_path()
    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    year, month, day = (int(part) for part in date.split("-"))

    local_midnight_ut = Fraction(swe.julday(year, month, day, 0.0)) - tz_hours / 24
    sunrise = find_sunrise_jd_ut(local_midnight_ut, lat, lon)
    next_midnight_ut = local_midnight_ut + 1
    next_sunrise = find_sunrise_jd_ut(next_midnight_ut, lat, lon)
    sunset = find_sunset_jd_ut(local_midnight_ut, lat, lon)

    window_start, window_end = float(sunrise), float(next_sunrise)

    # Python's date.weekday() is the reliable source for weekday name, not an
    # ad hoc JD-mod-7 formula (JD's own day-of-week epoch alignment is easy
    # to get subtly wrong).
    weekday = datetime.date(year, month, day).strftime("%A")
    vara_lord = tables.VARA_LORDS[weekday]

    tithi_segments = _find_segments(_elongation_angle, 12.0, window_start, window_end)
    tithi_entries: list[dict[str, object]] = []
    for number, start_jd, end_jd in tithi_segments:
        tithi_number = ((number - 1) % 30) + 1
        name, lord, nature = tables.tithi_name_lord_nature(tithi_number)
        paksha = "Shukla" if tithi_number <= 15 else "Krishna"
        tithi_entries.append(
            {
                "name": name,
                "number": tithi_number,
                "paksha": paksha,
                "lord": lord,
                "start_local": jd_ut_to_local_string(Fraction(start_jd), tz_hours, True),
                "end_local": jd_ut_to_local_string(Fraction(end_jd), tz_hours, True),
                "nature": nature,
            }
        )

    nakshatra_segments = _find_segments(
        _nakshatra_angle, NAKSHATRA_ARC_DEG, window_start, window_end
    )
    nakshatra_entries: list[dict[str, object]] = []
    for number, start_jd, end_jd in nakshatra_segments:
        nak_index = (number - 1) % 27
        name, lord = NAKSHATRAS[nak_index]
        nakshatra_entries.append(
            {
                "name": name,
                "lord": lord,
                "start_local": jd_ut_to_local_string(Fraction(start_jd), tz_hours, True),
                "end_local": jd_ut_to_local_string(Fraction(end_jd), tz_hours, True),
            }
        )

    yoga_segments = _find_segments(_nitya_yoga_angle, NAKSHATRA_ARC_DEG, window_start, window_end)
    yoga_entries: list[dict[str, object]] = []
    for number, start_jd, end_jd in yoga_segments:
        yoga_number = ((number - 1) % 27) + 1
        name, nature = tables.nitya_yoga_name_nature(yoga_number)
        yoga_entries.append(
            {
                "name": name,
                "nature": nature,
                "start_local": jd_ut_to_local_string(Fraction(start_jd), tz_hours, True),
                "end_local": jd_ut_to_local_string(Fraction(end_jd), tz_hours, True),
            }
        )

    karana_segments = _find_segments(_elongation_angle, 6.0, window_start, window_end)
    karana_entries: list[dict[str, object]] = []
    for number, start_jd, end_jd in karana_segments:
        karana_number = ((number - 1) % 60) + 1
        name, aka, nature = tables.karana_name_aka_nature(karana_number)
        karana_entries.append(
            {
                "name": name,
                "aka": aka,
                "start_local": jd_ut_to_local_string(Fraction(start_jd), tz_hours, True),
                "end_local": jd_ut_to_local_string(Fraction(end_jd), tz_hours, True),
                "nature": nature,
            }
        )

    day_length = sunset - sunrise
    segment_length = day_length / 8

    def _segment_window(segment_number: int) -> dict[str, str]:
        seg_start = sunrise + (segment_number - 1) * segment_length
        seg_end = sunrise + segment_number * segment_length
        return {
            "start_local": jd_ut_to_local_string(seg_start, tz_hours, True),
            "end_local": jd_ut_to_local_string(seg_end, tz_hours, True),
        }

    muhurta_length = day_length / 15
    abhijit_start = sunrise + 7 * muhurta_length
    abhijit_end = sunrise + 8 * muhurta_length

    return PanchangResult(
        date_local=date,
        sunrise_local=jd_ut_to_local_string(sunrise, tz_hours, True),
        sunset_local=jd_ut_to_local_string(sunset, tz_hours, True),
        vara={"weekday": weekday, "lord": vara_lord},
        tithi=tithi_entries,
        nakshatra=nakshatra_entries,
        nitya_yoga=yoga_entries,
        karana=karana_entries,
        muhurta_flags={
            "rahu_kaal": _segment_window(tables.RAHU_KAAL_SEGMENT[weekday]),
            "yamaganda": _segment_window(tables.YAMAGANDA_SEGMENT[weekday]),
            "gulika": _segment_window(tables.GULIKA_SEGMENT[weekday]),
            "abhijit": {
                "start_local": jd_ut_to_local_string(abhijit_start, tz_hours, True),
                "end_local": jd_ut_to_local_string(abhijit_end, tz_hours, True),
            },
        },
    )
