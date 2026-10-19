"""Point pyswisseph at the Swiss Ephemeris data directory.

Must run before any swe.calc_ut/houses_ex/get_ayanamsa_ut call, or
pyswisseph silently falls back to the lower-precision Moshier ephemeris
(apps/vastrochart-compute/ephemeris/NOTE.md).

swe.set_ephe_path() is thread-local, not process-global - verified
empirically (a second OS thread that never calls it falls back to
Moshier even though a first thread already did, 2026-10-18). FastAPI
runs each sync route handler in a thread-pool worker thread, and
consecutive requests can land on different threads, so a plain
module-level "already configured" boolean is wrong: it was found True
on a thread that was never actually configured, silently degrading a
real production request to Moshier precision with no error raised.
threading.local() makes the "already configured" check correctly
per-thread instead.
"""

import os
import threading
from pathlib import Path

import swisseph as swe

_state = threading.local()


def configure_ephemeris_path() -> None:
    if getattr(_state, "configured", False):
        return
    path = Path(os.environ.get("EPHEMERIS_PATH", _default_path()))
    if path.exists():
        swe.set_ephe_path(str(path))
    _state.configured = True


def _default_path() -> Path:
    # .../src/vastrochart_compute/compute/ -> .../apps/vastrochart-compute/ephemeris
    return Path(__file__).resolve().parents[3] / "ephemeris"
