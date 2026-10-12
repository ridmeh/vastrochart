from vastrochart_compute.compute.constants import NAKSHATRAS
from vastrochart_compute.compute.nakshatras import build_nakshatra_distribution, nakshatra_key


def test_all_27_canonical_keys_always_present() -> None:
    distribution = build_nakshatra_distribution({})
    assert len(distribution) == 27
    assert distribution[nakshatra_key("Ashwini")] == []
    assert distribution[nakshatra_key("Revati")] == []


def test_occupants_grouped_by_their_nakshatra() -> None:
    distribution = build_nakshatra_distribution(
        {"Moon": "Rohini", "Mars": "Mrigashira", "Lagna": "Magha"}
    )
    assert distribution["rohini"] == ["Moon"]
    assert distribution["mrigashira"] == ["Mars"]
    assert distribution["magha"] == ["Lagna"]
    assert distribution["ashwini"] == []


def test_multiple_occupants_in_the_same_nakshatra() -> None:
    distribution = build_nakshatra_distribution({"Sun": "Ashlesha", "Jupiter": "Ashlesha"})
    assert distribution["ashlesha"] == ["Sun", "Jupiter"]


def test_key_format_is_lowercase_with_underscores() -> None:
    assert nakshatra_key("Purva Phalguni") == "purva_phalguni"
    assert nakshatra_key("Uttara Bhadrapada") == "uttara_bhadrapada"


def test_every_nakshatra_name_from_constants_has_a_key() -> None:
    distribution = build_nakshatra_distribution({})
    for display_name, _lord in NAKSHATRAS:
        assert nakshatra_key(display_name) in distribution
