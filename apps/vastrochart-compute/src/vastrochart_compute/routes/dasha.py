"""`/v1/dasha` - Vimshottari dasha: birth balance, full MD sequence, and the
nested MD/AD/PD/Sookshma/Prana active at a date.
"""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.dasha import (
    compute_active_dasha,
    compute_balance_at_birth,
    compute_mahadasha_sequence,
)
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.planets import compute_raw_planet_positions
from vastrochart_compute.compute.time_utils import to_julian_day_ut
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.dasha import DashaRequest

router = APIRouter(prefix="/v1", tags=["dasha"])

ENDPOINT_PATH = "/v1/dasha"


def _moon_longitude_and_source(
    dob: str, tob: str, tz_offset: str, ayanamsa: str
) -> tuple[float, str]:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)
    positions = compute_raw_planet_positions(jd_ut, ayanamsa)
    moon = next(p for p in positions if p.name == "Moon")
    return moon.sidereal_longitude, moon.ephemeris_source


@router.post("/dasha")
def get_dasha(request: DashaRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    moon_longitude, ephemeris_source = _moon_longitude_and_source(
        request.dob, request.tob, request.tz_offset, request.ayanamsa
    )

    balance = compute_balance_at_birth(moon_longitude)
    sequence = compute_mahadasha_sequence(
        moon_longitude, request.dob, request.tob, request.tz_offset
    )
    active = compute_active_dasha(
        moon_longitude,
        request.dob,
        request.tob,
        request.tz_offset,
        request.as_of_date,
        request.depth,
    )

    warnings = []
    if ephemeris_source == "moshier":
        warnings.append(
            {
                "code": "EPHEMERIS_LOW_PRECISION_FALLBACK",
                "message": "Date outside the loaded Swiss Ephemeris file range; "
                "Moon position computed via the lower-precision Moshier model.",
                "field": "dob",
            }
        )

    data = {
        "balance_at_birth": asdict(balance),
        "mahadasha_sequence": [asdict(period) for period in sequence],
        "active_at_date": active,
    }
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data=data,
        warnings=warnings,
        compute_started_at=started_at,
        ephemeris_source=ephemeris_source,
    )
