"""Classical yoga detection - the 11 high-confidence detectors reviewed in
docs/yoga-detectors-ledger.md. Medium/low-confidence detectors are
deliberately not implemented yet.

Confidence and notes are properties of the detector itself, not of any one
chart (docs/05-decisions.md ADR-034) - reclassifying a detector later is a
data change, not a schema change, and both `compute_yogas` and
`registry_entries` read the same REGISTRY so they can never drift apart.
"""

from collections.abc import Callable
from dataclasses import dataclass

from vastrochart_compute.compute.constants import (
    CLASSICAL_PLANETS,
    EXALTATION,
    OWN_SIGNS,
    SIGN_LORDS,
)
from vastrochart_compute.compute.ephemeris_init import configure_ephemeris_path
from vastrochart_compute.compute.houses import sign_of, whole_sign_house
from vastrochart_compute.compute.planets import (
    compute_ascendant_longitude,
    compute_raw_planet_positions,
)
from vastrochart_compute.compute.time_utils import to_julian_day_ut

_KENDRAS = {1, 4, 7, 10}


@dataclass(frozen=True)
class PlanetPlacement:
    sidereal_longitude: float
    sign: str


@dataclass(frozen=True)
class YogaContext:
    lagna_longitude: float
    planets: dict[str, PlanetPlacement]  # Sun..Ketu, keyed by name


@dataclass(frozen=True)
class YogaResult:
    name: str
    sanskrit: str
    category: str
    present: bool
    confidence: str
    notes: str | None
    formed_by: list[str]


DetectorFn = Callable[[YogaContext], list[str]]


@dataclass(frozen=True)
class YogaDetector:
    name: str
    sanskrit: str
    category: str
    confidence: str
    notes: str | None
    rule_summary: str
    detect: DetectorFn


def _own_or_exalted(planet: str, sign: str) -> str | None:
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"
    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return "own"
    return None


def _mahapurusha(planet: str) -> DetectorFn:
    def detect(ctx: YogaContext) -> list[str]:
        placement = ctx.planets[planet]
        dignity = _own_or_exalted(planet, placement.sign)
        if dignity is None:
            return []
        house = whole_sign_house(placement.sidereal_longitude, ctx.lagna_longitude)
        if house not in _KENDRAS:
            return []
        return [f"{planet} is {dignity} in {placement.sign}, house {house} from Lagna"]

    return detect


def _kendra_from(reference: str, target: str) -> DetectorFn:
    def detect(ctx: YogaContext) -> list[str]:
        ref_longitude = ctx.planets[reference].sidereal_longitude
        target_placement = ctx.planets[target]
        house = whole_sign_house(target_placement.sidereal_longitude, ref_longitude)
        if house not in _KENDRAS:
            return []
        return [f"{target} is in house {house} from {reference}"]

    return detect


def _any_conjunct_any(group_a: tuple[str, ...], group_b: tuple[str, ...]) -> DetectorFn:
    def detect(ctx: YogaContext) -> list[str]:
        formed_by = []
        seen: set[tuple[str, str]] = set()
        for a in group_a:
            for b in group_b:
                if a == b or (a, b) in seen or (b, a) in seen:
                    continue
                seen.add((a, b))
                sign_a = ctx.planets[a].sign
                if sign_a == ctx.planets[b].sign:
                    formed_by.append(f"{a} and {b} are both in {sign_a}")
        return formed_by

    return detect


def _parivartana(ctx: YogaContext) -> list[str]:
    """Detects the sign-exchange mechanic only (high confidence). Classifying
    a given exchange as auspicious/inauspicious by which houses are involved
    is a separate, medium-confidence step not implemented here."""
    formed_by = []
    checked: set[frozenset[str]] = set()
    for planet in CLASSICAL_PLANETS:
        sign = ctx.planets[planet].sign
        lord = SIGN_LORDS[sign]
        if lord == planet:
            continue
        pair = frozenset((planet, lord))
        if pair in checked:
            continue
        checked.add(pair)
        lord_sign = ctx.planets[lord].sign
        if SIGN_LORDS[lord_sign] == planet:
            formed_by.append(
                f"{planet} occupies {lord}'s sign ({sign}) and {lord} occupies "
                f"{planet}'s sign ({lord_sign})"
            )
    return formed_by


REGISTRY: list[YogaDetector] = [
    YogaDetector(
        name="Ruchaka Yoga",
        sanskrit="रुचक",
        category="mahapurusha",
        confidence="high",
        notes=None,
        rule_summary="Mars in Aries/Scorpio (own) or Capricorn (exalted), "
        "in a kendra (1/4/7/10) from Lagna.",
        detect=_mahapurusha("Mars"),
    ),
    YogaDetector(
        name="Bhadra Yoga",
        sanskrit="भद्र",
        category="mahapurusha",
        confidence="high",
        notes=None,
        rule_summary="Mercury in Gemini or Virgo (own = exalted sign), "
        "in a kendra (1/4/7/10) from Lagna.",
        detect=_mahapurusha("Mercury"),
    ),
    YogaDetector(
        name="Hamsa Yoga",
        sanskrit="हंस",
        category="mahapurusha",
        confidence="high",
        notes=None,
        rule_summary="Jupiter in Sagittarius/Pisces (own) or Cancer (exalted), "
        "in a kendra (1/4/7/10) from Lagna.",
        detect=_mahapurusha("Jupiter"),
    ),
    YogaDetector(
        name="Malavya Yoga",
        sanskrit="मालव्य",
        category="mahapurusha",
        confidence="high",
        notes=None,
        rule_summary="Venus in Taurus/Libra (own) or Pisces (exalted), "
        "in a kendra (1/4/7/10) from Lagna.",
        detect=_mahapurusha("Venus"),
    ),
    YogaDetector(
        name="Shasha Yoga",
        sanskrit="शश",
        category="mahapurusha",
        confidence="high",
        notes=None,
        rule_summary="Saturn in Capricorn/Aquarius (own) or Libra (exalted), "
        "in a kendra (1/4/7/10) from Lagna.",
        detect=_mahapurusha("Saturn"),
    ),
    YogaDetector(
        name="Gaja Kesari Yoga",
        sanskrit="गजकेसरी",
        category="chandra_based",
        confidence="high",
        notes=None,
        rule_summary="Jupiter occupies house 1, 4, 7, or 10 counted from the Moon's house.",
        detect=_kendra_from("Moon", "Jupiter"),
    ),
    YogaDetector(
        name="Chandra Mangala Yoga",
        sanskrit="चन्द्र-मंगल",
        category="chandra_based",
        confidence="high",
        notes=None,
        rule_summary="Moon and Mars occupy the same sign.",
        detect=_any_conjunct_any(("Moon",), ("Mars",)),
    ),
    YogaDetector(
        name="Budhaditya Yoga",
        sanskrit="बुधादित्य",
        category="surya_based",
        confidence="high",
        notes="Will trigger often - Mercury is never far from the Sun. Some sources add "
        "'and Mercury is not combust', not checked here (no combust-orb decision yet).",
        rule_summary="Sun and Mercury occupy the same sign.",
        detect=_any_conjunct_any(("Sun",), ("Mercury",)),
    ),
    YogaDetector(
        name="Guru Chandala Yoga",
        sanskrit="गुरु चाण्डाल",
        category="arishta",
        confidence="high",
        notes=None,
        rule_summary="Jupiter occupies the same sign as Rahu or Ketu.",
        detect=_any_conjunct_any(("Jupiter",), ("Rahu", "Ketu")),
    ),
    YogaDetector(
        name="Grahan Yoga",
        sanskrit="ग्रहण",
        category="arishta",
        confidence="high",
        notes=None,
        rule_summary="Sun or Moon occupies the same sign as Rahu or Ketu.",
        detect=_any_conjunct_any(("Sun", "Moon"), ("Rahu", "Ketu")),
    ),
    YogaDetector(
        name="Parivartana Yoga",
        sanskrit="परिवर्तन",
        category="parivartana",
        confidence="high",
        notes="Detects the sign-exchange mechanic only (high confidence). Classifying a given "
        "exchange as auspicious or inauspicious by which houses are involved is medium "
        "confidence per the ledger and not implemented here.",
        rule_summary="A planet occupies the sign ruled by a second planet, and that second "
        "planet occupies the sign ruled by the first.",
        detect=_parivartana,
    ),
]


def registry_entries(category: str = "all") -> list[YogaDetector]:
    if category == "all":
        return list(REGISTRY)
    return [detector for detector in REGISTRY if detector.category == category]


def _build_context(
    jd_ut: float, lat: float, lon: float, ayanamsa: str, node_type: str
) -> YogaContext:
    lagna_longitude = compute_ascendant_longitude(jd_ut, lat, lon, ayanamsa)
    raw_positions = compute_raw_planet_positions(jd_ut, ayanamsa, node_type)
    planets = {
        raw.name: PlanetPlacement(
            sidereal_longitude=raw.sidereal_longitude, sign=sign_of(raw.sidereal_longitude)
        )
        for raw in raw_positions
    }
    return YogaContext(lagna_longitude=lagna_longitude, planets=planets)


def compute_yogas(
    dob: str,
    tob: str,
    tz_offset: str,
    lat: float,
    lon: float,
    ayanamsa: str,
    node_type: str,
    category: str = "all",
) -> list[YogaResult]:
    configure_ephemeris_path()
    jd_ut = to_julian_day_ut(dob, tob, tz_offset)
    ctx = _build_context(jd_ut, lat, lon, ayanamsa, node_type)

    results = []
    for detector in registry_entries(category):
        formed_by = detector.detect(ctx)
        results.append(
            YogaResult(
                name=detector.name,
                sanskrit=detector.sanskrit,
                category=detector.category,
                present=bool(formed_by),
                confidence=detector.confidence,
                notes=detector.notes,
                formed_by=formed_by,
            )
        )
    return results
