"""Pydantic request model for /v1/transits."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOB_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")

TransitPlanet = Literal[
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
]
AspectType = Literal["conjunction", "opposition", "trine", "square", "sextile"]


class TransitsRequest(BaseModel):
    dob: str
    tob: str
    tz_offset: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri"
    node_type: Literal["true", "mean"] = "true"
    start_date: str
    end_date: str
    planets: list[TransitPlanet] | None = None
    aspect_types: list[AspectType] | None = None
    orb_degrees: float = Field(default=1.0, gt=0, le=15)

    @field_validator("dob")
    @classmethod
    def _validate_dob(cls, value: str) -> str:
        if not _DATE_PATTERN.match(value):
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

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_range_date(cls, value: str) -> str:
        if not _DATE_PATTERN.match(value):
            raise ValueError("must be YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def _validate_range_order(self) -> "TransitsRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self
