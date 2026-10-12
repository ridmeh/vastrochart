"""Classical Vedic graha drishti (planetary aspects) - whole-sign/house
based, not raw-degree Western aspects.

Every graha aspects the 7th house from its own position (universal aspect).
Mars additionally aspects the 4th and 8th from itself; Jupiter the 5th and
9th; Saturn the 3rd and 10th (BPHS special aspects). v1 scope is binary
full-strength aspects only - partial-strength (3/4, 1/2, 1/4) drishti is
deferred to a later version.

Rahu/Ketu get the universal 7th-house aspect only here. Classical texts
disagree on whether/how nodes cast aspects (some give them Saturn-like
3rd/7th/10th, some say they don't aspect at all) - treating them like the 5
non-special-aspect grahas is a defensible, commonly-used convention, not an
asserted classical fact.

Both aspects.vedic_graha_drishti (planet/Lagna-to-planet/Lagna pairs) and
houses.whole_sign[].aspected_by (planet-to-house) are built from the SAME
per-planet aspected_houses() below, so they can never independently drift
out of sync.
"""

SPECIAL_ASPECTS = {
    "Mars": (4, 8),
    "Jupiter": (5, 9),
    "Saturn": (3, 10),
}


def _house_counted_from(base_house: int, count: int) -> int:
    """The `count`-th house counted inclusively from base_house, 1-indexed, wrapping."""
    return (base_house - 1 + count - 1) % 12 + 1


def aspected_houses(from_house: int, planet_name: str) -> dict[int, str]:
    """{house_number: aspect_type} this planet aspects, given its own
    whole-sign house number (1-12)."""
    result = {_house_counted_from(from_house, 7): "7th"}
    if planet_name in SPECIAL_ASPECTS:
        first, second = SPECIAL_ASPECTS[planet_name]
        label = f"{first}th_{second}th"
        result[_house_counted_from(from_house, first)] = label
        result[_house_counted_from(from_house, second)] = label
    return result


def compute_graha_drishti(
    planet_houses: dict[str, int], lagna_house: int = 1
) -> list[dict[str, str]]:
    """planet_houses: {planet_name: house_vedic_wholesign} for all 9 grahas.
    Lagna is always house 1 in whole-sign by definition and is a valid
    aspect target alongside planets."""
    targets = dict(planet_houses)
    targets["Lagna"] = lagna_house

    drishti = []
    for from_name, from_house in planet_houses.items():
        houses_aspected = aspected_houses(from_house, from_name)
        for to_name, to_house in targets.items():
            if to_name == from_name:
                continue
            if to_house in houses_aspected:
                drishti.append(
                    {
                        "from": from_name,
                        "to": to_name,
                        "aspect_type": houses_aspected[to_house],
                        "strength": "full",
                    }
                )
    return drishti


def compute_aspected_by(planet_houses: dict[str, int]) -> dict[int, list[str]]:
    """{house_number: [planet names aspecting it]}, for all 12 houses -
    independent of whether anything occupies that house."""
    result: dict[int, list[str]] = {house: [] for house in range(1, 13)}
    for name, house in planet_houses.items():
        for aspected_house in aspected_houses(house, name):
            result[aspected_house].append(name)
    return result
