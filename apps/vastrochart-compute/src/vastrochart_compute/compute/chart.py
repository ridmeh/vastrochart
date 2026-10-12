"""Natal chart orchestrator: ties together ephemeris, nakshatra, dignity,
house, and K.P. sub-lord modules into the response shape
docs/09-output-schema.md defines.

`combust` is still pending (blocked on the orb-threshold decision,
docs/06-roadmap.md open items). Aspects and nakshatra_distribution are not
part of this module.
"""

from dataclasses import dataclass, field

from vastrochart_compute.compute import dignity as dignity_mod
from vastrochart_compute.compute import houses as houses_mod
from vastrochart_compute.compute import kp_sublord, nakshatras
from vastrochart_compute.compute.constants import CLASSICAL_PLANETS, PLANET_SANSKRIT, PLANET_SYMBOL
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.formatting import to_dms_string
from vastrochart_compute.compute.planets import (
    compute_ascendant_longitude,
    compute_ayanamsa_value,
    compute_raw_planet_positions,
)
from vastrochart_compute.compute.time_utils import to_julian_day_ut
from vastrochart_compute.models.chart import (
    AscendantModel,
    AyanamsaInfo,
    Houses,
    NatalChart,
    PlacidusHouse,
    PlanetModel,
    WholeSignHouse,
)


@dataclass
class ChartComputeResult:
    chart: NatalChart
    warnings: list[dict[str, str]] = field(default_factory=list)
    ephemeris_source: str = "swiss_ephemeris"  # or "moshier" - see EPHEMERIS_LOW_PRECISION_FALLBACK


def _build_planet_models(
    jd_ut: float, lagna_longitude: float, ayanamsa: str
) -> tuple[list[PlanetModel], str]:
    """Returns (planet models, ephemeris_source) - source is "moshier" if any
    planet fell back to it, else "swiss_ephemeris"."""
    raw_positions = compute_raw_planet_positions(jd_ut, ayanamsa)
    zodiacal = {p.name: nakshatras.locate(p.sidereal_longitude) for p in raw_positions}
    other_signs = {name: zodiacal[name].sign for name in CLASSICAL_PLANETS}
    ephemeris_source = (
        "moshier"
        if any(p.ephemeris_source == "moshier" for p in raw_positions)
        else "swiss_ephemeris"
    )

    models = []
    for raw in raw_positions:
        pos = zodiacal[raw.name]
        dignity_value = dignity_mod.compute_dignity(
            raw.name, pos.sign, pos.sign_degree, other_signs
        )
        sub_lords = kp_sublord.compute_kp_sub_lords(raw.sidereal_longitude)
        models.append(
            PlanetModel(
                name=raw.name,
                sanskrit=PLANET_SANSKRIT[raw.name],
                symbol=PLANET_SYMBOL[raw.name],
                sidereal_longitude=round(raw.sidereal_longitude, 4),
                sidereal_longitude_formatted=to_dms_string(raw.sidereal_longitude),
                sign=pos.sign,
                sign_lord=pos.sign_lord,
                sign_degree=round(pos.sign_degree, 4),
                sign_degree_formatted=to_dms_string(pos.sign_degree),
                nakshatra=pos.nakshatra,
                nakshatra_lord=pos.nakshatra_lord,
                pada=pos.pada,
                kp_sub_lord=sub_lords.sub_lord,
                kp_sub_sub_lord=sub_lords.sub_sub_lord,
                retrograde=raw.retrograde,
                dignity=dignity_value,
                speed_degrees_per_day=round(raw.speed_degrees_per_day, 4),
                house_vedic_wholesign=houses_mod.whole_sign_house(
                    raw.sidereal_longitude, lagna_longitude
                ),
            )
        )
    return models, ephemeris_source


def _build_whole_sign_houses(
    lagna_longitude: float, planets: list[PlanetModel]
) -> list[WholeSignHouse]:
    from vastrochart_compute.compute.constants import SIGN_LORDS, SIGNS

    lagna_sign_index = int(lagna_longitude // 30)
    result = []
    for house_number in range(1, 13):
        sign = SIGNS[(lagna_sign_index + house_number - 1) % 12]
        occupants = [p.name for p in planets if p.house_vedic_wholesign == house_number]
        result.append(
            WholeSignHouse(
                house=house_number, sign=sign, sign_lord=SIGN_LORDS[sign], occupants=occupants
            )
        )
    return result


def _build_placidus_houses(cusps: list[float], planets: list[PlanetModel]) -> list[PlacidusHouse]:
    result = []
    for house_number in range(1, 13):
        cusp_longitude = cusps[house_number - 1]
        pos = nakshatras.locate(cusp_longitude)
        sub_lords = kp_sublord.compute_kp_sub_lords(cusp_longitude)
        occupants = [
            p.name
            for p in planets
            if houses_mod.placidus_house_for(p.sidereal_longitude, cusps) == house_number
        ]
        result.append(
            PlacidusHouse(
                house=house_number,
                cusp_sidereal_longitude=round(cusp_longitude, 4),
                cusp_formatted=f"{pos.sign} {to_dms_string(pos.sign_degree)}",
                sign=pos.sign,
                sign_lord=pos.sign_lord,
                nakshatra=pos.nakshatra,
                nakshatra_lord=pos.nakshatra_lord,
                kp_sub_lord=sub_lords.sub_lord,
                kp_sub_sub_lord=sub_lords.sub_sub_lord,
                occupants=occupants,
            )
        )
    return result


def compute_natal_chart(
    dob: str, tob: str, tz_offset: str, lat: float, lon: float, ayanamsa: str = "lahiri"
) -> ChartComputeResult:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)
    lagna_longitude = compute_ascendant_longitude(jd_ut, lat, lon, ayanamsa)
    lagna_pos = nakshatras.locate(lagna_longitude)
    lagna_sub_lords = kp_sublord.compute_kp_sub_lords(lagna_longitude)

    ascendant = AscendantModel(
        sidereal_longitude=round(lagna_longitude, 4),
        sidereal_longitude_formatted=to_dms_string(lagna_longitude),
        sign=lagna_pos.sign,
        sign_lord=lagna_pos.sign_lord,
        sign_degree=round(lagna_pos.sign_degree, 4),
        sign_degree_formatted=to_dms_string(lagna_pos.sign_degree),
        nakshatra=lagna_pos.nakshatra,
        nakshatra_lord=lagna_pos.nakshatra_lord,
        pada=lagna_pos.pada,
        kp_sub_lord=lagna_sub_lords.sub_lord,
        kp_sub_sub_lord=lagna_sub_lords.sub_sub_lord,
    )

    planets, ephemeris_source = _build_planet_models(jd_ut, lagna_longitude, ayanamsa)
    whole_sign = _build_whole_sign_houses(lagna_longitude, planets)

    placidus_result = houses_mod.compute_placidus_cusps(jd_ut, lat, lon, ayanamsa)
    warnings: list[dict[str, str]] = []
    if ephemeris_source == "moshier":
        warnings.append(
            {
                "code": "EPHEMERIS_LOW_PRECISION_FALLBACK",
                "message": "Date outside the loaded Swiss Ephemeris file range; "
                "planetary positions computed via the lower-precision Moshier model.",
                "field": "dob",
            }
        )
    placidus_kp: list[PlacidusHouse] | None = None
    if placidus_result.cusps is not None:
        placidus_kp = _build_placidus_houses(placidus_result.cusps, planets)
        for planet in planets:
            planet.house_kp_placidus = houses_mod.placidus_house_for(
                planet.sidereal_longitude, placidus_result.cusps
            )
    else:
        warnings.append(
            {
                "code": "PLACIDUS_DEGENERATE_AT_LATITUDE",
                "message": "Placidus undefined at this latitude/date; whole_sign still computed.",
                "field": "lat",
            }
        )

    ayanamsa_value = compute_ayanamsa_value(jd_ut, ayanamsa)
    chart = NatalChart(
        ayanamsa=AyanamsaInfo(
            name=ayanamsa,
            value_degrees=round(ayanamsa_value, 4),
            value_formatted=to_dms_string(ayanamsa_value),
        ),
        ascendant=ascendant,
        planets=planets,
        houses=Houses(whole_sign=whole_sign, placidus_kp=placidus_kp),
    )
    return ChartComputeResult(chart=chart, warnings=warnings, ephemeris_source=ephemeris_source)
