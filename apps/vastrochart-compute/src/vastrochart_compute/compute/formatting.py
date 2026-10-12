"""Degree <-> DMS formatting. Keep arithmetic in whole arc-seconds to avoid
float drift across sandhi (sign/nakshatra boundary) comparisons."""


def to_dms_string(decimal_degrees: float) -> str:
    """Format a decimal-degree value (0-360 or 0-30) as DMS, e.g. '23°34\\'17\"'."""
    total_seconds = round(decimal_degrees * 3600)
    degrees, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{degrees:02d}°{minutes:02d}'{seconds:02d}\""


def parse_tz_offset(tz_offset: str) -> float:
    """Parse a signed offset string like '+05:30' or '-07:00' into decimal hours."""
    sign = -1.0 if tz_offset.startswith("-") else 1.0
    hours_str, minutes_str = tz_offset.lstrip("+-").split(":")
    return sign * (int(hours_str) + int(minutes_str) / 60)
