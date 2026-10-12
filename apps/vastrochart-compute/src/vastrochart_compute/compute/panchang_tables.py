"""Classical panchang lookup tables: tithi names/lords/nature, nitya yoga
names/nature, karana names/nature, muhurta-flag weekday-segment tables.

CONFIDENCE NOTE (be honest, don't hallucinate precision): the astronomical
math elsewhere in this package (sunrise/sunset, tithi/nakshatra/yoga/karana
NUMBER and transition TIMES) is exact and deterministic - no uncertainty
there. These specific classical NAME/LORD/NATURE assignments, however, are
reconstructed from general Jyotish knowledge, not pulled from a verified
live source. Confidence varies per table, noted inline. Cross-verify against
DrikPanchang (prompts/starter-prompts.md's own stated reference) before
treating any of this as authoritative - flagged to the user, not silently
presented as fact.
"""

VARA_LORDS = {
    "Sunday": "Sun",
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
}

# Tithi base names (1-14, shared by both parities) + lords (deities, not
# planets - per docs/09-output-schema.md's own guarantee). Moderate
# confidence: 7/8/11/14/15 well-established across sources; 3/4/5/6/9/10/13
# have some textual variation I'm not fully certain of.
_TITHI_BASE_NAMES = [
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
]
_TITHI_BASE_LORDS = [
    "Agni",
    "Brahma",
    "Gauri",
    "Ganesha",
    "Naga",
    "Kartikeya",
    "Surya",
    "Shiva",
    "Durga",
    "Yama",
    "Vishnu",
    "Vishnu",
    "Kamadeva",
    "Kali",
]
# Classical 5-fold tithi nature cycle (Nanda/Bhadra/Jaya/Rikta/Purna),
# repeating every 5 tithis within each paksha - well-established, higher
# confidence than the lord table above.
_TITHI_NATURE_CYCLE = ["nanda", "bhadra", "jaya", "rikta", "purna"]


def tithi_name_lord_nature(tithi_number: int) -> tuple[str, str, str]:
    """tithi_number: 1-30 (1-15 Shukla, 16-30 Krishna)."""
    position_in_paksha = ((tithi_number - 1) % 15) + 1  # 1-15
    if position_in_paksha == 15:
        if tithi_number == 15:
            return "Purnima", "Chandra", "purna"
        return "Amavasya", "Pitrs", "shunya"  # special-cased, not just "purna"
    name = _TITHI_BASE_NAMES[position_in_paksha - 1]
    lord = _TITHI_BASE_LORDS[position_in_paksha - 1]
    nature = _TITHI_NATURE_CYCLE[(position_in_paksha - 1) % 5]
    return name, lord, nature


# 27 nitya yoga names - this specific list is highly standardized across
# Jyotish software, high confidence on names. Nature (auspicious/
# inauspicious) follows the commonly-cited "9 malefic yogas" classification
# - moderate-good confidence, not independently verified here.
NITYA_YOGA_NAMES = [
    "Vishkumbha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]
_INAUSPICIOUS_YOGAS = {
    "Vishkumbha",
    "Atiganda",
    "Shula",
    "Ganda",
    "Vyaghata",
    "Vajra",
    "Vyatipata",
    "Parigha",
    "Vaidhriti",
}


def nitya_yoga_name_nature(yoga_number: int) -> tuple[str, str]:
    """yoga_number: 1-27."""
    name = NITYA_YOGA_NAMES[(yoga_number - 1) % 27]
    nature = "inauspicious" if name in _INAUSPICIOUS_YOGAS else "auspicious"
    return name, nature


# Karana: 60 half-tithis per lunar month. karana #1 is always the fixed
# Kimstughna; #2-57 cycle through the 7 "movable" karanas (56 = 7x8 exactly);
# #58-60 are the fixed Shakuni/Chatushpada/Naga. Structure well-established;
# exact nature labels beyond Vishti (classically inauspicious, "Bhadra") are
# lower confidence.
_MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
_KARANA_NATURE = {
    "Vishti": "inauspicious_classical",
    "Kimstughna": "neutral",
    "Shakuni": "neutral",
    "Chatushpada": "neutral",
    "Naga": "neutral",
}


def karana_name_aka_nature(karana_number: int) -> tuple[str, str | None, str]:
    """karana_number: 1-60 within a lunar month (derive from tithi context)."""
    if karana_number == 1:
        name = "Kimstughna"
    elif karana_number == 58:
        name = "Shakuni"
    elif karana_number == 59:
        name = "Chatushpada"
    elif karana_number == 60:
        name = "Naga"
    else:
        name = _MOVABLE_KARANAS[(karana_number - 2) % 7]
    aka = "Bhadra" if name == "Vishti" else None
    nature = _KARANA_NATURE.get(name, "benefic")
    return name, aka, nature


# Day (sunrise-to-sunset) divided into 8 equal segments; which segment
# (1-8, 1-indexed from sunrise) is the inauspicious one, by weekday.
# Standard, well-established tables - higher confidence than the deity/
# nature tables above.
RAHU_KAAL_SEGMENT = {
    "Sunday": 8,
    "Monday": 2,
    "Tuesday": 7,
    "Wednesday": 5,
    "Thursday": 6,
    "Friday": 4,
    "Saturday": 3,
}
YAMAGANDA_SEGMENT = {
    "Sunday": 5,
    "Monday": 4,
    "Tuesday": 3,
    "Wednesday": 2,
    "Thursday": 1,
    "Friday": 7,
    "Saturday": 6,
}
GULIKA_SEGMENT = {
    "Sunday": 7,
    "Monday": 6,
    "Tuesday": 5,
    "Wednesday": 4,
    "Thursday": 3,
    "Friday": 2,
    "Saturday": 1,
}
