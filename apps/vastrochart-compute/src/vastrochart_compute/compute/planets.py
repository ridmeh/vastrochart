"""Raw sidereal planetary positions via Swiss Ephemeris.

Ketu always mirrors Rahu's retrograde state and speed (ADR-023) - it's the
same node 180 deg away, never computed independently.
"""

from dataclasses import dataclass

import swisseph as swe

from vastrochart_compute.compute.constants import AYANAMSA_MODES, PLANET_IDS


@dataclass(frozen=True)
class RawPlanetPosition:
    name: str
    sidereal_longitude: float
    speed_degrees_per_day: float
    retrograde: bool


def compute_raw_planet_positions(jd_ut: float, ayanamsa: str) -> list[RawPlanetPosition]:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])

    positions = []
    rahu_longitude = 0.0
    rahu_speed = 0.0
    for name, planet_id in PLANET_IDS.items():
        values, _flags = swe.calc_ut(jd_ut, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        longitude, speed = values[0], values[3]
        positions.append(
            RawPlanetPosition(
                name=name,
                sidereal_longitude=longitude,
                speed_degrees_per_day=speed,
                retrograde=speed < 0,
            )
        )
        if name == "Rahu":
            rahu_longitude, rahu_speed = longitude, speed

    positions.append(
        RawPlanetPosition(
            name="Ketu",
            sidereal_longitude=(rahu_longitude + 180) % 360,
            speed_degrees_per_day=rahu_speed,
            retrograde=rahu_speed < 0,
        )
    )
    return positions


def compute_ascendant_longitude(jd_ut: float, lat: float, lon: float, ayanamsa: str) -> float:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"P", swe.FLG_SIDEREAL)
    return float(ascmc[0])


def compute_ayanamsa_value(jd_ut: float, ayanamsa: str) -> float:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    return float(swe.get_ayanamsa_ut(jd_ut))
