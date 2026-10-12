"""`/v1/mudda-dasha` - annual (Varshaphal) Vimshottari dasha anchored to a
solar return (ADR-030)."""

import datetime
import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.mudda import compute_mudda_dasha
from vastrochart_compute.compute.planets import compute_raw_planet_positions
from vastrochart_compute.compute.time_utils import to_julian_day_ut
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.mudda import MuddaDashaRequest

router = APIRouter(prefix="/v1", tags=["mudda-dasha"])

ENDPOINT_PATH = "/v1/mudda-dasha"


def _natal_moon_and_sun(
    dob: str, tob: str, tz_offset: str, ayanamsa: str
) -> tuple[float, float, str]:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)
    positions = compute_raw_planet_positions(jd_ut, ayanamsa)
    moon = next(p for p in positions if p.name == "Moon")
    sun = next(p for p in positions if p.name == "Sun")
    source = (
        "moshier"
        if "moshier" in (moon.ephemeris_source, sun.ephemeris_source)
        else "swiss_ephemeris"
    )
    return moon.sidereal_longitude, sun.sidereal_longitude, source


@router.post("/mudda-dasha")
def get_mudda_dasha(request: MuddaDashaRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    moon_longitude, sun_longitude, ephemeris_source = _natal_moon_and_sun(
        request.dob, request.tob, request.tz_offset, request.ayanamsa
    )
    as_of_date = request.as_of_date or datetime.date.today().isoformat()

    result = compute_mudda_dasha(
        moon_sidereal_longitude=moon_longitude,
        natal_sun_longitude=sun_longitude,
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        ayanamsa=request.ayanamsa,
        year_offset=request.year_offset,
        as_of_date=as_of_date,
    )

    warnings = []
    if ephemeris_source == "moshier":
        warnings.append(
            {
                "code": "EPHEMERIS_LOW_PRECISION_FALLBACK",
                "message": "Date outside the loaded Swiss Ephemeris file range; "
                "Sun/Moon positions computed via the lower-precision Moshier model.",
                "field": "dob",
            }
        )

    data = {
        "solar_return_date": result.solar_return_date,
        "mudda_md": asdict(result.mudda_md),
        "mudda_ad": asdict(result.mudda_ad),
    }
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input={**request.model_dump(), "as_of_date": as_of_date},
        data=data,
        warnings=warnings,
        compute_started_at=started_at,
        ephemeris_source=ephemeris_source,
    )
