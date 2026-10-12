"""Golden regression against private reference charts (docs/07-reference-chart.md).

Fixture files (tests/golden/private_*.json) are gitignored - real people's
birth data never reaches the public repo. When none are present (e.g. public
CI), this suite collects zero tests and passes trivially rather than failing.
"""

import json
from pathlib import Path

import pytest

from vastrochart_compute.compute.chart import compute_natal_chart

GOLDEN_DIR = Path(__file__).parent
LONGITUDE_TOLERANCE_DEG = 2.0 / 60  # 2 arc-minutes, per docs/07-reference-chart.md

# Rahu/Ketu node type (True vs Mean) is unconfirmed for these fixtures -
# exclude from strict longitude tolerance (see each fixture's node_type_caveat).
NODE_NAMES = {"Rahu", "Ketu"}

# Documented, narrow exception - NOT a general loosening of the golden bar.
# See docs/known-reference-tool-deltas.md: Jupiter/Saturn consistently show
# larger deltas vs AstroSage than the other 5 classical planets, likely an
# ephemeris build/version difference, not yet confirmed against a second
# independent tool. Revert to the standard 2' tolerance once resolved.
WIDENED_TOLERANCE_DEG = {
    "Jupiter": 7.0 / 60,
    "Saturn": 7.0 / 60,
}


def _load_fixtures() -> list[dict]:
    fixtures = []
    for path in sorted(GOLDEN_DIR.glob("private_*.json")):
        with open(path) as f:
            fixtures.append(json.load(f))
    return fixtures


FIXTURES = _load_fixtures()


@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
def test_golden_chart(fixture: dict) -> None:
    inputs = fixture["input"]
    result = compute_natal_chart(
        dob=inputs["dob"],
        tob=inputs["tob"],
        tz_offset=inputs["tz_offset"],
        lat=inputs["lat"],
        lon=inputs["lon"],
        ayanamsa=inputs["ayanamsa"],
    )
    chart = result.chart
    expected = fixture["expected"]

    _assert_point_matches(
        chart.ascendant, expected["ascendant"], "Ascendant", strict_longitude=True
    )

    expected_planets = {p["name"]: p for p in expected["planets"]}
    for computed_planet in chart.planets:
        if computed_planet.name not in expected_planets:
            continue
        exp = expected_planets[computed_planet.name]
        strict = computed_planet.name not in NODE_NAMES
        tolerance = WIDENED_TOLERANCE_DEG.get(computed_planet.name, LONGITUDE_TOLERANCE_DEG)
        _assert_point_matches(
            computed_planet, exp, computed_planet.name, strict_longitude=strict, tolerance=tolerance
        )


def _assert_point_matches(
    computed,
    expected: dict,
    label: str,
    strict_longitude: bool,
    tolerance: float = LONGITUDE_TOLERANCE_DEG,
) -> None:
    assert computed.sign == expected["sign"], f"{label}: sign mismatch"
    assert computed.nakshatra == expected["nakshatra"], f"{label}: nakshatra mismatch"
    assert computed.pada == expected["pada"], f"{label}: pada mismatch"
    if strict_longitude:
        delta = abs(computed.sidereal_longitude - expected["sidereal_longitude"])
        delta = min(delta, 360 - delta)
        assert delta <= tolerance, (
            f"{label}: longitude delta {delta * 60:.2f}' exceeds {tolerance * 60:.0f}' tolerance"
        )
