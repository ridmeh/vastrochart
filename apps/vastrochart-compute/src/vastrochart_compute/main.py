import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from vastrochart_compute.compute.exceptions import EphemerisRangeError
from vastrochart_compute.envelope import build_error_envelope
from vastrochart_compute.mcp.server import mcp
from vastrochart_compute.routes.charts import router as charts_router
from vastrochart_compute.routes.dasha import router as dasha_router
from vastrochart_compute.routes.divisional import router as divisional_router
from vastrochart_compute.routes.hora import router as hora_router
from vastrochart_compute.routes.mudda import router as mudda_router
from vastrochart_compute.routes.panchang import router as panchang_router
from vastrochart_compute.routes.transits import router as transits_router
from vastrochart_compute.routes.yogas import router as yogas_router

# The MCP sub-app owns its own lifespan (session management etc.) - the
# parent FastAPI app must run it too, or MCP requests fail at startup.
_mcp_app = mcp.http_app(path="/")

app = FastAPI(title="VAstroChart Compute", version="0.1.0", lifespan=_mcp_app.lifespan)
app.include_router(charts_router)
app.include_router(dasha_router)
app.include_router(mudda_router)
app.include_router(panchang_router)
app.include_router(hora_router)
app.include_router(divisional_router)
app.include_router(yogas_router)
app.include_router(transits_router)
# Mounted last, at a dedicated prefix - mounting at "/" would shadow every
# other route (verified empirically; see docs/05-decisions.md ADR-037).
app.mount("/mcp", _mcp_app)

EPHEMERIS_PATH = Path(os.environ.get("EPHEMERIS_PATH", "/opt/ephemeris"))

# Maps a failing request field to its documented error code
# (docs/09-output-schema.md "Error codes committed to"). Any field not
# listed here falls back to INVALID_REQUEST (ADR-026).
_FIELD_ERROR_CODES = {
    "dob": "INVALID_DATE",
    "tob": "INVALID_TIME",
    "tz_offset": "INVALID_TZ",
    "lat": "INVALID_LATITUDE",
    "lon": "INVALID_LONGITUDE",
    "ayanamsa": "UNSUPPORTED_AYANAMSA",
    "varga": "UNSUPPORTED_VARGA",
    "start_date": "INVALID_DATE",
    "end_date": "INVALID_DATE",
}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0]
    field = str(first_error["loc"][-1]) if first_error["loc"] else ""
    code = _FIELD_ERROR_CODES.get(field, "INVALID_REQUEST")
    return JSONResponse(
        status_code=422,
        content=build_error_envelope(
            endpoint=request.url.path,
            code=code,
            message=first_error["msg"],
            field=field or None,
            retry_safe=False,
        ),
    )


@app.exception_handler(EphemerisRangeError)
async def ephemeris_range_exception_handler(
    request: Request, _exc: EphemerisRangeError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=build_error_envelope(
            endpoint=request.url.path,
            code="DATE_OUT_OF_EPHEMERIS_RANGE",
            message="Date is outside the range the ephemeris engine can compute "
            "(roughly 3000 BCE to 3000 CE).",
            field="dob",
            retry_safe=False,
        ),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    # Never leak stack traces, file paths, or request-body content here -
    # docs/09-output-schema.md error envelope rules.
    return JSONResponse(
        status_code=500,
        content=build_error_envelope(
            endpoint=request.url.path,
            code="INTERNAL_COMPUTE_ERROR",
            message="An internal error occurred while computing this request.",
            field=None,
            retry_safe=True,
        ),
    )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, object]:
    ephemeris_files = list(EPHEMERIS_PATH.glob("*.se1")) if EPHEMERIS_PATH.exists() else []
    return {
        "status": "ok",
        "ephemeris_loaded": bool(ephemeris_files),
        "ephemeris_file_count": len(ephemeris_files),
        "fallback": None if ephemeris_files else "moshier",
    }
