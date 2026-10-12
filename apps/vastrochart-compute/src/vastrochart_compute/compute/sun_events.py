"""Sunrise/sunset, shared by panchang and hora.

Uses swe.BIT_HINDU_RISING (disc center, geocentric, no atmospheric
refraction) rather than the default civil-sunrise definition (upper limb,
with refraction) - verified empirically (2026-10-12) this gives a real,
several-minute-different result. The classical Vedic definition is the
correct one for panchang/hora, not generic Western civil sunrise.
"""

from fractions import Fraction

import swisseph as swe

from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path

_RISING_FLAGS = swe.BIT_HINDU_RISING


def find_sunrise_jd_ut(date_jd_ut_midnight: Fraction, lat: float, lon: float) -> Fraction:
    configure_ephemeris_path()
    geopos = (lon, lat, 0.0)
    _res, tret = swe.rise_trans(
        float(date_jd_ut_midnight), swe.SUN, swe.CALC_RISE | _RISING_FLAGS, geopos
    )
    return Fraction(tret[0])


def find_sunset_jd_ut(date_jd_ut_midnight: Fraction, lat: float, lon: float) -> Fraction:
    configure_ephemeris_path()
    geopos = (lon, lat, 0.0)
    _res, tret = swe.rise_trans(
        float(date_jd_ut_midnight), swe.SUN, swe.CALC_SET | _RISING_FLAGS, geopos
    )
    return Fraction(tret[0])
