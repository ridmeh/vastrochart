"""Divisional charts (vargas) - D1 through D60.

Pure transform of D1 (natal) sidereal longitudes - no new astronomical
computation needed beyond what the D1 chart already has. K.P. sub-lord
theory is D1-only (docs/02-domain-knowledge.md) - never computed for
vargas. Only Whole-Sign houses are meaningful for a varga; Placidus/K.P.
houses are not computed here.

Within-sign degree convention: a planet's position within its original
nakshatra-division "part" is proportionally re-mapped to fill the full 30
deg of the resulting varga sign (not simply copying the original degree
across) - the standard practice in Vedic software.

CONFIDENCE NOTE (be honest, don't hallucinate precision): D1/D9/D10/D12
starting-sign rules are well-established and consistently cited across
Jyotish sources - good confidence. D16/D20/D24/D30/D60 have real textual
variation across sources for exact starting-sign rules and (for D30) exact
degree boundaries - moderate-to-lower confidence, flagged per-varga below.
Cross-verify against a reference before treating as authoritative, same
spirit as compute/panchang_tables.py (ADR-031).
"""

VARGA_NAMES = {
    "D1": "Rashi",
    "D9": "Navamsha",
    "D10": "Dashamsha",
    "D12": "Dwadashamsha",
    "D16": "Shodashamsha",
    "D20": "Vimshamsha",
    "D24": "Chaturvimshamsha",
    "D30": "Trimshamsha",
    "D60": "Shashtiamsha",
}

_MOVABLE = {0, 3, 6, 9}  # Aries, Cancer, Libra, Capricorn (0-indexed)
_FIXED = {1, 4, 7, 10}  # Taurus, Leo, Scorpio, Aquarius
_DUAL = {2, 5, 8, 11}  # Gemini, Virgo, Sagittarius, Pisces

VARGA_DIVISIONS = {"D9": 9, "D10": 10, "D12": 12, "D16": 16, "D20": 20, "D24": 24, "D60": 60}


def _d9_start(sign_index: int) -> int:
    """Good confidence - the standard, consistently-cited navamsha rule."""
    if sign_index in _MOVABLE:
        return sign_index
    if sign_index in _FIXED:
        return (sign_index + 8) % 12  # 9th from it
    return (sign_index + 4) % 12  # dual: 5th from it


def _d10_start(sign_index: int) -> int:
    """Good confidence. sign_index % 2 == 0 means Aries/Gemini/... (classical
    "odd" signs, 1-indexed) - same sign; "even" signs - 9th from it."""
    if sign_index % 2 == 0:
        return sign_index
    return (sign_index + 8) % 12


def _d12_start(sign_index: int) -> int:
    """Good confidence - always starts from the same sign."""
    return sign_index


def _d16_start(sign_index: int) -> int:
    """Moderate confidence - some textual variation in exact starting signs."""
    if sign_index in _MOVABLE:
        return 0  # Aries
    if sign_index in _FIXED:
        return 4  # Leo
    return 8  # Sagittarius


def _d20_start(sign_index: int) -> int:
    """Moderate confidence - some textual variation."""
    if sign_index in _MOVABLE:
        return 0  # Aries
    if sign_index in _FIXED:
        return 8  # Sagittarius
    return 4  # Leo


def _d24_start(sign_index: int) -> int:
    """Moderate confidence. "Odd" signs (1-indexed) -> Leo; "even" -> Cancer."""
    if sign_index % 2 == 0:
        return 4  # Leo
    return 3  # Cancer


def _d60_start(sign_index: int) -> int:
    """LOWER confidence - using the simplest "always same sign" rule; some
    sources describe direction (forward/reverse) varying by odd/even sign,
    which is not implemented here."""
    return sign_index


_VARGA_START_FN = {
    "D9": _d9_start,
    "D10": _d10_start,
    "D12": _d12_start,
    "D16": _d16_start,
    "D20": _d20_start,
    "D24": _d24_start,
    "D60": _d60_start,
}

# D30 (Trimshamsha): unequal divisions assigned to 5 planets, differs for
# odd vs even signs - moderate confidence, some textual variation in exact
# degree boundaries across sources. (start_deg, end_deg, planet, varga_sign_index)
_D30_ODD_RANGES = [
    (0.0, 5.0, "Mars", 0),  # Aries
    (5.0, 10.0, "Saturn", 10),  # Aquarius
    (10.0, 18.0, "Jupiter", 8),  # Sagittarius
    (18.0, 25.0, "Mercury", 2),  # Gemini
    (25.0, 30.0, "Venus", 6),  # Libra
]
_D30_EVEN_RANGES = [
    (0.0, 5.0, "Venus", 1),  # Taurus
    (5.0, 12.0, "Mercury", 5),  # Virgo
    (12.0, 20.0, "Jupiter", 11),  # Pisces
    (20.0, 25.0, "Saturn", 9),  # Capricorn
    (25.0, 30.0, "Mars", 7),  # Scorpio
]


def _d30_range_for(sign_index: int, sign_degree: float) -> tuple[float, float, int]:
    ranges = _D30_ODD_RANGES if sign_index % 2 == 0 else _D30_EVEN_RANGES
    for start, end, _planet, varga_sign in ranges:
        if start <= sign_degree < end:
            return start, end, varga_sign
    start, end, _planet, varga_sign = ranges[-1]  # sign_degree == 30.0 edge case
    return start, end, varga_sign


def varga_longitude(sidereal_longitude: float, varga: str) -> float:
    """Re-maps a D1 sidereal longitude into the given varga, proportionally
    filling the resulting sign's 30 degrees from the planet's position
    within its original division "part"."""
    longitude = sidereal_longitude % 360
    if varga == "D1":
        return longitude

    sign_index = int(longitude // 30)
    sign_degree = longitude - sign_index * 30

    if varga == "D30":
        start, end, varga_sign = _d30_range_for(sign_index, sign_degree)
        fraction = (sign_degree - start) / (end - start)
        return (varga_sign + fraction) * 30 % 360

    divisions = VARGA_DIVISIONS[varga]
    part_size = 30 / divisions
    part_number = min(int(sign_degree // part_size), divisions - 1)
    remainder = sign_degree - part_number * part_size
    fraction = remainder / part_size
    varga_sign = (_VARGA_START_FN[varga](sign_index) + part_number) % 12
    return (varga_sign + fraction) * 30 % 360
