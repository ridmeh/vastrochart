"""Pydantic models matching docs/09-output-schema.md field-for-field.

`combust` is Optional and unset for now - blocked on the orb-threshold
decision (open item, see docs/06-roadmap.md). Leaving it None rather than
fabricating a value keeps the contract honest about what's actually computed.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_DOB_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOB_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")


class ChartComputeRequest(BaseModel):
    dob: str
    tob: str
    tz_offset: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri"
    # Accepted for forward-compatibility, no effect in v1 - both house
    # systems are always computed (ADR-020).
    house_systems: list[str] | None = None

    @field_validator("dob")
    @classmethod
    def _validate_dob(cls, value: str) -> str:
        if not _DOB_PATTERN.match(value):
            raise ValueError("dob must be YYYY-MM-DD")
        return value

    @field_validator("tob")
    @classmethod
    def _validate_tob(cls, value: str) -> str:
        if not _TOB_PATTERN.match(value):
            raise ValueError("tob must be HH:MM (24h)")
        return value

    @field_validator("tz_offset")
    @classmethod
    def _validate_tz_offset(cls, value: str) -> str:
        if not _TZ_OFFSET_PATTERN.match(value):
            raise ValueError("tz_offset must be signed HH:MM, e.g. '+05:30'")
        return value


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
