from vastrochart_compute.compute.hora import CHALDEAN_ORDER, compute_hora

DATE, LAT, LON, TZ = "2026-10-10", 37.6819, -121.7680, "-07:00"  # Saturday


def test_twenty_four_horas_returned() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert len(result.horas) == 24
    assert [h["index"] for h in result.horas] == list(range(1, 25))


def test_first_hora_lord_matches_weekday_lord() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert result.horas[0]["lord"] == "Saturn"  # Saturday's own lord


def test_chaldean_order_continues_unbroken_across_day_night_boundary() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    lords = [h["lord"] for h in result.horas]
    start_index = CHALDEAN_ORDER.index("Saturn")
    expected = [CHALDEAN_ORDER[(start_index + i) % 7] for i in range(24)]
    assert lords == expected


def test_first_twelve_are_day_last_twelve_are_night() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert all(h["day_or_night"] == "day" for h in result.horas[:12])
    assert all(h["day_or_night"] == "night" for h in result.horas[12:])


def test_horas_are_contiguous() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    for earlier, later in zip(result.horas, result.horas[1:], strict=False):
        assert earlier["end_local"] == later["start_local"]


def test_day_hora_spans_match_sunrise_sunset() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    assert result.horas[0]["start_local"] == result.sunrise_local
    assert result.horas[11]["end_local"] == result.sunset_local
    assert result.horas[12]["start_local"] == result.sunset_local


def test_twelve_day_horas_sum_to_sunrise_sunset_span() -> None:
    import datetime

    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    sunrise = datetime.datetime.fromisoformat(result.sunrise_local)
    sunset = datetime.datetime.fromisoformat(result.sunset_local)
    day_span_minutes = (sunset - sunrise).total_seconds() / 60
    # day_hora_minutes is rounded to 2 decimals before this multiply, so up
    # to 12 x 0.005 = 0.06 min of rounding amplification is expected, not a bug.
    assert abs(result.day_hora_minutes * 12 - day_span_minutes) < 0.1


def test_every_hora_has_a_nature_and_activity_lists() -> None:
    result = compute_hora(date=DATE, lat=LAT, lon=LON, tz_offset=TZ)
    for h in result.horas:
        assert h["nature"] in ("benefic", "malefic", "neutral")
        assert isinstance(h["best_for"], list)
        assert isinstance(h["avoid_for"], list)
