"""Pydantic request model for /v1/panchang."""

import re

from pydantic import BaseModel, Field, field_validator

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TZ_OFFSET_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")


class PanchangRequest(BaseModel):
    date: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    tz_offset: str

    @field_validator("date")
    @classmethod
    def _validate_date(cls, value: str) -> str:
        if not _DATE_PATTERN.match(value):
            raise ValueError("date must be YYYY-MM-DD")
        return value

    @field_validator("tz_offset")
    @classmethod
    def _validate_tz_offset(cls, value: str) -> str:
        if not _TZ_OFFSET_PATTERN.match(value):
            raise ValueError("tz_offset must be signed HH:MM, e.g. '+05:30'")
        return value
