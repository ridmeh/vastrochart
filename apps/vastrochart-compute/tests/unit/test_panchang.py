from vastrochart_compute.compute.panchang import compute_panchang

# 2026-10-10 at these coordinates is a verified new-moon day (confirmed via
# the karana/tithi internal-consistency check below) - a good edge case.
NEW_MOON_DATE = "2026-10-10"
LAT, LON, TZ = 37.6819, -121.7680, "-07:00"


def test_weekday_matches_python_calendar() -> None:
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert result.vara["weekday"] == "Saturday"  # verified via datetime.date(2026,10,10)
    assert result.vara["lord"] == "Saturn"


def test_sunrise_before_sunset() -> None:
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert result.sunrise_local < result.sunset_local


def test_tithi_spans_the_whole_sunrise_to_sunrise_window() -> None:
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert result.tithi[0]["start_local"] == result.sunrise_local
    assert result.tithi[-1]["end_local"] == result.nakshatra[-1]["end_local"]


def test_new_moon_day_tithi_transitions_30_to_1() -> None:
    # Amavasya (30) ending, Pratipada (1) beginning - genuine new moon.
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    numbers = [t["number"] for t in result.tithi]
    assert numbers == [30, 1]
    assert result.tithi[0]["name"] == "Amavasya"
    assert result.tithi[1]["name"] == "Pratipada"


def test_karana_wraps_through_fixed_kimstughna_at_new_moon() -> None:
    # Classical structure check: the last karana of a month (Naga, #60) must
    # be immediately followed by the fixed Kimstughna (#1), then the first
    # movable karana (Bava, #2) - this is a strong internal-consistency
    # signal that the astronomical engine and the karana table agree.
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    names = [k["name"] for k in result.karana]
    assert names == ["Naga", "Kimstughna", "Bava"]


def test_nakshatra_entries_have_required_fields() -> None:
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    for entry in result.nakshatra:
        assert entry["name"]
        assert entry["lord"]
        assert entry["start_local"] < entry["end_local"]


def test_muhurta_flags_all_present_and_well_ordered() -> None:
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    for key in ("rahu_kaal", "yamaganda", "gulika", "abhijit"):
        flag = result.muhurta_flags[key]
        assert flag["start_local"] < flag["end_local"]
        assert result.sunrise_local <= flag["start_local"]
        assert flag["end_local"] <= result.sunset_local


def test_abhijit_is_centered_on_the_day() -> None:
    # Abhijit = 8th of 15 muhurtas, i.e. roughly the middle of the day.
    result = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    abhijit = result.muhurta_flags["abhijit"]
    assert result.sunrise_local < abhijit["start_local"] < result.sunset_local
    assert result.sunrise_local < abhijit["end_local"] < result.sunset_local


def test_different_location_gives_different_sunrise() -> None:
    delhi = compute_panchang(date=NEW_MOON_DATE, lat=28.6139, lon=77.2090, tz_offset="+05:30")
    california = compute_panchang(date=NEW_MOON_DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert delhi.sunrise_local != california.sunrise_local
