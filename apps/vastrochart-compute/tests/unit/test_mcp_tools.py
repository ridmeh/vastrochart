"""MCP tool tests, using fastmcp's in-memory Client transport (no network -
connects directly to the `mcp` server object). Confirms the MCP layer
produces the same computed values as the equivalent REST call, for the
project's reference chart (dob 1990-01-15, 14:30 +05:30, Delhi, Lahiri).

Plain `asyncio.run()` per call rather than async def test functions +
pytest-asyncio: this subpackage's pyproject.toml sets asyncio_mode = "auto",
but that setting isn't picked up when the whole workspace is run from the
repo root (`uv run pytest`, the command CLAUDE.md documents) - pytest then
resolves config from the workspace root's pyproject.toml instead, which has
no pytest section at all. Wrapping each call keeps these tests correct
regardless of which directory pytest is invoked from.
"""

import asyncio
from typing import Any

from fastmcp import Client

from vastrochart_compute.mcp.server import mcp

REFERENCE_BODY = {
    "dob": "1990-01-15",
    "tob": "14:30",
    "tz_offset": "+05:30",
    "lat": 28.6139,
    "lon": 77.2090,
    "ayanamsa": "lahiri",
}


def _call_tool(name: str, arguments: dict[str, Any], raise_on_error: bool = True) -> Any:
    async def run() -> Any:
        async with Client(mcp) as client:
            return await client.call_tool(name, arguments, raise_on_error=raise_on_error)

    return asyncio.run(run())


def _list_tools() -> Any:
    async def run() -> Any:
        async with Client(mcp) as client:
            return await client.list_tools()

    return asyncio.run(run())


def test_all_nine_tools_are_registered() -> None:
    tools = _list_tools()
    assert {tool.name for tool in tools} == {
        "compute_chart",
        "get_dasha",
        "get_mudda_dasha",
        "get_panchang",
        "get_hora",
        "compute_divisional",
        "detect_yogas",
        "list_yoga_detectors",
        "get_transit_hits",
    }


def test_compute_chart_matches_known_ascendant() -> None:
    result = _call_tool("compute_chart", REFERENCE_BODY)
    assert result.data["ascendant"]["sign"] == "Taurus"
    assert len(result.data["planets"]) == 9
    assert result.data["warnings"] == []


def test_get_dasha_matches_rest_shape() -> None:
    result = _call_tool(
        "get_dasha", {**REFERENCE_BODY, "as_of_date": "2026-01-01", "depth": "sookshma"}
    )
    assert "balance_at_birth" in result.data
    assert len(result.data["mahadasha_sequence"]) == 9
    assert result.data["warnings"] == []


def test_detect_yogas_matches_known_present_set() -> None:
    result = _call_tool("detect_yogas", REFERENCE_BODY)
    yogas = {yoga["name"]: yoga for yoga in result.data["yogas"]}
    assert len(yogas) == 11
    expected_present = {"Ruchaka Yoga", "Grahan Yoga", "Parivartana Yoga"}
    for name, yoga in yogas.items():
        assert yoga["present"] == (name in expected_present), name


def test_list_yoga_detectors_category_filter() -> None:
    result = _call_tool("list_yoga_detectors", {"category": "mahapurusha"})
    assert len(result.data["detectors"]) == 5


def test_compute_divisional_d1_matches_natal_chart() -> None:
    result = _call_tool("compute_divisional", {**REFERENCE_BODY, "varga": "D1"})
    assert result.data["ascendant"]["sign"] == "Taurus"


def test_get_transit_hits_matches_known_conjunction() -> None:
    result = _call_tool(
        "get_transit_hits",
        {
            **REFERENCE_BODY,
            "start_date": "2025-12-28",
            "end_date": "2026-01-05",
            "planets": ["Moon"],
            "aspect_types": ["conjunction"],
        },
    )
    lagna_hits = [hit for hit in result.data["hits"] if hit["natal_point"] == "Lagna"]
    assert len(lagna_hits) == 1
    assert lagna_hits[0]["exact_date"] == "2026-01-01T07:51:54Z"


def test_get_panchang_and_get_hora_need_no_birth_data() -> None:
    body = {"date": "2026-01-01", "lat": 28.6139, "lon": 77.2090, "tz_offset": "+05:30"}
    panchang = _call_tool("get_panchang", body)
    hora = _call_tool("get_hora", body)
    assert "tithi" in panchang.data
    assert len(hora.data["horas"]) == 24


def test_invalid_latitude_is_rejected_by_shared_validation() -> None:
    result = _call_tool("compute_chart", {**REFERENCE_BODY, "lat": 200}, raise_on_error=False)
    assert result.is_error
