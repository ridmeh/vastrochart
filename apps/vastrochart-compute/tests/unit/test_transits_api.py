"""End-to-end HTTP tests for /v1/transits."""

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
    "start_date": "2026-01-01",
    "end_date": "2026-01-10",
    "planets": ["Moon"],
    "aspect_types": ["conjunction"],
}


def test_returns_expected_hit_shape() -> None:
    response = client.post("/v1/transits", json=VALID_BODY)
    assert response.status_code == 200
    hits = response.json()["data"]["hits"]
    assert len(hits) >= 1
    hit = hits[0]
    assert set(hit) == {
        "transit_planet",
        "aspect_type",
        "natal_point",
        "natal_point_longitude",
        "exact_date",
        "orb_entry_date",
        "orb_exit_date",
        "transit_longitude_at_exact",
    }
    assert hit["transit_planet"] == "Moon"
    assert hit["aspect_type"] == "conjunction"


def test_default_planets_and_aspect_types_used_when_omitted() -> None:
    body = {
        "dob": VALID_BODY["dob"],
        "tob": VALID_BODY["tob"],
        "tz_offset": VALID_BODY["tz_offset"],
        "lat": VALID_BODY["lat"],
        "lon": VALID_BODY["lon"],
        "ayanamsa": VALID_BODY["ayanamsa"],
        "start_date": "2026-01-01",
        "end_date": "2026-01-05",
    }
    response = client.post("/v1/transits", json=body)
    assert response.status_code == 200
    hits = response.json()["data"]["hits"]
    assert {hit["aspect_type"] for hit in hits} <= {
        "conjunction",
        "opposition",
        "trine",
        "square",
        "sextile",
    }


def test_end_date_before_start_date_is_rejected() -> None:
    response = client.post(
        "/v1/transits", json={**VALID_BODY, "start_date": "2026-02-01", "end_date": "2026-01-01"}
    )
    assert response.status_code == 422


def test_orb_degrees_out_of_bounds_is_rejected() -> None:
    response = client.post("/v1/transits", json={**VALID_BODY, "orb_degrees": 20.0})
    assert response.status_code == 422


def test_invalid_latitude_returns_mapped_error_code() -> None:
    response = client.post("/v1/transits", json={**VALID_BODY, "lat": 200})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_LATITUDE"


def test_invalid_start_date_returns_mapped_error_code() -> None:
    response = client.post("/v1/transits", json={**VALID_BODY, "start_date": "not-a-date"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE"


def test_unknown_planet_is_rejected() -> None:
    response = client.post("/v1/transits", json={**VALID_BODY, "planets": ["Pluto"]})
    assert response.status_code == 422
