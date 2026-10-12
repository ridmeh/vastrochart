"""`/v1/charts/compute` - core natal chart endpoint."""

import time
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.chart import compute_natal_chart
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.chart import ChartComputeRequest

router = APIRouter(prefix="/v1/charts", tags=["charts"])

ENDPOINT_PATH = "/v1/charts/compute"


@router.post("/compute")
def compute_chart(request: ChartComputeRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = compute_natal_chart(
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        lat=request.lat,
        lon=request.lon,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data=result.chart.model_dump(mode="json", by_alias=True),
        warnings=result.warnings,
        compute_started_at=started_at,
        ephemeris_source=result.ephemeris_source,
    )
