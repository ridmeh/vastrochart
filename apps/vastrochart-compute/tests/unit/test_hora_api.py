"""End-to-end HTTP tests for /v1/hora."""

from fastapi.testclient import TestClient

from vastrochart_compute.main import app

client = TestClient(app)

VALID_BODY = {
    "date": "2026-10-10",
    "lat": 37.6819,
    "lon": -121.7680,
    "tz_offset": "-07:00",
}


def test_valid_request_returns_full_envelope() -> None:
    response = client.post("/v1/hora", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["horas"]) == 24
    assert data["horas"][0]["lord"] == "Saturn"


def test_invalid_date_format_is_rejected() -> None:
    response = client.post("/v1/hora", json={**VALID_BODY, "date": "bad-date"})
    assert response.status_code == 422
