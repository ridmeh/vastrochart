"""Pydantic request model for /v1/divisional/{varga}. Body matches
/v1/charts/compute's input minus house_systems (vargas only have Whole-Sign
houses) - varga itself comes from the URL path, not the body."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOB_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")

VargaName = Literal["D1", "D9", "D10", "D12", "D16", "D20", "D24", "D30", "D60"]


class DivisionalChartRequest(BaseModel):
    dob: str
    tob: str
    tz_offset: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri"
    node_type: Literal["true", "mean"] = "true"

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
