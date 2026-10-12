"""`/v1/panchang` - five limbs of a day from local sunrise."""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.panchang import compute_panchang
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.panchang import PanchangRequest

router = APIRouter(prefix="/v1", tags=["panchang"])

ENDPOINT_PATH = "/v1/panchang"


@router.post("/panchang")
def get_panchang(request: PanchangRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = compute_panchang(
        date=request.date, lat=request.lat, lon=request.lon, tz_offset=request.tz_offset
    )
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data=asdict(result),
        warnings=[],
        compute_started_at=started_at,
    )
