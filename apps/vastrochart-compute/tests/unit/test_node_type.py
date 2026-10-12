"""node_type parameter (ADR-027) - True vs Mean Rahu/Ketu."""

from vastrochart_compute.compute.chart import compute_natal_chart
from vastrochart_compute.compute.planets import compute_raw_planet_positions
from vastrochart_compute.compute.time_utils import to_julian_day_ut


def test_true_and_mean_node_give_different_rahu_longitude() -> None:
    jd = to_julian_day_ut("1990-01-15", "14:30", "+05:30")
    true_positions = compute_raw_planet_positions(jd, "lahiri", node_type="true")
    mean_positions = compute_raw_planet_positions(jd, "lahiri", node_type="mean")

    true_rahu = next(p for p in true_positions if p.name == "Rahu")
    mean_rahu = next(p for p in mean_positions if p.name == "Rahu")

    # They should differ meaningfully (not be coincidentally equal) - True
    # vs Mean Node commonly differ by up to ~1.5 deg.
    assert abs(true_rahu.sidereal_longitude - mean_rahu.sidereal_longitude) > 0.01


def test_ketu_always_mirrors_rahu_for_either_node_type() -> None:
    jd = to_julian_day_ut("1990-01-15", "14:30", "+05:30")
    for node_type in ["true", "mean"]:
        positions = compute_raw_planet_positions(jd, "lahiri", node_type=node_type)
        rahu = next(p for p in positions if p.name == "Rahu")
        ketu = next(p for p in positions if p.name == "Ketu")
        assert abs((rahu.sidereal_longitude + 180) % 360 - ketu.sidereal_longitude) < 1e-9
        assert ketu.retrograde == rahu.retrograde


def test_node_type_defaults_to_true_and_is_accepted_end_to_end() -> None:
    default_result = compute_natal_chart(
        dob="1990-01-15", tob="14:30", tz_offset="+05:30", lat=28.6139, lon=77.2090
    )
    explicit_true = compute_natal_chart(
        dob="1990-01-15",
        tob="14:30",
        tz_offset="+05:30",
        lat=28.6139,
        lon=77.2090,
        node_type="true",
    )
    rahu_default = next(p for p in default_result.chart.planets if p.name == "Rahu")
    rahu_explicit = next(p for p in explicit_true.chart.planets if p.name == "Rahu")
    assert rahu_default.sidereal_longitude == rahu_explicit.sidereal_longitude
