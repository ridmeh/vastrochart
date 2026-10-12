"""24 planetary hours (hora) per day - Chaldean order throughout.

Chaldean order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon) cycles
continuously across all 24 horas - the 12 night horas are NOT a fresh
restart, they continue the same 7-planet cycle from wherever hora 12 left
off. First hora of the day always equals that weekday's own lord
(docs/02-domain-knowledge.md).

Nature (benefic/malefic/neutral) per lord is a well-established classical
classification. best_for/avoid_for activity lists are LOWER CONFIDENCE: a
reasonable construction from each planet's classical significations, not a
literally memorized hora-activity table from one specific text - flagged
here and to the user, same spirit as compute/panchang_tables.py.
"""

import datetime
from dataclasses import dataclass
from fractions import Fraction

from vastrochart_compute.compute.dasha import jd_ut_to_local_string
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.formatting import parse_tz_offset
from vastrochart_compute.compute.panchang_tables import VARA_LORDS
from vastrochart_compute.compute.sun_events import find_sunrise_jd_ut, find_sunset_jd_ut
from vastrochart_compute.compute.time_utils import to_julian_day_ut

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

_LORD_PROFILE: dict[str, tuple[str, list[str], list[str]]] = {
    "Saturn": ("malefic", ["discipline", "routine_work"], ["new_initiatives", "travel"]),
    "Mars": ("malefic", ["surgery"], ["new_initiatives", "ceremonies", "travel"]),
    "Jupiter": ("benefic", ["study", "contracts", "ceremonies"], []),
    "Sun": ("neutral", ["meetings", "contracts"], []),
    "Venus": ("benefic", ["ceremonies", "contracts"], []),
    "Mercury": ("neutral", ["study", "writing", "contracts"], []),
    "Moon": ("benefic", ["travel", "meetings"], []),
}


@dataclass(frozen=True)
class HoraResult:
    date_local: str
    sunrise_local: str
    sunset_local: str
    day_hora_minutes: float
    night_hora_minutes: float
    horas: list[dict[str, object]]


def compute_hora(date: str, lat: float, lon: float, tz_offset: str) -> HoraResult:
    configure_ephemeris_path()
    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    year, month, day = (int(part) for part in date.split("-"))

    local_midnight_ut = Fraction(to_julian_day_ut(date, "00:00", tz_offset))
    sunrise = find_sunrise_jd_ut(local_midnight_ut, lat, lon)
    sunset = find_sunset_jd_ut(local_midnight_ut, lat, lon)
    next_sunrise = find_sunrise_jd_ut(local_midnight_ut + 1, lat, lon)

    day_hora_days = (sunset - sunrise) / 12
    night_hora_days = (next_sunrise - sunset) / 12

    weekday = datetime.date(year, month, day).strftime("%A")
    start_index = CHALDEAN_ORDER.index(VARA_LORDS[weekday])

    horas: list[dict[str, object]] = []
    for index in range(1, 25):
        lord = CHALDEAN_ORDER[(start_index + index - 1) % 7]
        nature, best_for, avoid_for = _LORD_PROFILE[lord]
        if index <= 12:
            start_jd = sunrise + (index - 1) * day_hora_days
            end_jd = sunrise + index * day_hora_days
            day_or_night = "day"
        else:
            night_index = index - 12
            start_jd = sunset + (night_index - 1) * night_hora_days
            end_jd = sunset + night_index * night_hora_days
            day_or_night = "night"
        horas.append(
            {
                "index": index,
                "start_local": jd_ut_to_local_string(start_jd, tz_hours, True),
                "end_local": jd_ut_to_local_string(end_jd, tz_hours, True),
                "lord": lord,
                "day_or_night": day_or_night,
                "nature": nature,
                "best_for": best_for,
                "avoid_for": avoid_for,
            }
        )

    return HoraResult(
        date_local=date,
        sunrise_local=jd_ut_to_local_string(sunrise, tz_hours, True),
        sunset_local=jd_ut_to_local_string(sunset, tz_hours, True),
        day_hora_minutes=round(float(day_hora_days) * 1440, 2),
        night_hora_minutes=round(float(night_hora_days) * 1440, 2),
        horas=horas,
    )
