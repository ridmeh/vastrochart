#!/usr/bin/env python3
"""
AstroApp — chart_compute prototype

Standalone starter demonstrating pyswisseph for Vedic + K.P. chart computation.
Validates against a reference chart (fill in your own birth data below).

Run:
    pip install pyswisseph
    python3 chart_compute.py

This prototype will become the core of chart-compute-mcp (Week 1 of roadmap).
"""

import swisseph as swe
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime, timedelta

# ---- Constants ----

AYANAMSA = {
    "lahiri": swe.SIDM_LAHIRI,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "raman": swe.SIDM_RAMAN,
}

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.TRUE_NODE,  # True Node per ADR-019 (K.P. sub-lord precision needs true, not mean, node)
}

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("PurvaPhalguni", "Venus"), ("UttaraPhalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("PurvaAshadha", "Venus"), ("UttaraAshadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("PurvaBhadrapada", "Jupiter"), ("UttaraBhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

# Vimshottari years per planet (sum = 120)
VIM_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIM_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

NAKSHATRA_ARC = 13 + 20/60  # 13°20'


@dataclass
class PlanetPosition:
    name: str
    sidereal_longitude: float
    sign: str
    sign_longitude: float
    nakshatra: str
    nakshatra_lord: str
    pada: int
    sub_lord: str
    retrograde: bool
    house_vedic: int = 0
    house_kp: int = 0


# ---- Helpers ----

def to_julian_day(year, month, day, hour, minute, tz_offset=0.0):
    """Convert local time to Universal Time Julian Day."""
    local_hours = hour + minute / 60.0
    ut_hours = local_hours - tz_offset
    jd = swe.julday(year, month, day, ut_hours)
    return jd


def get_sign_and_longitude(sidereal_long):
    sign_idx = int(sidereal_long // 30)
    sign_long = sidereal_long - sign_idx * 30
    return SIGNS[sign_idx], sign_long


def get_nakshatra_and_pada(sidereal_long):
    nak_idx = int(sidereal_long // NAKSHATRA_ARC)
    nak_name, nak_lord = NAKSHATRAS[nak_idx]
    long_in_nak = sidereal_long - nak_idx * NAKSHATRA_ARC
    pada = int(long_in_nak // (NAKSHATRA_ARC / 4)) + 1
    return nak_name, nak_lord, pada


def get_kp_sub_lord(sidereal_long):
    """K.P. sub-lord: Vimshottari-weighted subdivision of nakshatra."""
    nak_idx = int(sidereal_long // NAKSHATRA_ARC)
    _, nak_lord = NAKSHATRAS[nak_idx]
    long_in_nak = sidereal_long - nak_idx * NAKSHATRA_ARC

    # Sub sequence starts from nakshatra lord
    start_idx = VIM_ORDER.index(nak_lord)

    cumulative = 0.0
    for i in range(9):
        planet = VIM_ORDER[(start_idx + i) % 9]
        sub_arc = (VIM_YEARS[planet] / 120.0) * NAKSHATRA_ARC
        if long_in_nak < cumulative + sub_arc:
            return planet
        cumulative += sub_arc
    return VIM_ORDER[(start_idx + 8) % 9]  # last sub


def compute_vedic_house(sidereal_long, lagna_sidereal_long):
    """Whole-Sign: house = sign relative to Lagna sign."""
    lagna_sign = int(lagna_sidereal_long // 30)
    planet_sign = int(sidereal_long // 30)
    house = (planet_sign - lagna_sign) % 12 + 1
    return house


def compute_kp_house(sidereal_long, placidus_cusps):
    """K.P.: house = arc between Placidus cusps containing the planet."""
    for i in range(12):
        cusp_start = placidus_cusps[i]
        cusp_end = placidus_cusps[(i + 1) % 12]
        if cusp_end < cusp_start:  # crosses 0° Aries
            if sidereal_long >= cusp_start or sidereal_long < cusp_end:
                return i + 1
        else:
            if cusp_start <= sidereal_long < cusp_end:
                return i + 1
    return 1  # fallback


# ---- Main computation ----

def compute_chart(dob, tob, tz_offset, lat, lon, ayanamsa="lahiri"):
    """
    dob: 'YYYY-MM-DD'
    tob: 'HH:MM'
    tz_offset: float, e.g. 5.5 for IST
    """
    y, m, d = map(int, dob.split("-"))
    hr, mn = map(int, tob.split(":"))
    jd = to_julian_day(y, m, d, hr, mn, tz_offset)

    swe.set_sid_mode(AYANAMSA[ayanamsa])

    # Compute ascendant (Lagna) using Placidus for cusps (K.P. style)
    cusps_kp, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    lagna_long = ascmc[0]  # Ascendant sidereal longitude

    # Planets
    results = []
    for name, pid in PLANETS.items():
        pos, flags = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        sidereal_long = pos[0]
        speed = pos[3]
        retrograde = speed < 0

        sign, sign_long = get_sign_and_longitude(sidereal_long)
        nak, nak_lord, pada = get_nakshatra_and_pada(sidereal_long)
        sub = get_kp_sub_lord(sidereal_long)
        h_vedic = compute_vedic_house(sidereal_long, lagna_long)
        h_kp = compute_kp_house(sidereal_long, list(cusps_kp))

        results.append(PlanetPosition(
            name=name,
            sidereal_longitude=sidereal_long,
            sign=sign,
            sign_longitude=sign_long,
            nakshatra=nak,
            nakshatra_lord=nak_lord,
            pada=pada,
            sub_lord=sub,
            retrograde=retrograde,
            house_vedic=h_vedic,
            house_kp=h_kp,
        ))

    # Ketu = Rahu + 180
    rahu = next(p for p in results if p.name == "Rahu")
    ketu_long = (rahu.sidereal_longitude + 180) % 360
    k_sign, k_sign_long = get_sign_and_longitude(ketu_long)
    k_nak, k_nak_lord, k_pada = get_nakshatra_and_pada(ketu_long)
    k_sub = get_kp_sub_lord(ketu_long)
    results.append(PlanetPosition(
        name="Ketu",
        sidereal_longitude=ketu_long,
        sign=k_sign,
        sign_longitude=k_sign_long,
        nakshatra=k_nak,
        nakshatra_lord=k_nak_lord,
        pada=k_pada,
        sub_lord=k_sub,
        retrograde=rahu.retrograde,
        house_vedic=compute_vedic_house(ketu_long, lagna_long),
        house_kp=compute_kp_house(ketu_long, list(cusps_kp)),
    ))

    # Lagna as a "planet" entry for completeness
    lag_sign, lag_sign_long = get_sign_and_longitude(lagna_long)
    lag_nak, lag_nak_lord, lag_pada = get_nakshatra_and_pada(lagna_long)
    lag_sub = get_kp_sub_lord(lagna_long)

    return {
        "ascendant": {
            "sidereal_longitude": lagna_long,
            "sign": lag_sign,
            "sign_longitude": lag_sign_long,
            "nakshatra": lag_nak,
            "nakshatra_lord": lag_nak_lord,
            "pada": lag_pada,
            "sub_lord": lag_sub,
        },
        "planets": results,
        "kp_cusps": list(cusps_kp),
        "ayanamsa_used": ayanamsa,
    }


# ---- Pretty print ----

def print_chart(chart):
    print("\n" + "=" * 70)
    print("ASCENDANT (Lagna)")
    print("=" * 70)
    asc = chart["ascendant"]
    print(f"  Sign: {asc['sign']} {asc['sign_longitude']:.4f}°")
    print(f"  Nakshatra: {asc['nakshatra']} pada {asc['pada']} (lord: {asc['nakshatra_lord']})")
    print(f"  Sub-lord: {asc['sub_lord']}")

    print("\n" + "=" * 70)
    print(f"{'Planet':<10} {'Sign':<12} {'°':<10} {'Nak':<16} {'Pd':<4} {'Sub':<10} {'HVed':<5} {'HKP':<5} {'R':<2}")
    print("=" * 70)
    for p in chart["planets"]:
        retro = "R" if p.retrograde else ""
        print(f"{p.name:<10} {p.sign:<12} {p.sign_longitude:7.4f}°  {p.nakshatra:<16} {p.pada:<4} {p.sub_lord:<10} {p.house_vedic:<5} {p.house_kp:<5} {retro}")

    print("\n" + "=" * 70)
    print("K.P. Placidus Cusps (Krishnamurti would differ slightly)")
    print("=" * 70)
    for i, cusp in enumerate(chart["kp_cusps"], 1):
        s, sl = get_sign_and_longitude(cusp)
        print(f"  Cusp {i:>2}: {s} {sl:.4f}°")


# ---- Reference Chart Verification ----
#
# FILL IN YOUR OWN BIRTH DATA BELOW to validate the prototype against a known chart.
# Compare the output against an external reference tool (AstroSage, Jagannatha Hora,
# or any Swiss Ephemeris frontend) and update the EXPECTED values accordingly.

# ──────────── EDIT THESE ────────────
REFERENCE_DOB = "YYYY-MM-DD"             # e.g. "1990-01-15"
REFERENCE_TOB = "HH:MM"                  # 24h local time, e.g. "14:30"
REFERENCE_TZ_OFFSET = 0.0                # e.g. 5.5 for IST, -8.0 for PST (standard)
REFERENCE_LAT = 0.0                      # decimal degrees, e.g. 28.6139 for Delhi
REFERENCE_LON = 0.0                      # decimal degrees, e.g. 77.2090 for Delhi

EXPECTED_LAGNA_SIGN = "Virgo"            # e.g. "Virgo"
EXPECTED_MARS_SIGN = "Taurus"            # e.g. "Taurus"
EXPECTED_MARS_LONG_IN_SIGN = 0.0         # decimal degrees within sign, 0-30
# ─────────────────────────────────────


def verify_reference_chart():
    """Golden test — reference chart. Must match external reference tool ±2'."""
    print("\n" + "#" * 70)
    print(f"# AstroApp — Reference Chart (Lahiri)")
    print(f"# DOB: {REFERENCE_DOB}  TOB: {REFERENCE_TOB}  TZ: {REFERENCE_TZ_OFFSET:+.1f}")
    print("#" * 70)

    chart = compute_chart(
        dob=REFERENCE_DOB,
        tob=REFERENCE_TOB,
        tz_offset=REFERENCE_TZ_OFFSET,
        lat=REFERENCE_LAT,
        lon=REFERENCE_LON,
        ayanamsa="lahiri",
    )
    print_chart(chart)

    print("\n" + "=" * 70)
    print("GOLDEN ASSERTIONS")
    print("=" * 70)

    # Mars check (edit expected values above)
    mars = next(p for p in chart["planets"] if p.name == "Mars")
    print(f"  Mars sign: {mars.sign}  (expected: {EXPECTED_MARS_SIGN})")
    print(f"  Mars sign longitude: {mars.sign_longitude:.6f}°  (expected: {EXPECTED_MARS_LONG_IN_SIGN:.4f}°)")
    if EXPECTED_MARS_LONG_IN_SIGN > 0:
        diff_arcmin = abs(mars.sign_longitude - EXPECTED_MARS_LONG_IN_SIGN) * 60
        print(f"  Delta: {diff_arcmin:.3f}' — {'PASS' if diff_arcmin < 2 else 'FAIL'}")

    # Lagna check
    asc = chart["ascendant"]
    print(f"\n  Lagna sign: {asc['sign']}  (expected: {EXPECTED_LAGNA_SIGN})")
    print(f"  Lagna longitude: {asc['sign_longitude']:.6f}°")


if __name__ == "__main__":
    if REFERENCE_DOB == "YYYY-MM-DD":
        print("⚠  Please fill in REFERENCE_DOB, REFERENCE_TOB, REFERENCE_LAT, REFERENCE_LON")
        print("   near the top of this file, then re-run.")
    else:
        verify_reference_chart()
