"""Unit tests for the 11 high-confidence yoga detectors (compute/yogas.py),
built on hand-constructed YogaContext objects rather than real ephemeris -
each check is sign-level only, so exact degrees don't matter here.
"""

from vastrochart_compute.compute.yogas import (
    REGISTRY,
    PlanetPlacement,
    YogaContext,
    registry_entries,
)

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def _placement(sign: str) -> PlanetPlacement:
    return PlanetPlacement(sidereal_longitude=SIGNS.index(sign) * 30 + 15.0, sign=sign)


def _ctx(lagna_sign: str, **planet_signs: str) -> YogaContext:
    lagna_longitude = SIGNS.index(lagna_sign) * 30 + 15.0
    planets = {name: _placement(sign) for name, sign in planet_signs.items()}
    return YogaContext(lagna_longitude=lagna_longitude, planets=planets)


def _detector(name: str):
    return next(detector for detector in REGISTRY if detector.name == name)


def test_registry_has_exactly_eleven_detectors() -> None:
    assert len(REGISTRY) == 11


def test_registry_entries_filters_by_category() -> None:
    assert len(registry_entries("mahapurusha")) == 5
    assert len(registry_entries("chandra_based")) == 2
    assert len(registry_entries("surya_based")) == 1
    assert len(registry_entries("arishta")) == 2
    assert len(registry_entries("parivartana")) == 1
    assert len(registry_entries("all")) == 11


def test_ruchaka_absent_mars_own_sign_but_not_kendra() -> None:
    ctx = _ctx("Aries", Mars="Scorpio")  # Aries(0) -> Scorpio(7): house 8, not a kendra.
    assert _detector("Ruchaka Yoga").detect(ctx) == []


def test_ruchaka_present_mars_own_sign_and_kendra() -> None:
    ctx = _ctx("Taurus", Mars="Scorpio")  # Taurus(idx1) -> Scorpio(idx7): house 7, kendra.
    formed_by = _detector("Ruchaka Yoga").detect(ctx)
    assert len(formed_by) == 1
    assert "Mars is own in Scorpio" in formed_by[0]


def test_ruchaka_absent_when_mars_undignified() -> None:
    ctx = _ctx("Taurus", Mars="Gemini")  # not own, not exalted
    assert _detector("Ruchaka Yoga").detect(ctx) == []


def test_shasha_present_saturn_exalted_in_kendra() -> None:
    ctx = _ctx("Capricorn", Saturn="Libra")  # Capricorn(9)->Libra(6): house 10, kendra.
    formed_by = _detector("Shasha Yoga").detect(ctx)
    assert len(formed_by) == 1
    assert "exalted" in formed_by[0]


def test_gaja_kesari_present_jupiter_kendra_from_moon() -> None:
    ctx = _ctx("Aries", Moon="Cancer", Jupiter="Capricorn")  # Cancer(3)->Capricorn(9): house 7
    formed_by = _detector("Gaja Kesari Yoga").detect(ctx)
    assert len(formed_by) == 1


def test_gaja_kesari_absent_jupiter_not_kendra_from_moon() -> None:
    ctx = _ctx("Aries", Moon="Cancer", Jupiter="Leo")  # Cancer(3)->Leo(4): house 2
    assert _detector("Gaja Kesari Yoga").detect(ctx) == []


def test_chandra_mangala_present_same_sign() -> None:
    ctx = _ctx("Aries", Moon="Leo", Mars="Leo")
    assert len(_detector("Chandra Mangala Yoga").detect(ctx)) == 1


def test_chandra_mangala_absent_different_signs() -> None:
    ctx = _ctx("Aries", Moon="Leo", Mars="Virgo")
    assert _detector("Chandra Mangala Yoga").detect(ctx) == []


def test_budhaditya_present_same_sign() -> None:
    ctx = _ctx("Aries", Sun="Capricorn", Mercury="Capricorn")
    assert len(_detector("Budhaditya Yoga").detect(ctx)) == 1


def test_budhaditya_notes_flag_combust_caveat() -> None:
    detector = _detector("Budhaditya Yoga")
    assert detector.notes is not None
    assert "combust" in detector.notes


def test_guru_chandala_present_jupiter_with_either_node() -> None:
    present_rahu = _ctx("Aries", Jupiter="Gemini", Rahu="Gemini", Ketu="Sagittarius")
    present_ketu = _ctx("Aries", Jupiter="Gemini", Rahu="Sagittarius", Ketu="Gemini")
    assert len(_detector("Guru Chandala Yoga").detect(present_rahu)) == 1
    assert len(_detector("Guru Chandala Yoga").detect(present_ketu)) == 1


def test_guru_chandala_absent_no_conjunction() -> None:
    ctx = _ctx("Aries", Jupiter="Gemini", Rahu="Virgo", Ketu="Pisces")
    assert _detector("Guru Chandala Yoga").detect(ctx) == []


def test_grahan_present_sun_conjunct_rahu() -> None:
    ctx = _ctx("Aries", Sun="Capricorn", Moon="Leo", Rahu="Capricorn", Ketu="Cancer")
    formed_by = _detector("Grahan Yoga").detect(ctx)
    assert formed_by == ["Sun and Rahu are both in Capricorn"]


def test_grahan_absent_no_luminary_node_conjunction() -> None:
    ctx = _ctx("Aries", Sun="Capricorn", Moon="Leo", Rahu="Gemini", Ketu="Sagittarius")
    assert _detector("Grahan Yoga").detect(ctx) == []


def test_parivartana_present_on_mutual_sign_exchange() -> None:
    # Mercury in Sagittarius (ruled by Jupiter), Jupiter in Gemini (ruled by
    # Mercury) - the other five classical planets placed in their own signs
    # so they contribute no exchange of their own.
    ctx = _ctx(
        "Aries",
        Sun="Leo",
        Moon="Cancer",
        Mars="Aries",
        Mercury="Sagittarius",
        Jupiter="Gemini",
        Venus="Taurus",
        Saturn="Capricorn",
    )
    formed_by = _detector("Parivartana Yoga").detect(ctx)
    assert len(formed_by) == 1
    assert "Mercury" in formed_by[0] and "Jupiter" in formed_by[0]


def test_parivartana_absent_when_every_planet_in_own_sign() -> None:
    ctx = _ctx(
        "Aries",
        Sun="Leo",
        Moon="Cancer",
        Mars="Aries",
        Mercury="Gemini",
        Jupiter="Sagittarius",
        Venus="Taurus",
        Saturn="Capricorn",
    )
    assert _detector("Parivartana Yoga").detect(ctx) == []
