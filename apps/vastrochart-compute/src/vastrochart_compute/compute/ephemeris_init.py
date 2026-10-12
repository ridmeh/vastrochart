"""Point pyswisseph at the Swiss Ephemeris data directory.

Must run before any swe.calc_ut/houses_ex/get_ayanamsa_ut call, or
pyswisseph silently falls back to the lower-precision Moshier ephemeris
(apps/vastrochart-compute/ephemeris/NOTE.md).
"""

import os
from pathlib import Path

import swisseph as swe

_configured = False


def configure_ephemeris_path() -> None:
    global _configured
    if _configured:
        return
    path = Path(os.environ.get("EPHEMERIS_PATH", _default_path()))
    if path.exists():
        swe.set_ephe_path(str(path))
    _configured = True


def _default_path() -> Path:
    # .../src/vastrochart_compute/compute/ -> .../apps/vastrochart-compute/ephemeris
    return Path(__file__).resolve().parents[3] / "ephemeris"
