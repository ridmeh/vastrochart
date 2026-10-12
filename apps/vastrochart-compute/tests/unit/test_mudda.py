from fractions import Fraction

from vastrochart_compute.compute.dasha import birth_jd_ut_for, compute_balance_at_birth
from vastrochart_compute.compute.mudda import (
    MUDDA_DAYS_PER_UNIT,
    SOLAR_YEAR_DAYS,
    compute_mudda_dasha,
    find_solar_return_jd_ut,
)

# Synthetic, not real birth data.
SYNTHETIC_DOB = "1990-01-15"
SYNTHETIC_TOB = "14:30"
SYNTHETIC_TZ = "+05:30"
SYNTHETIC_MOON_LONGITUDE = 142.216  # matches the synthetic chart used elsewhere in this session
SYNTHETIC_SUN_LONGITUDE = 271.2295


def test_mudda_unit_scale_spans_exactly_one_solar_year() -> None:
    # 120 units x days-per-unit must equal exactly 365.25 days - full-year
    # coverage with no gap (ADR-030), not a 120-real-day sub-slice.
    assert MUDDA_DAYS_PER_UNIT * 120 == SOLAR_YEAR_DAYS


def test_solar_return_converges_to_exact_natal_sun_longitude() -> None:
    import swisseph as swe

    from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path

    configure_ephemeris_path()
    birth_jd = birth_jd_ut_for(SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ)
    sr_jd = find_solar_return_jd_ut(SYNTHETIC_SUN_LONGITUDE, birth_jd, 10, "lahiri")

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    values, _flags = swe.calc_ut(float(sr_jd), swe.SUN, swe.FLG_SIDEREAL)
    assert abs(values[0] - SYNTHETIC_SUN_LONGITUDE) < 1e-6


def test_solar_return_lands_near_birthday_anniversary() -> None:
    birth_jd = birth_jd_ut_for(SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ)
    sr_jd = find_solar_return_jd_ut(SYNTHETIC_SUN_LONGITUDE, birth_jd, 10, "lahiri")
    elapsed_years = float((sr_jd - birth_jd) / SOLAR_YEAR_DAYS)
    assert abs(elapsed_years - 10) < 0.01


def test_mudda_md_lord_matches_natal_balance_lord_at_solar_return_instant() -> None:
    # Right at the solar return itself (as_of_date == solar_return_date),
    # mudda_md must be the SAME lord as the natal balance - the mudda cycle
    # reuses the fixed birth-nakshatra balance every year (ADR-030).
    balance = compute_balance_at_birth(SYNTHETIC_MOON_LONGITUDE)
    result = compute_mudda_dasha(
        moon_sidereal_longitude=SYNTHETIC_MOON_LONGITUDE,
        natal_sun_longitude=SYNTHETIC_SUN_LONGITUDE,
        dob=SYNTHETIC_DOB,
        tob=SYNTHETIC_TOB,
        tz_offset=SYNTHETIC_TZ,
        ayanamsa="lahiri",
        year_offset=5,
        as_of_date=result_solar_return_date(SYNTHETIC_DOB, SYNTHETIC_TOB, SYNTHETIC_TZ, 5),
    )
    assert result.mudda_md.lord == balance.lord


def result_solar_return_date(dob: str, tob: str, tz_offset: str, year_offset: int) -> str:
    birth_jd = birth_jd_ut_for(dob, tob, tz_offset)
    sr_jd = find_solar_return_jd_ut(SYNTHETIC_SUN_LONGITUDE, birth_jd, year_offset, "lahiri")
    from vastrochart_compute.compute.dasha import jd_ut_to_local_string
    from vastrochart_compute.compute.formatting import parse_tz_offset

    tz_hours = Fraction(parse_tz_offset(tz_offset)).limit_denominator(1440)
    return jd_ut_to_local_string(sr_jd, tz_hours, False)


def test_mudda_ad_is_nested_within_mudda_md() -> None:
    result = compute_mudda_dasha(
        moon_sidereal_longitude=SYNTHETIC_MOON_LONGITUDE,
        natal_sun_longitude=SYNTHETIC_SUN_LONGITUDE,
        dob=SYNTHETIC_DOB,
        tob=SYNTHETIC_TOB,
        tz_offset=SYNTHETIC_TZ,
        ayanamsa="lahiri",
        year_offset=20,
        as_of_date="2010-02-01",
    )
    assert result.mudda_md.start <= result.mudda_ad.start
    assert result.mudda_ad.end <= result.mudda_md.end
