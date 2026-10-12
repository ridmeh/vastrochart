"""End-to-end HTTP tests for /v1/divisional/{varga}."""

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


def test_d1_matches_natal_chart() -> None:
    response = client.post("/v1/divisional/D1", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["varga"] == "D1"
    assert data["varga_name"] == "Rashi"
    assert data["ascendant"]["sign"] == "Taurus"


def test_d9_returns_navamsha() -> None:
    response = client.post("/v1/divisional/D9", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["varga"] == "D9"
    assert data["varga_name"] == "Navamsha"
    assert len(data["planets"]) == 9


def test_all_nine_committed_vargas_work() -> None:
    for varga in ["D1", "D9", "D10", "D12", "D16", "D20", "D24", "D30", "D60"]:
        response = client.post(f"/v1/divisional/{varga}", json=VALID_BODY)
        assert response.status_code == 200, f"{varga} failed"
        assert response.json()["data"]["varga"] == varga


def test_unsupported_varga_returns_mapped_error() -> None:
    response = client.post("/v1/divisional/D7", json=VALID_BODY)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_VARGA"


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/divisional/D9", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_LATITUDE"
