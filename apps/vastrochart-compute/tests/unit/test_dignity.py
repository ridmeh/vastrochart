from vastrochart_compute.compute.dignity import compute_dignity

# Fixed states don't need other_signs context.
EMPTY: dict[str, str] = {}


def test_jupiter_exalted_in_cancer() -> None:
    assert compute_dignity("Jupiter", "Cancer", 5.0, EMPTY) == "exalted"


def test_jupiter_debilitated_in_capricorn() -> None:
    assert compute_dignity("Jupiter", "Capricorn", 5.0, EMPTY) == "debilitated"


def test_sun_own_in_leo() -> None:
    # Leo 0-20 deg is Sun's moolatrikona (narrower, takes priority) - test
    # "own" specifically outside that range, still within Leo.
    assert compute_dignity("Sun", "Leo", 25.0, EMPTY) == "own"


def test_saturn_debilitated_in_aries() -> None:
    assert compute_dignity("Saturn", "Aries", 20.0, EMPTY) == "debilitated"


def test_mercury_moolatrikona_within_own_exaltation_sign() -> None:
    # Virgo is both Mercury's exaltation sign (whole sign) AND its
    # moolatrikona range (16-20 deg) - the narrower range should win.
    assert compute_dignity("Mercury", "Virgo", 18.0, EMPTY) == "moolatrikona"


def test_mercury_exalted_outside_moolatrikona_range() -> None:
    assert compute_dignity("Mercury", "Virgo", 25.0, EMPTY) == "exalted"


def test_rahu_ketu_dignity_is_undefined() -> None:
    assert compute_dignity("Rahu", "Leo", 10.0, EMPTY) is None
    assert compute_dignity("Ketu", "Aquarius", 10.0, EMPTY) is None


def test_panchadha_great_enemy() -> None:
    # Mars in Gemini (lord Mercury); natural Mars->Mercury = enemy.
    # Mercury also in Gemini -> temporal distance 1 -> temporal enemy.
    # enemy + enemy = great_enemy.
    other_signs = {
        "Mercury": "Gemini",
        "Sun": "Aries",
        "Moon": "Aries",
        "Venus": "Aries",
        "Jupiter": "Aries",
        "Saturn": "Aries",
    }
    assert compute_dignity("Mars", "Gemini", 10.0, other_signs) == "great_enemy"


def test_panchadha_great_friend() -> None:
    # Moon in Gemini (lord Mercury); natural Moon->Mercury = friend.
    # Mercury in Leo -> distance Gemini(idx2)->Leo(idx4) = 3 -> temporal friend.
    # friend + friend = great_friend.
    other_signs = {
        "Mercury": "Leo",
        "Sun": "Aries",
        "Mars": "Aries",
        "Venus": "Aries",
        "Jupiter": "Aries",
        "Saturn": "Aries",
    }
    assert compute_dignity("Moon", "Gemini", 10.0, other_signs) == "great_friend"
