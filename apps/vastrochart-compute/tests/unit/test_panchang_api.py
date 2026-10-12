"""End-to-end HTTP tests for /v1/panchang."""

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
    response = client.post("/v1/panchang", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["vara"]["weekday"] == "Saturday"
    assert len(data["tithi"]) >= 1
    assert len(data["nakshatra"]) >= 1
    assert len(data["nitya_yoga"]) >= 1
    assert len(data["karana"]) >= 1
    assert set(data["muhurta_flags"].keys()) == {"rahu_kaal", "yamaganda", "gulika", "abhijit"}


def test_invalid_date_format_is_rejected() -> None:
    response = client.post("/v1/panchang", json={**VALID_BODY, "date": "10-10-2026"})
    assert response.status_code == 422


def test_invalid_tz_offset_is_rejected() -> None:
    response = client.post("/v1/panchang", json={**VALID_BODY, "tz_offset": "bad"})
    assert response.status_code == 422
