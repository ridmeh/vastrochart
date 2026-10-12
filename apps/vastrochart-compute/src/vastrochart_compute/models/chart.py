"""Pydantic models matching docs/09-output-schema.md field-for-field.

K.P. sub-lord fields and `combust` are Optional and unset for now - those
land in Day 4 (sub-lord algorithm) and once combustion orbs are decided
(open item, see docs/06-roadmap.md). Leaving them None rather than
fabricating a value keeps the contract honest about what's actually computed.
"""

from pydantic import BaseModel


class AscendantModel(BaseModel):
    sidereal_longitude: float
    sidereal_longitude_formatted: str
    sign: str
    sign_lord: str
    sign_degree: float
    sign_degree_formatted: str
    nakshatra: str
    nakshatra_lord: str
    pada: int
    kp_sub_lord: str | None = None
    kp_sub_sub_lord: str | None = None


class PlanetModel(BaseModel):
    name: str
    sanskrit: str
    symbol: str
    sidereal_longitude: float
    sidereal_longitude_formatted: str
    sign: str
    sign_lord: str
    sign_degree: float
    sign_degree_formatted: str
    nakshatra: str
    nakshatra_lord: str
    pada: int
    kp_sub_lord: str | None = None
    kp_sub_sub_lord: str | None = None
    retrograde: bool
    combust: bool | None = None
    dignity: str | None = None
    speed_degrees_per_day: float
    house_vedic_wholesign: int
    house_kp_placidus: int | None = None


class WholeSignHouse(BaseModel):
    house: int
    sign: str
    sign_lord: str
    occupants: list[str]
    aspected_by: list[str] | None = None  # graha drishti not yet implemented


class PlacidusHouse(BaseModel):
    house: int
    cusp_sidereal_longitude: float
    cusp_formatted: str
    sign: str
    sign_lord: str
    nakshatra: str
    nakshatra_lord: str
    kp_sub_lord: str | None = None
    kp_sub_sub_lord: str | None = None
    occupants: list[str]


class Houses(BaseModel):
    whole_sign: list[WholeSignHouse]
    placidus_kp: list[PlacidusHouse] | None  # None when geometrically undefined (ADR-022)


class AyanamsaInfo(BaseModel):
    name: str
    value_degrees: float
    value_formatted: str


class NatalChart(BaseModel):
    ayanamsa: AyanamsaInfo
    ascendant: AscendantModel
    planets: list[PlanetModel]
    houses: Houses
