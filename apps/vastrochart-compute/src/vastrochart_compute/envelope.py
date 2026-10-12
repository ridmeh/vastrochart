"""Response envelope common to every endpoint (docs/09-output-schema.md).
Not compute logic - shared API plumbing, hence top-level rather than under
compute/.
"""

import time
from datetime import UTC, datetime
from typing import Any

import swisseph as swe
from ulid import ULID

API_VERSION = "1.0.0"

# Swiss Ephemeris's standard sepl/semo/seas distribution is documented by
# Astrodienst to be fit to JPL's DE431 - not independently verified from
# this specific file's binary header (which states no DE number itself).
SWISS_EPHEMERIS_DATA_SOURCE = "DE431"
MOSHIER_DATA_SOURCE = "moshier_analytical"


def new_request_id() -> str:
    return f"req_{ULID()}"


def _iso_utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_envelope(
    endpoint: str,
    request_input: dict[str, Any],
    data: dict[str, Any],
    warnings: list[dict[str, str]],
    compute_started_at: float,
    ephemeris_source: str = "swiss_ephemeris",
) -> dict[str, Any]:
    compute_ms = round((time.perf_counter() - compute_started_at) * 1000)
    data_source = (
        MOSHIER_DATA_SOURCE if ephemeris_source == "moshier" else SWISS_EPHEMERIS_DATA_SOURCE
    )
    return {
        "api_version": API_VERSION,
        "endpoint": endpoint,
        "request_id": new_request_id(),
        "computed_at": _iso_utc_now(),
        "compute_ms": compute_ms,
        "ephemeris": {
            "name": "swiss_ephemeris",
            "library_version": swe.version,
            "data_source": data_source,
        },
        "warnings": warnings,
        "input": request_input,
        "data": data,
    }


def build_error_envelope(
    endpoint: str, code: str, message: str, field: str | None, retry_safe: bool
) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "endpoint": endpoint,
        "request_id": new_request_id(),
        "error": {
            "code": code,
            "message": message,
            "field": field,
            "retry_safe": retry_safe,
            "documentation_url": f"https://docs.vastrochart.com/errors/{code}",
        },
    }
