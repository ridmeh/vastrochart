"""End-to-end HTTP tests for /v1/mudda-dasha. Synthetic input only."""

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
    "year_offset": 36,
}


def test_valid_request_returns_full_envelope() -> None:
    response = client.post("/v1/mudda-dasha", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()

    assert body["endpoint"] == "/v1/mudda-dasha"
    data = body["data"]
    assert data["solar_return_date"]
    assert data["mudda_md"]["lord"]
    assert data["mudda_ad"]["lord"]


def test_as_of_date_defaults_to_today_when_omitted() -> None:
    response = client.post("/v1/mudda-dasha", json=VALID_BODY)
    assert response.status_code == 200
    # Resolved as_of_date should be echoed in input, not left null.
    assert response.json()["input"]["as_of_date"] is not None


def test_explicit_as_of_date_is_honored() -> None:
    response = client.post("/v1/mudda-dasha", json={**VALID_BODY, "as_of_date": "2026-03-01"})
    assert response.status_code == 200
    assert response.json()["input"]["as_of_date"] == "2026-03-01"


def test_invalid_year_offset_is_rejected() -> None:
    response = client.post("/v1/mudda-dasha", json={**VALID_BODY, "year_offset": -1})
    assert response.status_code == 422


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/mudda-dasha", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_LATITUDE"
