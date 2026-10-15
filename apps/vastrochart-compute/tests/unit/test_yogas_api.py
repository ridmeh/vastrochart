"""End-to-end HTTP tests for /v1/yogas and /v1/yogas/registry.

The present/absent expectations below for VALID_BODY (the same reference
chart used by test_divisional_api.py - dob 1990-01-15, 14:30 +05:30, Delhi,
Lahiri) were hand-derived from that chart's already-known planet signs
(Lagna Taurus; Mars Scorpio; Sun/Rahu both Capricorn; Mercury Sagittarius +
Jupiter Gemini - a mutual sign exchange), not just trusted from the
detector code's own output - same verification approach as ADR-033.
"""

from fastapi.testclient import TestClient

from vastrochart_compute.main import app

client = TestClient(app)

VALID_BODY = {
    "dob": "1990-01-15",
    "tob": "14:30",
    "tz_offset": "+05:30",
    "lat": 28.6139,
    "lon": 77.2090,
    "ayanamsa": "lahiri",
}


def _yogas_by_name(data: dict) -> dict:
    return {yoga["name"]: yoga for yoga in data["yogas"]}


def test_returns_all_eleven_detectors_present_or_absent() -> None:
    response = client.post("/v1/yogas", json=VALID_BODY)
    assert response.status_code == 200
    yogas = _yogas_by_name(response.json()["data"])
    assert len(yogas) == 11

    expected_present = {"Ruchaka Yoga", "Grahan Yoga", "Parivartana Yoga"}
    for name, yoga in yogas.items():
        assert yoga["present"] == (name in expected_present), name


def test_ruchaka_formed_by_mars_own_sign_in_kendra() -> None:
    response = client.post("/v1/yogas", json=VALID_BODY)
    yoga = _yogas_by_name(response.json()["data"])["Ruchaka Yoga"]
    assert yoga["confidence"] == "high"
    assert "Mars" in yoga["formed_by"][0]


def test_parivartana_formed_by_mercury_jupiter_exchange() -> None:
    response = client.post("/v1/yogas", json=VALID_BODY)
    yoga = _yogas_by_name(response.json()["data"])["Parivartana Yoga"]
    assert yoga["present"] is True
    assert "Mercury" in yoga["formed_by"][0] and "Jupiter" in yoga["formed_by"][0]


def test_absent_detector_has_empty_formed_by() -> None:
    response = client.post("/v1/yogas", json=VALID_BODY)
    yoga = _yogas_by_name(response.json()["data"])["Hamsa Yoga"]
    assert yoga["present"] is False
    assert yoga["formed_by"] == []


def test_category_filter_narrows_to_mahapurusha_only() -> None:
    response = client.post("/v1/yogas", json={**VALID_BODY, "category": "mahapurusha"})
    data = response.json()["data"]
    assert len(data["yogas"]) == 5
    assert all(yoga["category"] == "mahapurusha" for yoga in data["yogas"])


def test_category_filter_on_a_not_yet_implemented_category_returns_empty() -> None:
    response = client.post("/v1/yogas", json={**VALID_BODY, "category": "neechabhanga"})
    assert response.status_code == 200
    assert response.json()["data"]["yogas"] == []


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/yogas", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_LATITUDE"


def test_registry_lists_all_eleven_detectors_with_rule_summaries() -> None:
    response = client.get("/v1/yogas/registry")
    assert response.status_code == 200
    detectors = response.json()["data"]["detectors"]
    assert len(detectors) == 11
    for detector in detectors:
        assert detector["confidence"] == "high"
        assert detector["rule_summary"]


def test_registry_category_filter() -> None:
    response = client.get("/v1/yogas/registry", params={"category": "arishta"})
    detectors = response.json()["data"]["detectors"]
    assert {d["name"] for d in detectors} == {"Guru Chandala Yoga", "Grahan Yoga"}


def test_registry_and_compute_endpoints_agree_on_detector_count() -> None:
    compute_response = client.post("/v1/yogas", json=VALID_BODY)
    registry_response = client.get("/v1/yogas/registry")
    assert len(compute_response.json()["data"]["yogas"]) == len(
        registry_response.json()["data"]["detectors"]
    )
