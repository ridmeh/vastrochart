"""`/v1/transits` - transit hit search over a date range."""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.transits import compute_transits
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.transits import TransitsRequest

router = APIRouter(prefix="/v1", tags=["transits"])

ENDPOINT_PATH = "/v1/transits"


@router.post("/transits")
def get_transits(request: TransitsRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    hits = compute_transits(
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        lat=request.lat,
        lon=request.lon,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
        start_date=request.start_date,
        end_date=request.end_date,
        planets=request.planets,
        aspect_types=request.aspect_types,
        orb_degrees=request.orb_degrees,
    )
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data={"hits": [asdict(hit) for hit in hits]},
        warnings=[],
        compute_started_at=started_at,
    )
