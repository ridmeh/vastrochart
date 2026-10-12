"""Raw sidereal planetary positions via Swiss Ephemeris.

Ketu always mirrors Rahu's retrograde state and speed (ADR-023) - it's the
same node 180 deg away, never computed independently.
"""

from dataclasses import dataclass

import swisseph as swe

from vastrochart_compute.compute.constants import AYANAMSA_MODES, NODE_IDS, PLANET_IDS
from vastrochart_compute.compute.exceptions import EphemerisRangeError


@dataclass(frozen=True)
class RawPlanetPosition:
    name: str
    sidereal_longitude: float
    speed_degrees_per_day: float
    retrograde: bool
    ephemeris_source: str  # "swiss_ephemeris" (our loaded files) or "moshier" (fallback)


def _calc_ut(jd_ut: float, planet_id: int) -> tuple[float, float, str]:
    try:
        values, flags = swe.calc_ut(jd_ut, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    except swe.Error as exc:
        # calc_ut's only failure mode here is the date falling outside even
        # Moshier's own usable range - verified empirically 2026-10-12
        # (see docs/05-decisions.md). Any other library-level failure would
        # also land here; not differentiated further for now.
        raise EphemerisRangeError(str(exc)) from exc
    source = "moshier" if flags & swe.FLG_MOSEPH else "swiss_ephemeris"
    return float(values[0]), float(values[3]), source


def compute_raw_planet_positions(
    jd_ut: float, ayanamsa: str, node_type: str = "true"
) -> list[RawPlanetPosition]:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])

    positions = []
    for name, planet_id in PLANET_IDS.items():
        longitude, speed, source = _calc_ut(jd_ut, planet_id)
        positions.append(
            RawPlanetPosition(
                name=name,
                sidereal_longitude=longitude,
                speed_degrees_per_day=speed,
                retrograde=speed < 0,
                ephemeris_source=source,
            )
        )

    rahu_longitude, rahu_speed, rahu_source = _calc_ut(jd_ut, NODE_IDS[node_type])
    positions.append(
        RawPlanetPosition(
            name="Rahu",
            sidereal_longitude=rahu_longitude,
            speed_degrees_per_day=rahu_speed,
            retrograde=rahu_speed < 0,
            ephemeris_source=rahu_source,
        )
    )
    positions.append(
        RawPlanetPosition(
            name="Ketu",
            sidereal_longitude=(rahu_longitude + 180) % 360,
            speed_degrees_per_day=rahu_speed,
            retrograde=rahu_speed < 0,
            ephemeris_source=rahu_source,
        )
    )
    return positions


def compute_ascendant_longitude(jd_ut: float, lat: float, lon: float, ayanamsa: str) -> float:
    """Uses the Whole-Sign house system ('W'), not Placidus ('P'), purely to
    extract the Ascendant point - verified empirically (2026-10-12) that
    ascmc[0] is identical across house systems, but Whole-Sign still resolves
    at polar latitudes where Placidus raises swisseph.Error entirely (cusps
    AND ascmc together). Whole-Sign houses need the Ascendant to exist even
    when Placidus degenerates (ADR-022) - this was a real bug until fixed."""
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SIDEREAL)
    return float(ascmc[0])


def compute_ayanamsa_value(jd_ut: float, ayanamsa: str) -> float:
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    return float(swe.get_ayanamsa_ut(jd_ut))
