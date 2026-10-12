from vastrochart_compute.compute.aspects import compute_aspected_by, compute_graha_drishti


def test_universal_seventh_aspect() -> None:
    # Sun in house 1 aspects house 7 (universal 7th-from-self).
    planet_houses = {"Sun": 1, "Moon": 7}
    drishti = compute_graha_drishti(planet_houses)
    entry = next(d for d in drishti if d["from"] == "Sun" and d["to"] == "Moon")
    assert entry["aspect_type"] == "7th"
    assert entry["strength"] == "full"


def test_mutual_seventh_aspect_is_always_symmetric() -> None:
    # Classical fact: two planets exactly opposite each other (7th from each
    # other) always mutually aspect via the universal 7th rule.
    planet_houses = {"Mercury": 3, "Venus": 9}
    drishti = compute_graha_drishti(planet_houses)
    pairs = {(d["from"], d["to"]) for d in drishti}
    assert ("Mercury", "Venus") in pairs
    assert ("Venus", "Mercury") in pairs


def test_mars_special_aspects_4th_and_8th() -> None:
    # Mars in house 1 also aspects houses 4 and 8 (not just 7).
    planet_houses = {"Mars": 1, "Sun": 4, "Moon": 7, "Venus": 8}
    drishti = compute_graha_drishti(planet_houses)
    mars_targets = {d["to"]: d["aspect_type"] for d in drishti if d["from"] == "Mars"}
    assert mars_targets == {"Sun": "4th_8th", "Moon": "7th", "Venus": "4th_8th"}


def test_lagna_is_a_valid_aspect_target() -> None:
    planet_houses = {"Saturn": 7}
    drishti = compute_graha_drishti(planet_houses, lagna_house=1)
    assert {"from": "Saturn", "to": "Lagna", "aspect_type": "7th", "strength": "full"} in drishti


def test_planet_does_not_aspect_itself() -> None:
    planet_houses = {"Jupiter": 1}
    drishti = compute_graha_drishti(planet_houses)
    assert all(d["from"] != d["to"] for d in drishti)


def test_aspected_by_is_independent_of_occupancy() -> None:
    # An empty house can still be aspected - aspected_by doesn't require a target there.
    planet_houses = {"Saturn": 1}
    aspected_by = compute_aspected_by(planet_houses)
    assert aspected_by[7] == ["Saturn"]
    assert aspected_by[3] == ["Saturn"]  # Saturn's 3rd-from-self special aspect
    assert aspected_by[10] == ["Saturn"]  # Saturn's 10th-from-self special aspect
    assert aspected_by[5] == []


def test_aspected_by_and_graha_drishti_share_the_same_rule() -> None:
    # Jupiter in house 2's 9th-from-self special aspect lands on house 10
    # (counting inclusively: 2=1st,3=2nd,...,10=9th). If Saturn occupies
    # house 10, both views must agree.
    planet_houses = {"Jupiter": 2, "Saturn": 10}
    drishti = compute_graha_drishti(planet_houses)
    aspected_by = compute_aspected_by(planet_houses)
    assert any(d["from"] == "Jupiter" and d["to"] == "Saturn" for d in drishti)
    assert "Jupiter" in aspected_by[10]
