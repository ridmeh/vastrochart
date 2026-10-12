"""Local birth time -> UT Julian Day conversion."""

import swisseph as swe

from vastrochart_compute.compute.formatting import parse_tz_offset


def to_julian_day_ut(dob: str, tob: str, tz_offset: str) -> float:
    """dob: 'YYYY-MM-DD', tob: 'HH:MM', tz_offset: signed string e.g. '+05:30'."""
    year, month, day = (int(part) for part in dob.split("-"))
    hour, minute = (int(part) for part in tob.split(":"))
    local_hours = hour + minute / 60
    ut_hours = local_hours - parse_tz_offset(tz_offset)
    return float(swe.julday(year, month, day, ut_hours))
