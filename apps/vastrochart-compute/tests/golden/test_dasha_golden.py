"""Dasha balance-at-birth cross-check against the private golden fixtures'
AstroSage-sourced dasha_balance_at_birth_per_source_tool field.

See docs/known-reference-tool-deltas.md: lord matches exactly in all three
charts; day-level deltas (~0-3 days) are consistent with the already-
documented small Moon-longitude noise between the two tools, not a new bug.
Tolerance here (0.02 years, ~7 days) is set generously above that observed
noise floor.
"""

import json
from pathlib import Path

import pytest

from vastrochart_compute.compute.chart import compute_natal_chart
from vastrochart_compute.compute.dasha import compute_balance_at_birth

GOLDEN_DIR = Path(__file__).parent
BALANCE_YEARS_TOLERANCE = 0.02


def _load_fixtures() -> list[dict]:
    fixtures = []
    for path in sorted(GOLDEN_DIR.glob("private_*.json")):
        with open(path) as f:
            entry = json.load(f)
        if "dasha_balance_at_birth_per_source_tool" in entry.get("supplementary_unverified", {}):
            fixtures.append(entry)
    return fixtures


FIXTURES = _load_fixtures()


@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
def test_dasha_balance_matches_source_tool(fixture: dict) -> None:
    inputs = fixture["input"]
    result = compute_natal_chart(
        dob=inputs["dob"],
        tob=inputs["tob"],
        tz_offset=inputs["tz_offset"],
        lat=inputs["lat"],
        lon=inputs["lon"],
        ayanamsa=inputs["ayanamsa"],
    )
    moon = next(p for p in result.chart.planets if p.name == "Moon")
    balance = compute_balance_at_birth(moon.sidereal_longitude)

    expected = fixture["supplementary_unverified"]["dasha_balance_at_birth_per_source_tool"]
    assert balance.lord == expected["lord"]

    expected_years = expected["y"] + expected["m"] / 12 + expected["d"] / 360
    delta = abs(balance.balance_years - expected_years)
    assert delta <= BALANCE_YEARS_TOLERANCE, (
        f"balance_years delta {delta:.4f} exceeds {BALANCE_YEARS_TOLERANCE} tolerance "
        f"(computed={balance.balance_years}, source={expected_years:.4f})"
    )
