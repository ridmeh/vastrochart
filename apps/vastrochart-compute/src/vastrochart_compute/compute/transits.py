"""Transit hit search: when a transiting planet reaches an aspect angle
(conjunction/opposition/trine/square/sextile, within an orb) to a natal
point, over a date range.

Retrograde periods mean a planet's longitude isn't monotonic - the same
aspect can fire more than once around a station (a classical "triple
transit"). Rather than assuming one root per target, this samples each
transiting planet's longitude once per day across the whole range (cheap -
one ephemeris call per planet per day, independent of how many natal
points/aspects are being checked against it), finds every sign change of
the wrapped difference from the target angle, and Newton-refines each one
via compute/boundary_finder.py - same pattern as panchang's limb
transitions and mudda's solar return.

exact_date is a UTC instant; orb_entry_date/orb_exit_date are UTC calendar
dates. Transits are evaluated against a fixed ecliptic longitude, not the
birth location's clock, so there's no "local date" concept to anchor them
to the way there is for dasha/panchang - UTC was the simplest unambiguous
choice (ADR-036).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import swisseph as swe

from vastrochart_compute.compute.boundary_finder import find_angle_crossing
from vastrochart_compute.compute.constants import (
    AYANAMSA_MODES,
    CLASSICAL_PLANETS,
    NODE_IDS,
    PLANET_IDS,
)
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.exceptions import EphemerisRangeError
from vastrochart_compute.compute.planets import (
    compute_ascendant_longitude,
    compute_raw_planet_positions,
)
from vastrochart_compute.compute.time_utils import to_julian_day_ut

DEFAULT_TRANSIT_PLANETS = [*CLASSICAL_PLANETS, "Rahu", "Ketu"]

ASPECT_OFFSETS: dict[str, tuple[float, ...]] = {
    "conjunction": (0.0,),
    "sextile": (60.0, 300.0),
    "square": (90.0, 270.0),
    "trine": (120.0, 240.0),
    "opposition": (180.0,),
}
DEFAULT_ASPECT_TYPES = list(ASPECT_OFFSETS)


@dataclass(frozen=True)
class TransitHit:
    transit_planet: str
    aspect_type: str
    natal_point: str
    natal_point_longitude: float
    exact_date: str
    orb_entry_date: str
    orb_exit_date: str
    transit_longitude_at_exact: float


def _transit_longitude_speed(
    jd_ut: float, planet_name: str, ayanamsa: str, node_type: str
) -> tuple[float, float]:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    planet_id = NODE_IDS[node_type] if planet_name in ("Rahu", "Ketu") else PLANET_IDS[planet_name]
    try:
        values, _flags = swe.calc_ut(jd_ut, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    except swe.Error as exc:
        raise EphemerisRangeError(str(exc)) from exc
    longitude = (values[0] + 180) % 360 if planet_name == "Ketu" else values[0]
    return float(longitude), float(values[3])


def _wrapped_diff(value: float, target: float) -> float:
    return ((value - target + 180) % 360) - 180


def _jd_to_iso_utc(jd_ut: float) -> str:
    year, month, day, hour_frac = swe.revjul(jd_ut)
    total_seconds = round(hour_frac * 3600)
    hour, remainder = divmod(total_seconds, 3600)
    minute, second = divmod(remainder, 60)
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"


def _jd_to_date_utc(jd_ut: float) -> str:
    year, month, day, _hour_frac = swe.revjul(jd_ut)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _orb_bounds(
    planet_name: str,
    ayanamsa: str,
    node_type: str,
    exact_jd: float,
    absolute_target: float,
    orb_degrees: float,
) -> tuple[float, float]:
    _longitude, speed = _transit_longitude_speed(exact_jd, planet_name, ayanamsa, node_type)
    guess_offset = orb_degrees / max(abs(speed), 0.01)

    def angle_fn(jd: float) -> tuple[float, float]:
        return _transit_longitude_speed(jd, planet_name, ayanamsa, node_type)

    jd_a = find_angle_crossing(angle_fn, exact_jd - guess_offset, absolute_target - orb_degrees)
    jd_b = find_angle_crossing(angle_fn, exact_jd + guess_offset, absolute_target + orb_degrees)
    return min(jd_a, jd_b), max(jd_a, jd_b)


def _find_hits_for_target(
    planet_name: str,
    natal_name: str,
    natal_longitude: float,
    aspect_type: str,
    absolute_target: float,
    samples: list[float],
    start_jd: float,
    window_end_jd: float,
    ayanamsa: str,
    node_type: str,
    orb_degrees: float,
) -> list[TransitHit]:
    hits = []
    for day in range(len(samples) - 1):
        diff0 = _wrapped_diff(samples[day], absolute_target)
        diff1 = _wrapped_diff(samples[day + 1], absolute_target)
        # A real crossing has a small day-to-day change (matching the
        # planet's actual motion). A sign flip with a *large* change instead
        # means the wrapped diff jumped across its own +-180 deg
        # discontinuity (at the target's antipode) - not a true crossing.
        if diff0 * diff1 > 0 or abs(diff0 - diff1) >= 180:
            continue

        def angle_fn(jd: float) -> tuple[float, float]:
            return _transit_longitude_speed(jd, planet_name, ayanamsa, node_type)

        exact_jd = find_angle_crossing(angle_fn, start_jd + day + 0.5, absolute_target)
        if not (start_jd <= exact_jd < window_end_jd):
            continue
        transit_longitude, _speed = _transit_longitude_speed(
            exact_jd, planet_name, ayanamsa, node_type
        )
        entry_jd, exit_jd = _orb_bounds(
            planet_name, ayanamsa, node_type, exact_jd, absolute_target, orb_degrees
        )
        hits.append(
            TransitHit(
                transit_planet=planet_name,
                aspect_type=aspect_type,
                natal_point=natal_name,
                natal_point_longitude=round(natal_longitude, 4),
                exact_date=_jd_to_iso_utc(exact_jd),
                orb_entry_date=_jd_to_date_utc(entry_jd),
                orb_exit_date=_jd_to_date_utc(exit_jd),
                transit_longitude_at_exact=round(transit_longitude, 4),
            )
        )
    return hits


def compute_transits(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    ayanamsa: str,
    node_type: str,
    start_date: str,
    end_date: str,
    planets: Sequence[str] | None,
    aspect_types: Sequence[str] | None,
    orb_degrees: float,
) -> list[TransitHit]:
    configure_ephemeris_path()
    birth_jd_ut = to_julian_day_ut(dob, tob, tz_offset)

    lagna_longitude = compute_ascendant_longitude(birth_jd_ut, lat, lon, ayanamsa)
    natal_raw = compute_raw_planet_positions(birth_jd_ut, ayanamsa, node_type)
    natal_points = [("Lagna", lagna_longitude)] + [
        (raw.name, raw.sidereal_longitude) for raw in natal_raw
    ]

    transit_planets = planets if planets else DEFAULT_TRANSIT_PLANETS
    types = aspect_types if aspect_types else DEFAULT_ASPECT_TYPES

    start_y, start_m, start_d = (int(part) for part in start_date.split("-"))
    end_y, end_m, end_d = (int(part) for part in end_date.split("-"))
    start_jd = swe.julday(start_y, start_m, start_d, 0.0)
    window_end_jd = swe.julday(end_y, end_m, end_d, 0.0) + 1
    num_days = int(round(window_end_jd - start_jd))

    hits: list[TransitHit] = []
    for planet_name in transit_planets:
        samples = [
            _transit_longitude_speed(start_jd + day, planet_name, ayanamsa, node_type)[0]
            for day in range(num_days + 1)
        ]
        for natal_name, natal_longitude in natal_points:
            for aspect_type in types:
                for offset in ASPECT_OFFSETS[aspect_type]:
                    absolute_target = (natal_longitude + offset) % 360
                    hits.extend(
                        _find_hits_for_target(
                            planet_name,
                            natal_name,
                            natal_longitude,
                            aspect_type,
                            absolute_target,
                            samples,
                            start_jd,
                            window_end_jd,
                            ayanamsa,
                            node_type,
                            orb_degrees,
                        )
                    )
    hits.sort(key=lambda hit: hit.exact_date)
    return hits
