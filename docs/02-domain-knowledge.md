# 02 — Domain Knowledge

Essential astrology concepts the engine must get right. Not an astrology textbook — just what the code needs.

## Two Systems We Support

| Aspect | 📿 Vedic (Parasari) | 🎯 K.P. (Krishnamurti Paddhati) |
|---|---|---|
| Ayanamsa | Lahiri | Krishnamurti (differs ~5′) |
| Houses | **Whole-Sign** (house = full rashi) | **Placidus** (unequal, cusp-based) |
| Divisional charts | D1, D9 (Navamsha), D10, D12, D30 etc. | D1 only; sub-lord carries detail |
| Key technique | Yogas, Dasha, Transits, Divisionals | Sub-lord theory, Ruling Planets, cuspal interlinks |
| Prediction unit | Mahadasha period | Significator + sub-lord combo |

**Rule**: Every output labels its system. Users can switch, but we never silently mix.

## Core Objects

### Rashi (Sign)
12 signs, 30° each: Mesha, Vrishabha, Mithuna, Karka, Simha, Kanya, Tula, Vrishchika, Dhanu, Makara, Kumbha, Meena. Each has a lord (ruling planet).

### Bhava (House)
12 houses mapped from Lagna (ascendant). In Vedic Whole-Sign, Bhava N = Lagna rashi + (N-1). In K.P., Bhava N = arc between Placidus cusps N and N+1.

### Nakshatra
27 lunar mansions, each 13°20'. Each nakshatra has a lord and is divided into 4 padas (quarters) of 3°20'.
Order: Ashwini, Bharani, Krittika, Rohini, Mrigashira, Ardra, Punarvasu, Pushya, Ashlesha, Magha, PurvaPhalguni, UttaraPhalguni, Hasta, Chitra, Swati, Vishakha, Anuradha, Jyeshtha, Mula, PurvaAshadha, UttaraAshadha, Shravana, Dhanishta, Shatabhisha, PurvaBhadrapada, UttaraBhadrapada, Revati.

### K.P. Sub
Each nakshatra of 13°20' is divided into 9 subs based on Vimshottari ratios (Ke:7, Ve:20, Su:6, Mo:10, Ma:7, Ra:18, Ju:16, Sa:19, Me:17 = 120). First sub = nakshatra lord. Sub arc = (lord_years / 120) × 13°20'.

Sub-sub is the next level — same proportions applied inside each sub.

### Vimshottari Dasha
Based on Moon's natal nakshatra. 120-year cycle, 9 planetary periods (same ratios as above).
Hierarchy: **Mahadasha (MD) → Antardasha (AD) → Pratyantardasha (PD) → Sookshma → Prana**.

Each level uses the same 9-planet sequence proportioned within the parent.

### Mudda Vimshottari Dasha
Annual sub-dasha. Calculated from the solar return date. 120 days total within a solar year, each MD/AD scaled down to days instead of years.

### Panchang
Five limbs of a day, from local sunrise:
1. **Vara** — weekday (lord = planet of day)
2. **Tithi** — lunar day (angular distance Moon-Sun / 12°, 30 tithis per lunar month)
3. **Nakshatra** — Moon's current nakshatra
4. **Yoga** — (Sun long + Moon long) / 13°20', 27 yogas
5. **Karana** — half of a tithi (11 karanas, Bhadra = Vishti is the classical "avoid")

Transitions are time-stamped per lat/lon.

### Hora
24 planetary hours per day. 12 day-horas (sunrise to sunset) + 12 night-horas (sunset to next sunrise). Day-hora length = (sunset - sunrise) / 12. Sequence per weekday follows the Chaldean order: Sa, Ju, Ma, Su, Ve, Me, Mo. First hora of day = weekday lord.

**Activity enum for `best_for`/`avoid_for`** (starter set, expand as classical hora texts are implemented — never invent beyond cited sources): `study`, `writing`, `contracts`, `travel`, `surgery`, `new_initiatives`, `routine_work`, `discipline`, `meetings`, `ceremonies`. Each hora's `nature` (benefic/malefic/neutral) plus its planetary lord determines which activities land in which list — defined per-lord, not per-hora-instance.

## Ayanamsa Precision

Lahiri (official Indian govt) vs Krishnamurti differs by ~4′54″ as of 2026. Both are "correct" — they're different reference points. We default Lahiri but offer Krishnamurti for K.P. computations (since K.P. founder used it).

**Decision**: Store planet longitudes in **tropical** form internally, apply ayanamsa at render time. Avoids re-export bugs.

## Lunar Nodes (Rahu/Ketu)

Rahu is computed from the **True Node** (`swe.TRUE_NODE`), not the Mean Node (ADR-019). Mean vs. True can differ by up to ~1.5°, enough to flip a K.P. sub-lord at a boundary — unacceptable given sub-lord precision is the stated moat. Ketu = Rahu + 180° always.

## Classical Yogas We Compute

Deterministic rules for ~50 classical yogas:
- **Raja Yogas**: Kendra + Trikona lord conjunctions/aspects
- **Dhana Yogas**: 2nd/5th/9th/11th lord combinations
- **Lakshmi Yoga**: 9th lord in own/exalted + benefic lagna lord
- **Gaja Kesari**: Jupiter in kendra from Moon
- **Vipreet Raja**: 6-8-12 lords in 6-8-12 houses
- **Neechabhanga Raja**: Debilitated planet with cancellation
- **Pancha Mahapurusha**: Mars=Ruchaka, Mercury=Bhadra, Venus=Malavya, Jupiter=Hamsa, Saturn=Shasha

Yoga detection is pure function → part of chart-compute MCP tool.

## Classical Texts (RAG Corpus Order of Priority)

1. **Brihat Parasara Hora Shastra (BPHS)** — foundational
2. **Phaladeepika (Mantreswara)** — practical interpretation
3. **Jataka Parijata** — detailed house readings
4. **Saravali** — classical yogas
5. **Krishnamurti Padhdhati 6 Readers** — K.P. system
6. **Lal Kitab** — remedies (separate corpus, controversial — label as "Lal Kitab tradition")

## What Not To Trust The LLM With

- Degree computations
- Dasha dates
- Panchang transitions
- Yoga formation detection
- Specific remedy prescriptions (always from classical corpus)

What the LLM is good for: narrative synthesis, tone, lifestyle recommendations, explaining why a yoga matters, drafting the readable version of the rule output.
