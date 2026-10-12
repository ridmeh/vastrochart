"""Pydantic models for /v1/mudda-dasha.

as_of_date is optional (default: today) - not in the originally-locked
schema example, added deliberately (ADR-030) since the output otherwise has
no way to say which day within the mudda year mudda_md/mudda_ad describe.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOB_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")


class MuddaDashaRequest(BaseModel):
    dob: str
    tob: str
    tz_offset: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri"
    year_offset: int = Field(ge=0)
    as_of_date: str | None = None

    @field_validator("dob")
    @classmethod
    def _validate_dob(cls, value: str) -> str:
        if not _DATE_PATTERN.match(value):
            raise ValueError("dob must be YYYY-MM-DD")
        return value

    @field_validator("as_of_date")
    @classmethod
    def _validate_as_of_date(cls, value: str | None) -> str | None:
        if value is not None and not _DATE_PATTERN.match(value):
            raise ValueError("as_of_date must be YYYY-MM-DD")
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
