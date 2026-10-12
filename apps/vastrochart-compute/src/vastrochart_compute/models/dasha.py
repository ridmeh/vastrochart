"""Pydantic models for /v1/dasha, matching docs/09-output-schema.md.

node_type is deliberately NOT part of this request - Vimshottari dasha
depends only on the Moon's nakshatra lord, never Rahu/Ketu, so True vs Mean
node is not applicable here.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOB_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")


class DashaRequest(BaseModel):
    dob: str
    tob: str
    tz_offset: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri"
    as_of_date: str
    depth: Literal["md", "ad", "pd", "sookshma", "prana"] = "sookshma"

    @field_validator("dob", "as_of_date")
    @classmethod
    def _validate_date(cls, value: str) -> str:
        if not _DATE_PATTERN.match(value):
            raise ValueError("date must be YYYY-MM-DD")
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
