"""`/v1/divisional/{varga}` - divisional (varga) charts, D1 through D60."""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.divisional_chart import compute_divisional_chart
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.divisional import DivisionalChartRequest, VargaName

router = APIRouter(prefix="/v1/divisional", tags=["divisional"])


@router.post("/{varga}")
def get_divisional_chart(varga: VargaName, request: DivisionalChartRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    result = compute_divisional_chart(
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        lat=request.lat,
        lon=request.lon,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
        varga=varga,
    )
    return build_envelope(
        endpoint=f"/v1/divisional/{varga}",
        request_input=request.model_dump(),
        data=asdict(result),
        warnings=[],
        compute_started_at=started_at,
    )
