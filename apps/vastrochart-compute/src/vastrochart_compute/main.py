import os
from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="VAstroChart Compute", version="0.1.0")

EPHEMERIS_PATH = Path(os.environ.get("EPHEMERIS_PATH", "/opt/ephemeris"))


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
