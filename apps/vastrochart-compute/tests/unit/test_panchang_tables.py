from vastrochart_compute.compute.panchang_tables import (
    karana_name_aka_nature,
    nitya_yoga_name_nature,
    tithi_name_lord_nature,
)


def test_tithi_15_is_purnima_not_generic_name() -> None:
    name, lord, nature = tithi_name_lord_nature(15)
    assert name == "Purnima"
    assert lord == "Chandra"
    assert nature == "purna"


def test_tithi_30_is_amavasya_special_cased_shunya() -> None:
    name, lord, nature = tithi_name_lord_nature(30)
    assert name == "Amavasya"
    assert lord == "Pitrs"
    assert nature == "shunya"  # not "purna", despite being position 15 in its paksha


def test_tithi_1_and_16_share_base_name_different_paksha_implied() -> None:
    name1, lord1, _ = tithi_name_lord_nature(1)
    name16, lord16, _ = tithi_name_lord_nature(16)
    assert name1 == name16 == "Pratipada"
    assert lord1 == lord16  # same base lord regardless of paksha


def test_tithi_nature_cycles_every_five() -> None:
    _, _, nature1 = tithi_name_lord_nature(1)
    _, _, nature6 = tithi_name_lord_nature(6)
    _, _, nature11 = tithi_name_lord_nature(11)
    assert nature1 == nature6 == nature11 == "nanda"


def test_nitya_yoga_number_27_is_vaidhriti() -> None:
    name, _nature = nitya_yoga_name_nature(27)
    assert name == "Vaidhriti"


def test_nitya_yoga_wraps_at_28() -> None:
    name1, _ = nitya_yoga_name_nature(1)
    name28, _ = nitya_yoga_name_nature(28)
    assert name1 == name28 == "Vishkumbha"


def test_karana_1_is_fixed_kimstughna() -> None:
    name, aka, _nature = karana_name_aka_nature(1)
    assert name == "Kimstughna"
    assert aka is None


def test_karana_2_is_first_movable_bava() -> None:
    name, _, _ = karana_name_aka_nature(2)
    assert name == "Bava"


def test_karana_vishti_has_bhadra_aka_and_inauspicious_nature() -> None:
    # Vishti is the 7th movable karana: positions 2-57 cycle through 7
    # movables, so karana number 8 = (8-2)%7=6 -> 7th movable = Vishti.
    name, aka, nature = karana_name_aka_nature(8)
    assert name == "Vishti"
    assert aka == "Bhadra"
    assert nature == "inauspicious_classical"


def test_karana_58_59_60_are_the_three_fixed_month_end_karanas() -> None:
    assert karana_name_aka_nature(58)[0] == "Shakuni"
    assert karana_name_aka_nature(59)[0] == "Chatushpada"
    assert karana_name_aka_nature(60)[0] == "Naga"


def test_karana_movable_cycle_repeats_eight_times_between_fixed_ones() -> None:
    # 56 movable-karana slots (2-57) / 7 names = exactly 8 full cycles.
    names = [karana_name_aka_nature(n)[0] for n in range(2, 58)]
    assert len(names) == 56
    assert names[0] == names[7] == names[49] == "Bava"
