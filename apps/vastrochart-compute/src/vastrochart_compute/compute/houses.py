"""Whole-Sign (Vedic) and Placidus (K.P.) house assignment.

Placidus can be geometrically undefined at deep polar latitudes (ADR-022) -
callers should treat a None cusps list as "Placidus unavailable here", not
as an error.
"""

from dataclasses import dataclass

import swisseph as swe

from vastrochart_compute.compute.constants import AYANAMSA_MODES, SIGNS


def whole_sign_house(sidereal_longitude: float, lagna_sidereal_longitude: float) -> int:
    lagna_sign_index = int(lagna_sidereal_longitude // 30)
    planet_sign_index = int(sidereal_longitude // 30)
    return (planet_sign_index - lagna_sign_index) % 12 + 1


@dataclass(frozen=True)
class PlacidusResult:
    cusps: list[float] | None  # 12 sidereal cusp longitudes, index 0 = house 1; None if undefined


def compute_placidus_cusps(jd_ut: float, lat: float, lon: float, ayanamsa: str) -> PlacidusResult:
    """Empirically verified (2026-10-12): pyswisseph's houses_ex returns a flat
    12-element list (index 0 = house 1 = Ascendant) and raises swisseph.Error
    on Placidus degeneracy - it does not return degenerate zero cusps."""
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    try:
        cusps, _ascmc = swe.houses_ex(jd_ut, lat, lon, b"P", swe.FLG_SIDEREAL)
    except swe.Error:
        return PlacidusResult(cusps=None)
    return PlacidusResult(cusps=list(cusps))


def placidus_house_for(sidereal_longitude: float, cusps: list[float]) -> int:
    for house_index in range(12):
        start = cusps[house_index]
        end = cusps[(house_index + 1) % 12]
        if end < start:  # arc crosses 0 deg Aries
            if sidereal_longitude >= start or sidereal_longitude < end:
                return house_index + 1
        else:
            if start <= sidereal_longitude < end:
                return house_index + 1
    return 1  # unreachable for a well-formed 12-cusp list


def sign_of(sidereal_longitude: float) -> str:
    return SIGNS[int((sidereal_longitude % 360) // 30)]
