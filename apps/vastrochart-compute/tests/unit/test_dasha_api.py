"""End-to-end HTTP tests for /v1/dasha. Synthetic input only."""

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
    "as_of_date": "2026-10-10",
    "depth": "sookshma",
}


def test_valid_request_returns_full_envelope() -> None:
    response = client.post("/v1/dasha", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()

    assert body["endpoint"] == "/v1/dasha"
    assert body["request_id"].startswith("req_")

    data = body["data"]
    assert data["balance_at_birth"]["lord"]
    assert len(data["mahadasha_sequence"]) == 9
    assert set(data["active_at_date"].keys()) == {
        "mahadasha",
        "antardasha",
        "pratyantardasha",
        "sookshma",
    }


def test_depth_md_returns_only_mahadasha() -> None:
    response = client.post("/v1/dasha", json={**VALID_BODY, "depth": "md"})
    assert response.status_code == 200
    assert set(response.json()["data"]["active_at_date"].keys()) == {"mahadasha"}


def test_invalid_as_of_date_format_is_rejected() -> None:
    response = client.post("/v1/dasha", json={**VALID_BODY, "as_of_date": "10-10-2026"})
    assert response.status_code == 422


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/dasha", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_LATITUDE"
