from vastrochart_compute.compute.boundary_finder import find_angle_crossing


def test_finds_exact_crossing_for_linear_angle() -> None:
    # Synthetic linear angle: angle(jd) = (jd * 10) % 360, speed = 10 deg/day.
    def angle_fn(jd: float) -> tuple[float, float]:
        return (jd * 10) % 360, 10.0

    # Starting at jd=0 (angle=0), target 100 deg should be at jd=10.
    result = find_angle_crossing(angle_fn, jd_guess=5.0, target_angle=100.0)
    assert abs(result - 10.0) < 1e-6


def test_handles_wraparound_near_360() -> None:
    def angle_fn(jd: float) -> tuple[float, float]:
        return (jd * 10 + 355) % 360, 10.0

    # angle(0)=355, target=5 (wraps past 360) should be at jd=1.0.
    result = find_angle_crossing(angle_fn, jd_guess=0.5, target_angle=5.0)
    assert abs(result - 1.0) < 1e-6
