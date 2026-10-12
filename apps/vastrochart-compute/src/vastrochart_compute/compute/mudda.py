"""Mudda (annual/Varshaphal) Vimshottari dasha - solar-return-anchored.

The same 120-unit Vimshottari proportional cycle used for natal dasha
(compute/dasha.py) is compressed to span one full solar year (~365.25 days),
not years - every day of the mudda year has an active lord (ADR-030,
confirmed against docs/02-domain-knowledge.md's otherwise-ambiguous wording).
1 Vimshottari-year unit = 365.25/120 ~= 3.04 days here, vs 365.25 days in
natal dasha. The birth-nakshatra balance fraction is reused unchanged every
year - it's a fixed property of the natal Moon, not something that changes
with solar returns.

Solar return: the moment transiting Sun's sidereal longitude exactly equals
natal Sun's, nearest the (year_offset)-th birthday anniversary. Found via
Newton's method - Sun's motion is smooth and near-linear over the span of a
few days, so this converges in 2-3 iterations in practice.
"""

from dataclasses import dataclass
from fractions import Fraction

import swisseph as swe

from vastrochart_compute.compute.constants import AYANAMSA_MODES
from vastrochart_compute.compute.dasha import (
    balance_truncated_segments,
    birth_jd_ut_for,
    jd_ut_to_local_string,
    julian_day_local_midnight,
)
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.formatting import parse_tz_offset
from vastrochart_compute.compute.vimshottari import locate_segment, proportion_segments

SOLAR_YEAR_DAYS = Fraction(36525, 100)  # 365.25, same convention as natal dasha
MUDDA_DAYS_PER_UNIT = SOLAR_YEAR_DAYS / 120  # ~3.04375 days per Vimshottari-year unit


@dataclass(frozen=True)
class MuddaPeriod:
    lord: str
    start: str
    end: str


@dataclass(frozen=True)
class MuddaDashaResult:
    solar_return_date: str
    mudda_md: MuddaPeriod
    mudda_ad: MuddaPeriod


def _sun_sidereal(jd_ut: float, ayanamsa: str) -> tuple[float, float]:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    values, _flags = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return values[0], values[3]


def find_solar_return_jd_ut(
    natal_sun_longitude: float, birth_jd_ut: Fraction, year_offset: int, ayanamsa: str
) -> Fraction:
    guess_jd = float(birth_jd_ut) + year_offset * 365.25
    for _ in range(15):
        sun_longitude, sun_speed = _sun_sidereal(guess_jd, ayanamsa)
        diff = ((sun_longitude - natal_sun_longitude + 180) % 360) - 180
        if abs(diff) < 1e-8:
            break
        guess_jd -= diff / sun_speed
    return Fraction(guess_jd)


def compute_mudda_dasha(
    moon_sidereal_longitude: float,
    natal_sun_longitude: float,
    dob: str,
    tob: str,
    tz_offset: str,
    ayanamsa: str,
    year_offset: int,
    as_of_date: str,
) -> MuddaDashaResult:
    configure_ephemeris_path()
    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    birth_jd_ut = birth_jd_ut_for(dob, tob, tz_offset)
    solar_return_jd_ut = find_solar_return_jd_ut(
        natal_sun_longitude, birth_jd_ut, year_offset, ayanamsa
    )

    as_of_jd_ut = julian_day_local_midnight(as_of_date) - tz_hours / 24
    elapsed = as_of_jd_ut - solar_return_jd_ut

    segments = balance_truncated_segments(moon_sidereal_longitude, MUDDA_DAYS_PER_UNIT)
    md_lord, md_start, md_end = locate_segment(elapsed, segments)

    ad_lord, ad_start_rel, ad_end_rel = locate_segment(
        elapsed - md_start, proportion_segments(md_lord, md_end - md_start)
    )
    ad_start, ad_end = md_start + ad_start_rel, md_start + ad_end_rel

    return MuddaDashaResult(
        solar_return_date=jd_ut_to_local_string(solar_return_jd_ut, tz_hours, False),
        mudda_md=MuddaPeriod(
            lord=md_lord,
            start=jd_ut_to_local_string(solar_return_jd_ut + md_start, tz_hours, False),
            end=jd_ut_to_local_string(solar_return_jd_ut + md_end, tz_hours, False),
        ),
        mudda_ad=MuddaPeriod(
            lord=ad_lord,
            start=jd_ut_to_local_string(solar_return_jd_ut + ad_start, tz_hours, False),
            end=jd_ut_to_local_string(solar_return_jd_ut + ad_end, tz_hours, False),
        ),
    )
