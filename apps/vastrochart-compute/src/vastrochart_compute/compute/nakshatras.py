"""Sign and nakshatra/pada lookup from a sidereal longitude."""

from dataclasses import dataclass

from vastrochart_compute.compute.constants import NAKSHATRA_ARC_DEG, NAKSHATRAS, SIGN_LORDS, SIGNS


@dataclass(frozen=True)
class ZodiacalPosition:
    sign: str
    sign_lord: str
    sign_degree: float
    nakshatra: str
    nakshatra_lord: str
    pada: int


def locate(sidereal_longitude: float) -> ZodiacalPosition:
    """sidereal_longitude: 0-360 decimal degrees."""
    longitude = sidereal_longitude % 360

    sign_index = int(longitude // 30)
    sign = SIGNS[sign_index]
    sign_degree = longitude - sign_index * 30

    nakshatra_index = int(longitude // NAKSHATRA_ARC_DEG) % 27
    nakshatra, nakshatra_lord = NAKSHATRAS[nakshatra_index]
    longitude_in_nakshatra = longitude - nakshatra_index * NAKSHATRA_ARC_DEG
    pada = int(longitude_in_nakshatra // (NAKSHATRA_ARC_DEG / 4)) + 1

    return ZodiacalPosition(
        sign=sign,
        sign_lord=SIGN_LORDS[sign],
        sign_degree=sign_degree,
        nakshatra=nakshatra,
        nakshatra_lord=nakshatra_lord,
        pada=pada,
    )
