# 09 — Canonical Output Schema

**This is the product.** Every endpoint returns a predictable, versioned JSON structure. The main app (or any developer consumer) is contractually guaranteed this shape.

> ⚠ **Breaking changes to this schema only ship via `/v2/`, `/v3/` endpoints.** Never mutate `/v1/` responses after launch.

---

## Response Envelope (Common To All Endpoints)

Every response wraps the payload in a standard envelope:

```json
{
  "api_version": "1.0.0",
  "endpoint": "/v1/charts/compute",
  "request_id": "req_01HC4XZQJ8M3VNT7P5G9BWFKMT",
  "computed_at": "2026-10-11T19:05:12.345Z",
  "compute_ms": 48,
  "ephemeris": {
    "name": "swiss_ephemeris",
    "library_version": "2.10.3.2",
    "data_source": "DE431"
  },
  "warnings": [],
  "input": { /* echoed inputs, with any defaults resolved */ },
  "data": { /* endpoint-specific payload */ }
}
```

- `request_id` is `req_` + ULID — same prefix on every endpoint, no per-endpoint variants; developers echo it in support requests
- `computed_at` is server UTC
- `compute_ms` is a performance signal for developers to budget around
- `ephemeris.library_version` is the pyswisseph library version; `data_source` is the ephemeris data file — these version independently, kept separate to avoid ambiguity when debugging (ADR-021). `data_source` is per-response, not a fixed constant: `"DE431"` when the loaded high-precision files covered the requested date, `"moshier_analytical"` when it fell back to the lower-precision Moshier model (ADR-026; see `EPHEMERIS_LOW_PRECISION_FALLBACK` below)
- `warnings` is always present (empty array when none) — non-fatal advisories about the response, e.g. a house system that couldn't be computed for the given input (see Placidus polar degeneracy below, ADR-022). Distinct from `error`: a response with `warnings` still has a full `data` payload; a response with `error` does not.
- `input` echoes resolved inputs (useful when caller passed defaults)

---

## `/v1/charts/compute` — Full Natal Chart

**Input**:
```json
{
  "dob": "1990-01-15",
  "tob": "14:30",
  "tz_offset": "+05:30",
  "lat": 28.6139,
  "lon": 77.2090,
  "ayanamsa": "lahiri",
  "node_type": "true",
  "house_systems": ["whole_sign", "placidus_kp"]
}
```

- `node_type` ∈ `"true" | "mean"`, default `"true"` — Rahu/Ketu computed from the True Node or Mean Node (ADR-027). A genuine methodological split (different schools/tools default differently), not a precision bug — both values are "correct" within their tradition. Ketu always mirrors Rahu + 180° regardless.

**Response `data`**:

```json
{
  "ayanamsa": {
    "name": "lahiri",
    "value_degrees": 23.6708,
    "value_formatted": "23°40'15\""
  },
  "ascendant": {
    "sidereal_longitude": 125.5833,
    "sidereal_longitude_formatted": "125°35'00\"",
    "sign": "Leo",
    "sign_lord": "Sun",
    "sign_degree": 5.5833,
    "sign_degree_formatted": "05°35'00\"",
    "nakshatra": "Magha",
    "nakshatra_lord": "Ketu",
    "pada": 2,
    "kp_sub_lord": "Venus",
    "kp_sub_sub_lord": "Sun"
  },
  "planets": [
    {
      "name": "Sun",
      "sanskrit": "Surya",
      "symbol": "☉",
      "sidereal_longitude": 271.2456,
      "sidereal_longitude_formatted": "271°14'44\"",
      "sign": "Capricorn",
      "sign_lord": "Saturn",
      "sign_degree": 1.2456,
      "sign_degree_formatted": "01°14'44\"",
      "nakshatra": "Uttara Ashadha",
      "nakshatra_lord": "Sun",
      "pada": 2,
      "kp_sub_lord": "Sun",
      "kp_sub_sub_lord": "Moon",
      "retrograde": false,
      "combust": false,
      "dignity": "neutral",
      "speed_degrees_per_day": 1.0183,
      "house_vedic_wholesign": 6,
      "house_kp_placidus": 6
    }
    // ... Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
  ],
  "houses": {
    "whole_sign": [
      {
        "house": 1,
        "sign": "Leo",
        "sign_lord": "Sun",
        "occupants": ["Mars"],
        "aspected_by": ["Jupiter", "Saturn"]
      }
      // ... houses 2-12
    ],
    "placidus_kp": [
      {
        "house": 1,
        "cusp_sidereal_longitude": 125.5833,
        "cusp_formatted": "Leo 05°35'00\"",
        "sign": "Leo",
        "sign_lord": "Sun",
        "nakshatra": "Magha",
        "nakshatra_lord": "Ketu",
        "kp_sub_lord": "Venus",
        "kp_sub_sub_lord": "Sun",
        "occupants": ["Mars"]
      }
      // ... houses 2-12
    ]
  },
  "nakshatra_distribution": {
    "ashwini": [],
    "bharani": [],
    "krittika": [],
    "rohini": ["Moon"],
    "mrigashira": ["Mars"],
    "ardra": [],
    "punarvasu": [],
    "pushya": [],
    "ashlesha": [],
    "magha": ["Lagna"],
    "purva_phalguni": [],
    "uttara_phalguni": [],
    "hasta": [],
    "chitra": [],
    "swati": [],
    "vishakha": ["Mercury"],
    "anuradha": [],
    "jyeshtha": [],
    "mula": ["Venus"],
    "purva_ashadha": [],
    "uttara_ashadha": ["Sun"],
    "shravana": [],
    "dhanishta": [],
    "shatabhisha": ["Rahu"],
    "purva_bhadrapada": [],
    "uttara_bhadrapada": [],
    "revati": ["Ketu"]
  },
  "aspects": {
    "vedic_graha_drishti": [
      {
        "from": "Mars",
        "to": "Jupiter",
        "aspect_type": "4th_8th",
        "strength": "full"
      }
    ],
    "kp_cuspal": [
      {
        "house": 1,
        "cuspal_sub_lord": "Venus",
        "interlinked_houses": [2, 7, 11]
      },
      {
        "house": 2,
        "cuspal_sub_lord": "Sun",
        "interlinked_houses": [1, 6, 10]
      }
      // ... houses 3-12
    ]
  }
}
```

**Guarantees**:
- Every planet always present (never omit Rahu/Ketu)
- Longitudes to 4 decimal places (sub-arc-second precision)
- Both Vedic Whole-Sign AND K.P. Placidus houses always computed and returned — `house_systems` input is accepted for forward-compatibility but has no effect in v1 (ADR-020; cheaper to compute once per ADR-004) — **except** `houses.placidus_kp` is `null` when Placidus is geometrically undefined at the given latitude/date (deep polar cases); `houses.whole_sign` is unaffected since it never degenerates. A `PLACIDUS_DEGENERATE_AT_LATITUDE` entry is added to the envelope `warnings` array in that case (ADR-022).
- Nakshatra distribution shows which planet is in each of 27 nakshatras, Lagna included
- Graha drishti (Vedic aspects) always included; Lagna is a valid aspect target, not just planets
- K.P. cuspal interlinks (`aspects.kp_cuspal`) always included: for each house, its cuspal sub-lord and which other houses that sub-lord's planet rules — the classical "cuspal interlink" technique
- Rahu/Ketu default to the **True Node** per ADR-019 — matters for K.P. sub-lord precision at boundaries — but callers can request `node_type: "mean"` instead (ADR-027); both are legitimate, not a precision workaround
- `speed_degrees_per_day` is **signed** — negative means retrograde, consistent with the `retrograde` boolean; never cross-check two fields that could disagree (ADR-023)
- Rahu AND Ketu `retrograde` are both computed from actual signed speed, never hardcoded — Ketu mirrors Rahu's retrograde state exactly, since it's the same node viewed 180° away (ADR-023)
- `houses.whole_sign[].aspected_by` is always derived from `aspects.vedic_graha_drishti` at render time — never computed independently, to prevent the two from silently disagreeing
- `dignity` is a 9-value enum: `exalted | moolatrikona | own | great_friend | friend | neutral | enemy | great_enemy | debilitated` — the five relationship values are the classical Panchadha Maitri compound (natural + temporary friendship), not a flat per-sign lookup (ADR-025)

**Polar degeneracy example** (e.g. lat 70°N, midsummer):
```json
{
  "warnings": [
    {
      "code": "PLACIDUS_DEGENERATE_AT_LATITUDE",
      "message": "Placidus cusps undefined above ~66 deg latitude for this date; whole_sign houses still computed.",
      "field": "lat"
    }
  ],
  "data": {
    "houses": {
      "whole_sign": [ /* full 12 houses, unaffected */ ],
      "placidus_kp": null
    }
  }
}
```

---

## `/v1/dasha` — Vimshottari Dasha

**Input**:
```json
{
  "dob": "1990-01-15",
  "tob": "14:30",
  "tz_offset": "+05:30",
  "lat": 28.6139,
  "lon": 77.2090,
  "ayanamsa": "lahiri",
  "as_of_date": "2026-10-10",
  "depth": "sookshma"
}
```

**Response `data`**:
```json
{
  "balance_at_birth": {
    "lord": "Mercury",
    "balance_years": 11.4523,
    "balance_formatted": "11y 5m 12d"
  },
  "mahadasha_sequence": [
    {
      "lord": "Mercury",
      "start": "1990-01-15",
      "end": "2001-07-07",
      "age_at_start": 0,
      "age_at_end": 11.47
    }
    // ... Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn
  ],
  "active_at_date": {
    "mahadasha": {
      "lord": "Venus",
      "start": "2015-07-22",
      "end": "2035-07-22",
      "years_remaining": 8.78,
      "percent_elapsed": 56.1
    },
    "antardasha": {
      "lord": "Jupiter",
      "start": "2025-02-19",
      "end": "2028-02-19",
      "years_remaining": 1.37,
      "percent_elapsed": 54.4
    },
    "pratyantardasha": {
      "lord": "Venus",
      "start": "2026-08-14",
      "end": "2027-01-23",
      "percent_elapsed": 35.2
    },
    "sookshma": {
      "lord": "Venus",
      "start": "2026-10-01",
      "end": "2026-10-29",
      "percent_elapsed": 32.1
    },
    "prana": {
      "lord": "Mercury",
      "start": "2026-10-09T14:00:00+05:30",
      "end": "2026-10-11T02:30:00+05:30",
      "percent_elapsed": 61.8
    }
  }
}
```

- `active_at_date` nests exactly as deep as `depth` requests — `depth: "md"` returns only `mahadasha`; `depth: "prana"` returns all five levels. `prana` periods are short enough (hours, not days) that `start`/`end` carry full datetimes rather than dates.
- `mahadasha_sequence` always lists exactly the 9 Mahadashas of one full 120-year Vimshottari cycle from birth — it does not repeat or extend, since a second cycle is identical in composition. If `as_of_date` falls beyond 120 years from birth, `active_at_date` is computed by wrapping modulo the 120-year cycle rather than extending `mahadasha_sequence`.

---

## `/v1/mudda-dasha` — Annual Sub-Dasha

**Input**:
```json
{
  "dob": "1990-01-15",
  "tob": "14:30",
  "tz_offset": "+05:30",
  "lat": 28.6139,
  "lon": 77.2090,
  "ayanamsa": "lahiri",
  "year_offset": 36,
  "as_of_date": "2026-02-01"
}
```

**Response `data`**:
```json
{
  "solar_return_date": "2026-01-15",
  "mudda_md": {
    "lord": "Venus",
    "start": "2026-01-15",
    "end": "2026-02-05"
  },
  "mudda_ad": {
    "lord": "Saturn",
    "start": "2026-01-28",
    "end": "2026-02-01"
  }
}
```

- `year_offset` is the year of life (36 = the solar return nearest the native's 36th birthday); `solar_return_date` is when transiting Sun returns to its natal sidereal longitude for that year
- `as_of_date` is optional, default today — which day within the mudda year `mudda_md`/`mudda_ad` describe. Added deliberately (ADR-030): the original schema draft omitted it, which left no way to say which day the output applies to.
- Mudda periods scale the **same 120-unit Vimshottari proportional cycle** as natal dasha, compressed to span one **full solar year** (~365.25 days, not a 120-day sub-slice — every day of the year has an active lord). 1 Vimshottari-year unit ≈ 365.25/120 ≈ 3.04 days (ADR-030; see `docs/02-domain-knowledge.md`). The birth-nakshatra balance fraction is the same one natal dasha uses, reused unchanged every year.
- `mudda_md` and `mudda_ad` are always both present — v1 ships exactly these two levels, no deeper nesting and no depth parameter.

---

## `/v1/panchang` — Daily Panchang

**Input**:
```json
{
  "date": "2026-10-10",
  "lat": 37.6819,
  "lon": -121.7680,
  "tz_offset": "-07:00"
}
```

**Response `data`**:
```json
{
  "date_local": "2026-10-10",
  "sunrise_local": "2026-10-10T07:04:33-07:00",
  "sunset_local": "2026-10-10T18:38:47-07:00",
  "vara": {
    "weekday": "Saturday",
    "lord": "Saturn"
  },
  "tithi": [
    {
      "name": "Chaturdashi",
      "number": 14,
      "paksha": "Krishna",
      "lord": "Kali",
      "start_local": "2026-10-09T22:15:00-07:00",
      "end_local": "2026-10-10T19:42:30-07:00",
      "nature": "neutral"
    },
    {
      "name": "Amavasya",
      "number": 15,
      "paksha": "Krishna",
      "lord": "Pitrs",
      "start_local": "2026-10-10T19:42:30-07:00",
      "end_local": "2026-10-11T17:08:00-07:00",
      "nature": "shunya"
    }
  ],
  "nakshatra": [ /* same shape with transition times */ ],
  "nitya_yoga": [ /* same shape — the 27-fold lunar yoga (Vishkumbha, Priti, Siddha, ...) from Sun+Moon longitude; distinct from the classical Raja/Dhana/Mahapurusha yogas returned by /v1/yogas */ ],
  "karana": [
    {
      "name": "Shakuni",
      "aka": null,
      "start_local": "2026-10-10T07:04:33-07:00",
      "end_local": "2026-10-10T19:42:30-07:00",
      "nature": "benefic"
    },
    {
      "name": "Vishti",
      "aka": "Bhadra",
      "start_local": "2026-10-10T19:42:30-07:00",
      "end_local": "2026-10-11T07:28:10-07:00",
      "nature": "inauspicious_classical"
    }
  ],
  "muhurta_flags": {
    "rahu_kaal": {"start_local": "...", "end_local": "..."},
    "yamaganda": {"start_local": "...", "end_local": "..."},
    "gulika": {"start_local": "...", "end_local": "..."},
    "abhijit": {"start_local": "...", "end_local": "..."}
  }
}
```

- `tithi`, `nakshatra`, `nitya_yoga` carry 1-2 entries per sunrise-to-sunrise window (each limb's duration is close to 24h). `karana` — being half a tithi, ~11-13h — can carry up to 3 entries in a single day. Always an array; never assume exactly one.
- `tithi[].lord` is a presiding **deity** (e.g. "Kali", "Pitrs"), not a planet — unlike every other `_lord` field in this schema (`sign_lord`, `nakshatra_lord`, `vara.lord`). Classically correct for tithi; flagged here so it doesn't read as an inconsistency.

---

## `/v1/hora` — Planetary Hours

**Input**:
```json
{
  "date": "2026-10-10",
  "lat": 37.6819,
  "lon": -121.7680,
  "tz_offset": "-07:00"
}
```

**Response `data`**:
```json
{
  "date_local": "2026-10-10",
  "sunrise_local": "...",
  "sunset_local": "...",
  "day_hora_minutes": 57.85,
  "night_hora_minutes": 62.15,
  "horas": [
    {
      "index": 1,
      "start_local": "2026-10-10T07:04:33-07:00",
      "end_local": "2026-10-10T08:02:24-07:00",
      "lord": "Saturn",
      "day_or_night": "day",
      "nature": "malefic",
      "best_for": ["discipline", "routine_work"],
      "avoid_for": ["new_initiatives", "travel"]
    }
    // ... 24 total (12 day + 12 night)
  ]
}
```

---

## `/v1/divisional/{varga}` — Divisional Chart

**Path parameter**: `varga` ∈ `["D1", "D9", "D10", "D12", "D16", "D20", "D24", "D30", "D60"]`

**Input**: Same as `/charts/compute`

**Response `data`**:
```json
{
  "varga": "D9",
  "varga_name": "Navamsha",
  "ascendant": {
    "sidereal_longitude": 260.75,
    "sidereal_longitude_formatted": "260°45'00\"",
    "sign": "Sagittarius",
    "sign_lord": "Jupiter",
    "sign_degree": 20.75,
    "sign_degree_formatted": "20°45'00\""
  },
  "planets": [
    {
      "name": "Sun",
      "sanskrit": "Surya",
      "symbol": "☉",
      "sidereal_longitude": 45.0,
      "sidereal_longitude_formatted": "45°00'00\"",
      "sign": "Taurus",
      "sign_lord": "Venus",
      "sign_degree": 15.0,
      "sign_degree_formatted": "15°00'00\"",
      "house_vedic_wholesign": 6
    }
    // ... Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
  ]
}
```

- Planets re-mapped to the varga chart: same shape as `/charts/compute`'s `planets` array, minus nakshatra/sub-lord/K.P. fields (K.P. sub-lord theory is D1-only per `docs/02-domain-knowledge.md` — never computed for a varga)
- Houses: only `house_vedic_wholesign` is meaningful in a varga chart (Whole-Sign from the varga ascendant); K.P. Placidus houses are **not** computed for vargas — K.P. stays D1-only
- `varga_name` is the Sanskrit name (D9 → "Navamsha", D10 → "Dashamsha", etc.) — always included alongside the `D{n}` code

---

## `/v1/yogas` — Classical Yoga Detection

**Input**:
```json
{
  "dob": "...", "tob": "...", "lat": ..., "lon": ..., "ayanamsa": "lahiri",
  "corpus": "all"
}
```

**Response `data`**:
```json
{
  "yogas_formed": [
    {
      "name": "Gaja Kesari Yoga",
      "sanskrit": "गज केसरी योग",
      "category": "benefic",
      "formed_by": ["Jupiter in kendra from Moon"],
      "exact_description": "Jupiter in 1st house from Moon (same sign)",
      "classical_reference": {
        "text": "Brihat Parashara Hora Shastra",
        "chapter": 36,
        "verse": 33
      },
      "strength": 0.85
    }
  ],
  "yogas_absent_notable": [
    {
      "name": "Chandra Mangala Yoga",
      "reason_absent": "Moon and Mars not in same sign or in aspect"
    }
  ]
}
```

---

## `/v1/transits` — Transit Hits In A Date Range

**Input**:
```json
{
  "dob": "...", "tob": "...", "lat": ..., "lon": ..., "ayanamsa": "lahiri",
  "start_date": "2026-10-10",
  "end_date": "2027-10-10",
  "planets": ["Jupiter", "Saturn"],
  "aspect_types": ["conjunction", "opposition"],
  "orb_degrees": 1.0
}
```

**Response `data`**:
```json
{
  "hits": [
    {
      "transit_planet": "Jupiter",
      "aspect_type": "conjunction",
      "natal_point": "Lagna",
      "natal_point_longitude": 125.5833,
      "exact_date": "2027-03-15T14:22:00Z",
      "orb_entry_date": "2027-03-10",
      "orb_exit_date": "2027-03-20",
      "transit_longitude_at_exact": 125.5833
    }
  ]
}
```

---

## Error Response Shape

All errors follow this envelope:

```json
{
  "api_version": "1.0.0",
  "endpoint": "/v1/charts/compute",
  "request_id": "req_01HC4XZQJ8M3VNT7P5G9BWFKMT",
  "error": {
    "code": "INVALID_LATITUDE",
    "message": "lat must be between -90 and 90",
    "field": "lat",
    "retry_safe": false,
    "documentation_url": "https://docs.vastrochart.com/errors/INVALID_LATITUDE"
  }
}
```

**Error codes committed to**:
- `INVALID_DATE`, `INVALID_TIME`, `INVALID_TZ`, `INVALID_LATITUDE`, `INVALID_LONGITUDE`
- `UNSUPPORTED_AYANAMSA`, `UNSUPPORTED_HOUSE_SYSTEM`, `UNSUPPORTED_VARGA`
- `DATE_OUT_OF_EPHEMERIS_RANGE` — empirically verified (2026-10-12, ADR-026) against the live `pyswisseph`/Moshier engine: roughly 3000 BCE to 3000 CE is the hard outer limit regardless of which data files are loaded. A date within that range but outside the currently-*loaded* high-precision files degrades to `EPHEMERIS_LOW_PRECISION_FALLBACK` (a warning, not this error) rather than failing.
- `INVALID_REQUEST` — generic fallback for a request validation failure that doesn't map to one of the specific field codes above (ADR-026)
- `RATE_LIMIT_EXCEEDED`, `INVALID_API_KEY`, `SUBSCRIPTION_INACTIVE`
- `INTERNAL_COMPUTE_ERROR` (retry-safe: true)

**Warning codes committed to** (envelope `warnings` array, response still has full `data` — see ADR-021/ADR-022):
- `PLACIDUS_DEGENERATE_AT_LATITUDE` — Placidus cusps undefined at this latitude/date; `houses.placidus_kp` is `null`, `houses.whole_sign` unaffected
- `EPHEMERIS_LOW_PRECISION_FALLBACK` (ADR-026) — date is within the engine's computable range but outside the currently-loaded high-precision Swiss Ephemeris files, so planetary positions were computed via the lower-precision Moshier analytical model instead; `ephemeris.data_source` in the envelope reflects this (`"moshier_analytical"` instead of `"DE431"`) for the same response

**Never** leak:
- Raw stack traces
- Internal file paths
- Any part of the input birth data in the error message beyond the field name

---

## Versioning Policy

- **Patch (1.0.x)**: Bug fixes, no shape change
- **Minor (1.x.0)**: Additive only — new optional fields, new endpoints
- **Major (2.0.0)**: Breaking changes — ships at `/v2/` while `/v1/` keeps running for 12 months minimum

Developers can pin to `api_version` in request headers.

---

## Schema Discipline

- All timestamps: RFC 3339 with explicit timezone
- All longitudes: decimal degrees to 4 places (sub-arc-second)
- All angles: separate `_degrees` (decimal) and `_formatted` (DMS string) fields
- Sanskrit names: optional, always both English and Sanskrit for canonical items
- No locale-specific formatting (no comma-decimal, no Hindi numerals in payload — those are UI concerns)

**This file is the contract.** Changes require a new ADR + migration plan.
