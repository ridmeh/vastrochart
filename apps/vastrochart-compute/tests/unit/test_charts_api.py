"""End-to-end HTTP tests for /v1/charts/compute. Deliberately exercises the
real route + exception handlers, not just the compute layer directly - a
real bug (ADR-022 addendum) only surfaced at this level, not in unit tests
that called compute functions in isolation.
"""

from fastapi.testclient import TestClient

from vastrochart_compute.main import app

client = TestClient(app)

# Synthetic input only - never real birth data in a file that reaches the
# public repo.
VALID_BODY = {
    "dob": "1990-01-15",
    "tob": "14:30",
    "tz_offset": "+05:30",
    "lat": 28.6139,
    "lon": 77.2090,
    "ayanamsa": "lahiri",
}


def test_valid_request_returns_full_envelope() -> None:
    response = client.post("/v1/charts/compute", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()

    assert body["api_version"] == "1.0.0"
    assert body["endpoint"] == "/v1/charts/compute"
    assert body["request_id"].startswith("req_")
    assert body["compute_ms"] >= 0
    assert body["ephemeris"]["data_source"] == "DE431"
    assert body["warnings"] == []

    data = body["data"]
    assert data["ascendant"]["sign"]
    assert len(data["planets"]) == 9
    assert data["houses"]["whole_sign"]
    assert data["houses"]["placidus_kp"] is not None


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/charts/compute", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_LATITUDE"
    assert error["field"] == "lat"
    assert error["retry_safe"] is False


def test_malformed_dob_returns_invalid_date() -> None:
    response = client.post("/v1/charts/compute", json={**VALID_BODY, "dob": "15-01-1990"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE"


def test_polar_latitude_degrades_gracefully_not_500() -> None:
    # This is the regression case: used to 500 because compute_ascendant_longitude
    # shared Placidus's failure mode. Must now succeed with a warning.
    response = client.post(
        "/v1/charts/compute",
        json={
            "dob": "2026-06-21",
            "tob": "12:00",
            "tz_offset": "+00:00",
            "lat": 75.0,
            "lon": 10.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["warnings"][0]["code"] == "PLACIDUS_DEGENERATE_AT_LATITUDE"
    assert body["data"]["houses"]["placidus_kp"] is None
    assert body["data"]["houses"]["whole_sign"]  # still populated
    assert body["data"]["ascendant"]["sign"]  # still populated


def test_genuinely_out_of_range_date_returns_mapped_error() -> None:
    response = client.post("/v1/charts/compute", json={**VALID_BODY, "dob": "9999-06-15"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DATE_OUT_OF_EPHEMERIS_RANGE"


def test_moshier_fallback_date_succeeds_with_warning() -> None:
    response = client.post("/v1/charts/compute", json={**VALID_BODY, "dob": "2500-06-15"})
    assert response.status_code == 200
    body = response.json()
    assert body["ephemeris"]["data_source"] == "moshier_analytical"
    assert body["warnings"][0]["code"] == "EPHEMERIS_LOW_PRECISION_FALLBACK"


def test_node_type_mean_differs_from_default_true() -> None:
    default_response = client.post("/v1/charts/compute", json=VALID_BODY)
    mean_response = client.post("/v1/charts/compute", json={**VALID_BODY, "node_type": "mean"})
    default_rahu = next(
        p for p in default_response.json()["data"]["planets"] if p["name"] == "Rahu"
    )
    mean_rahu = next(p for p in mean_response.json()["data"]["planets"] if p["name"] == "Rahu")
    assert default_rahu["sidereal_longitude"] != mean_rahu["sidereal_longitude"]
    assert mean_response.json()["input"]["node_type"] == "mean"
