"""Planetary dignity: exalted/moolatrikona/own/debilitated, else Panchadha
Maitri (ADR-025) - Naisargika (natural) + Tatkalika (temporary) friendship,
compounded per the classical table:

               temporal friend   temporal enemy
natural friend   great_friend      neutral
natural neutral  friend            enemy
natural enemy    neutral           great_enemy

Dignity is undefined (None) for Rahu/Ketu - classical texts disagree enough
on nodal natural friendship that asserting a table here would be guessing,
and AstroSage itself leaves this blank for the nodes (see golden data).
"""

from vastrochart_compute.compute.constants import (
    CLASSICAL_PLANETS,
    DEBILITATION,
    EXALTATION,
    MOOLATRIKONA,
    NAISARGIKA_ENEMIES,
    NAISARGIKA_FRIENDS,
    OWN_SIGNS,
    SIGN_LORDS,
    SIGNS,
)

_TEMPORAL_FRIEND_DISTANCES = {2, 3, 4, 10, 11, 12}

_COMPOUND_TABLE = {
    ("friend", "friend"): "great_friend",
    ("friend", "enemy"): "neutral",
    ("neutral", "friend"): "friend",
    ("neutral", "enemy"): "enemy",
    ("enemy", "friend"): "neutral",
    ("enemy", "enemy"): "great_enemy",
}


def _fixed_state(planet: str, sign: str, sign_degree: float) -> str | None:
    # Moolatrikona checked first: it's a narrow degree range that can fall
    # inside the broader exaltation sign (e.g. Mercury: exalted all of Virgo,
    # moolatrikona only Virgo 16-20 deg) - the narrower, more specific
    # classification wins.
    if planet in MOOLATRIKONA:
        mool_sign, mool_start, mool_end = MOOLATRIKONA[planet]
        if sign == mool_sign and mool_start <= sign_degree <= mool_end:
            return "moolatrikona"
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"
    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return "own"
    if planet in DEBILITATION and DEBILITATION[planet][0] == sign:
        return "debilitated"
    return None


def _natural_relation(planet: str, other: str) -> str:
    if other in NAISARGIKA_FRIENDS[planet]:
        return "friend"
    if other in NAISARGIKA_ENEMIES[planet]:
        return "enemy"
    return "neutral"


def _temporal_relation(sign_a: str, sign_b: str) -> str:
    distance = (SIGNS.index(sign_b) - SIGNS.index(sign_a)) % 12 + 1
    return "friend" if distance in _TEMPORAL_FRIEND_DISTANCES else "enemy"


def compute_dignity(
    planet: str, sign: str, sign_degree: float, other_signs: dict[str, str]
) -> str | None:
    """other_signs: {planet_name: sign} for every other classical planet currently placed."""
    if planet not in CLASSICAL_PLANETS:
        return None

    fixed = _fixed_state(planet, sign, sign_degree)
    if fixed is not None:
        return fixed

    lord = SIGN_LORDS[sign]
    if lord not in other_signs:
        return (
            "neutral"  # lord's own position unknown (shouldn't happen for the 7 classical planets)
        )

    natural = _natural_relation(planet, lord)
    temporal = _temporal_relation(sign, other_signs[lord])
    return _COMPOUND_TABLE[(natural, temporal)]
