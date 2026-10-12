from vastrochart_compute.compute.nakshatras import locate


def test_zero_degrees_aries_is_ashwini_pada_1() -> None:
    pos = locate(0.0)
    assert pos.sign == "Aries"
    assert pos.nakshatra == "Ashwini"
    assert pos.nakshatra_lord == "Ketu"
    assert pos.pada == 1


def test_just_before_360_is_revati_pada_4() -> None:
    pos = locate(359.999)
    assert pos.sign == "Pisces"
    assert pos.nakshatra == "Revati"
    assert pos.pada == 4


def test_nakshatra_sandhi_boundary() -> None:
    # Ashwini ends / Bharani begins at 13 deg 20 min exactly.
    just_before = locate(13 + 20 / 60 - 0.001)
    at_boundary = locate(13 + 20 / 60)
    assert just_before.nakshatra == "Ashwini"
    assert at_boundary.nakshatra == "Bharani"


def test_sign_rollover_at_30_degrees() -> None:
    assert locate(29.999).sign == "Aries"
    assert locate(30.0).sign == "Taurus"


def test_longitude_wraps_past_360() -> None:
    assert locate(360.0).sign == "Aries"
    assert locate(725.0).sign == locate(5.0).sign


def test_moon_natal_nakshatra_example() -> None:
    # Cancer 24 deg 35' 32" = Ashlesha pada 3, a fixed classical fact
    # independent of any individual's birth data.
    pos = locate(90 + 24 + 35 / 60 + 32 / 3600)
    assert pos.sign == "Cancer"
    assert pos.nakshatra == "Ashlesha"
    assert pos.pada == 3
