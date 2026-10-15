"""`/v1/yogas` - classical yoga detection, plus the static detector registry."""

import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from vastrochart_compute.compute.yogas import compute_yogas, registry_entries
from vastrochart_compute.envelope import build_envelope
from vastrochart_compute.models.yogas import YogaCategory, YogasRequest

router = APIRouter(prefix="/v1/yogas", tags=["yogas"])

ENDPOINT_PATH = "/v1/yogas"
REGISTRY_ENDPOINT_PATH = "/v1/yogas/registry"


@router.post("")
def get_yogas(request: YogasRequest) -> dict[str, Any]:
    started_at = time.perf_counter()
    results = compute_yogas(
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        lat=request.lat,
        lon=request.lon,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
        category=request.category,
    )
    return build_envelope(
        endpoint=ENDPOINT_PATH,
        request_input=request.model_dump(),
        data={"yogas": [asdict(result) for result in results]},
        warnings=[],
        compute_started_at=started_at,
    )


@router.get("/registry")
def get_yoga_registry(category: YogaCategory = "all") -> dict[str, Any]:
    started_at = time.perf_counter()
    detectors = registry_entries(category)
    data = {
        "detectors": [
            {
                "name": detector.name,
                "sanskrit": detector.sanskrit,
                "category": detector.category,
                "confidence": detector.confidence,
                "rule_summary": detector.rule_summary,
                "notes": detector.notes,
            }
            for detector in detectors
        ]
    }
    return build_envelope(
        endpoint=REGISTRY_ENDPOINT_PATH,
        request_input={"category": category},
        data=data,
        warnings=[],
        compute_started_at=started_at,
    )
