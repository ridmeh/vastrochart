"""`/v1/hora` - 24 planetary hours for a day."""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.hora import compute_hora
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.hora import HoraRequest

router = APIRouter(prefix="/v1", tags=["hora"])

ENDPOINT_PATH = "/v1/hora"


@router.post("/hora")
def get_hora(request: HoraRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = compute_hora(
        date=request.date, lat=request.lat, lon=request.lon, tz_offset=request.tz_offset
    )
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data=asdict(result),
        warnings=[],
        compute_started_at=started_at,
    )
