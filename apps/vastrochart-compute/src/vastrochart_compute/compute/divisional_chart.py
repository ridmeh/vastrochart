"""Orchestrates a full divisional (varga) chart: D1 planets + ascendant,
remapped via compute/divisional.py, then re-derives sign/nakshatra/pada and
Whole-Sign houses from the VARGA ascendant - not the natal one. K.P. and
Placidus are D1-only, not included here.
"""

from dataclasses import dataclass

from vastrochart_compute.compute import divisional, nakshatras
from vastrochart_compute.compute import houses as houses_mod
from vastrochart_compute.compute.constants import PLANET_SANSKRIT, PLANET_SYMBOL
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.formatting import to_dms_string
from vastrochart_compute.compute.planets import (
    compute_ascendant_longitude,
    compute_raw_planet_positions,
)
from vastrochart_compute.compute.time_utils import to_julian_day_ut


@dataclass(frozen=True)
class DivisionalPlanet:
    name: str
    sanskrit: str
    symbol: str
    sidereal_longitude: float
    sidereal_longitude_formatted: str
    sign: str
    sign_lord: str
    sign_degree: float
    sign_degree_formatted: str
    house_vedic_wholesign: int


@dataclass(frozen=True)
class DivisionalAscendant:
    sidereal_longitude: float
    sidereal_longitude_formatted: str
    sign: str
    sign_lord: str
    sign_degree: float
    sign_degree_formatted: str


@dataclass(frozen=True)
class DivisionalChartResult:
    varga: str
    varga_name: str
    ascendant: DivisionalAscendant
    planets: list[DivisionalPlanet]


def compute_divisional_chart(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    ayanamsa: str,
    node_type: str,
    varga: str,
) -> DivisionalChartResult:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)

    natal_lagna = compute_ascendant_longitude(jd_ut, lat, lon, ayanamsa)
    varga_lagna_longitude = divisional.varga_longitude(natal_lagna, varga)
    varga_lagna_pos = nakshatras.locate(varga_lagna_longitude)
    ascendant = DivisionalAscendant(
        sidereal_longitude=round(varga_lagna_longitude, 4),
        sidereal_longitude_formatted=to_dms_string(varga_lagna_longitude),
        sign=varga_lagna_pos.sign,
        sign_lord=varga_lagna_pos.sign_lord,
        sign_degree=round(varga_lagna_pos.sign_degree, 4),
        sign_degree_formatted=to_dms_string(varga_lagna_pos.sign_degree),
    )

    raw_positions = compute_raw_planet_positions(jd_ut, ayanamsa, node_type)
    planets = []
    for raw in raw_positions:
        varga_longitude_value = divisional.varga_longitude(raw.sidereal_longitude, varga)
        pos = nakshatras.locate(varga_longitude_value)
        house = houses_mod.whole_sign_house(varga_longitude_value, varga_lagna_longitude)
        planets.append(
            DivisionalPlanet(
                name=raw.name,
                sanskrit=PLANET_SANSKRIT[raw.name],
                symbol=PLANET_SYMBOL[raw.name],
                sidereal_longitude=round(varga_longitude_value, 4),
                sidereal_longitude_formatted=to_dms_string(varga_longitude_value),
                sign=pos.sign,
                sign_lord=pos.sign_lord,
                sign_degree=round(pos.sign_degree, 4),
                sign_degree_formatted=to_dms_string(pos.sign_degree),
                house_vedic_wholesign=house,
            )
        )

    return DivisionalChartResult(
        varga=varga,
        varga_name=divisional.VARGA_NAMES[varga],
        ascendant=ascendant,
        planets=planets,
    )
