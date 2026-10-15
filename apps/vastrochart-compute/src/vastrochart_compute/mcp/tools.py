"""The 9 MCP tools (docs/04-mcp-spec.md), one per REST endpoint.

Each tool takes the same raw birth-data parameters as its REST
counterpart and validates them with the same Pydantic request model -
one validation contract, two transports (ADR-037). This is a deliberate
simplification from the original spec sketch, which had chart-dependent
tools (get_dasha, compute_divisional, detect_yogas, get_transit_hits,
get_mudda_dasha) take already-computed values from a prior compute_chart
call, to avoid re-deriving the ephemeris. Measured cost of a full
recompute is low single-digit milliseconds (docs/05-decisions.md
ADR-036 measured 136ms for the *heaviest* transit search, let alone a
single chart) - the efficiency the pipeline design was protecting isn't
a real cost here, and one shared contract per endpoint is less to keep
in sync than two.

Tool outputs return the same `data` shape REST puts in its envelope's
`data` field - no envelope (api_version/request_id/compute_ms aren't
meaningful outside an HTTP response), and MCP's own protocol-level error
reporting is used for invalid input/ephemeris-range failures rather than
REST's JSON error envelope.
"""

import datetime
from dataclasses import asdict
from typing import Any, Literal

from vastrochart_compute.compute.chart import compute_natal_chart
from vastrochart_compute.compute.dasha import (
    compute_active_dasha,
    compute_balance_at_birth,
    compute_mahadasha_sequence,
)
from vastrochart_compute.compute.divisional_chart import compute_divisional_chart
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.hora import compute_hora
from vastrochart_compute.compute.mudda import compute_mudda_dasha
from vastrochart_compute.compute.panchang import compute_panchang
from vastrochart_compute.compute.planets import compute_raw_planet_positions
from vastrochart_compute.compute.time_utils import to_julian_day_ut
from vastrochart_compute.compute.transits import compute_transits
from vastrochart_compute.compute.yogas import compute_yogas, registry_entries
from vastrochart_compute.mcp.server import mcp
from vastrochart_compute.models.chart import ChartComputeRequest
from vastrochart_compute.models.dasha import DashaRequest
from vastrochart_compute.models.divisional import DivisionalChartRequest, VargaName
from vastrochart_compute.models.hora import HoraRequest
from vastrochart_compute.models.mudda import MuddaDashaRequest
from vastrochart_compute.models.panchang import PanchangRequest
from vastrochart_compute.models.transits import AspectType, TransitPlanet, TransitsRequest
from vastrochart_compute.models.yogas import YogaCategory, YogasRequest


@mcp.tool
def compute_chart(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    node_type: Literal["true", "mean"] = "true",
) -> dict[str, Any]:
    """Compute a full Vedic + K.P. natal chart from birth data. Both house
    systems are always computed."""
    request = ChartComputeRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        node_type=node_type,
    )
    result = compute_natal_chart(
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        lat=request.lat,
        lon=request.lon,
        ayanamsa=request.ayanamsa,
        node_type=request.node_type,
    )
    return {**result.chart.model_dump(mode="json", by_alias=True), "warnings": result.warnings}


def _moon_longitude_and_source(
    dob: str, tob: str, tz_offset: str, ayanamsa: str
) -> tuple[float, str]:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)
    moon = next(p for p in compute_raw_planet_positions(jd_ut, ayanamsa) if p.name == "Moon")
    return moon.sidereal_longitude, moon.ephemeris_source


@mcp.tool
def get_dasha(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    as_of_date: str,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    depth: Literal["md", "ad", "pd", "sookshma", "prana"] = "sookshma",
) -> dict[str, Any]:
    """Vimshottari dasha: birth balance, the full 120-year mahadasha
    sequence, and the nested period active at as_of_date."""
    request = DashaRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        as_of_date=as_of_date,
        depth=depth,
    )
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
                "message": "Date outside the loaded Swiss Ephemeris file range; Moon position "
                "computed via the lower-precision Moshier model.",
                "field": "dob",
            }
        )
    return {
        "balance_at_birth": asdict(balance),
        "mahadasha_sequence": [asdict(period) for period in sequence],
        "active_at_date": active,
        "warnings": warnings,
    }


@mcp.tool
def get_mudda_dasha(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    year_offset: int,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Mudda (Varshaphal) annual dasha, anchored to the solar return for
    year_offset years after birth."""
    request = MuddaDashaRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        year_offset=year_offset,
        as_of_date=as_of_date,
    )
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(request.dob, request.tob, request.tz_offset)
    positions = compute_raw_planet_positions(jd_ut, request.ayanamsa)
    moon = next(p for p in positions if p.name == "Moon")
    sun = next(p for p in positions if p.name == "Sun")
    ephemeris_source = (
        "moshier"
        if "moshier" in (moon.ephemeris_source, sun.ephemeris_source)
        else "swiss_ephemeris"
    )
    resolved_as_of_date = request.as_of_date or datetime.date.today().isoformat()

    result = compute_mudda_dasha(
        moon_sidereal_longitude=moon.sidereal_longitude,
        natal_sun_longitude=sun.sidereal_longitude,
        dob=request.dob,
        tob=request.tob,
        tz_offset=request.tz_offset,
        ayanamsa=request.ayanamsa,
        year_offset=request.year_offset,
        as_of_date=resolved_as_of_date,
    )
    warnings = []
    if ephemeris_source == "moshier":
        warnings.append(
            {
                "code": "EPHEMERIS_LOW_PRECISION_FALLBACK",
                "message": "Date outside the loaded Swiss Ephemeris file range; Sun/Moon positions "
                "computed via the lower-precision Moshier model.",
                "field": "dob",
            }
        )
    return {
        "solar_return_date": result.solar_return_date,
        "mudda_md": asdict(result.mudda_md),
        "mudda_ad": asdict(result.mudda_ad),
        "as_of_date": resolved_as_of_date,
        "warnings": warnings,
    }


@mcp.tool
def get_panchang(date: str, lat: float, lon: float, tz_offset: str) -> dict[str, Any]:
    """Five limbs of a day (tithi, nakshatra, nitya_yoga, karana, vara) plus
    muhurta flags, from local Hindu sunrise."""
    request = PanchangRequest(date=date, lat=lat, lon=lon, tz_offset=tz_offset)
    result = compute_panchang(
        date=request.date, lat=request.lat, lon=request.lon, tz_offset=request.tz_offset
    )
    return asdict(result)


@mcp.tool
def get_hora(date: str, lat: float, lon: float, tz_offset: str) -> dict[str, Any]:
    """24 planetary hours (Chaldean order, unbroken across day/night)."""
    request = HoraRequest(date=date, lat=lat, lon=lon, tz_offset=tz_offset)
    result = compute_hora(
        date=request.date, lat=request.lat, lon=request.lon, tz_offset=request.tz_offset
    )
    return asdict(result)


@mcp.tool
def compute_divisional(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    varga: VargaName,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    node_type: Literal["true", "mean"] = "true",
) -> dict[str, Any]:
    """Divisional (varga) chart - D1 through D60, Whole-Sign houses only."""
    request = DivisionalChartRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        node_type=node_type,
    )
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
    return asdict(result)


@mcp.tool
def detect_yogas(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    node_type: Literal["true", "mean"] = "true",
    category: YogaCategory = "all",
) -> dict[str, Any]:
    """Classical yoga detection - the 11 high-confidence detectors
    (docs/yoga-detectors-ledger.md). Every evaluated detector is returned,
    present true or false, not just the ones that fired."""
    request = YogasRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        node_type=node_type,
        category=category,
    )
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
    return {"yogas": [asdict(result) for result in results]}


@mcp.tool
def list_yoga_detectors(category: YogaCategory = "all") -> dict[str, Any]:
    """Static catalog of every yoga detector this version evaluates - no
    birth data, mirrors /v1/yogas/registry."""
    detectors = registry_entries(category)
    return {
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


@mcp.tool
def get_transit_hits(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    ayanamsa: Literal["lahiri", "krishnamurti", "raman"] = "lahiri",
    node_type: Literal["true", "mean"] = "true",
    planets: list[TransitPlanet] | None = None,
    aspect_types: list[AspectType] | None = None,
    orb_degrees: float = 1.0,
) -> dict[str, Any]:
    """Find when transiting planets contact natal degrees, in a date
    range. Default: all 9 grahas, all 5 aspect types, 1.0 deg orb."""
    request = TransitsRequest(
        dob=dob,
        tob=tob,
        tz_offset=tz_offset,
        lat=lat,
        lon=lon,
        ayanamsa=ayanamsa,
        node_type=node_type,
        start_date=start_date,
        end_date=end_date,
        planets=planets,
        aspect_types=aspect_types,
        orb_degrees=orb_degrees,
    )
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
    return {"hits": [asdict(hit) for hit in hits]}
