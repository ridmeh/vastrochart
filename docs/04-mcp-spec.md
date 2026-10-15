# 04 — MCP Server Tool Specification

**Server name**: `chart-compute-mcp`
**Framework**: FastMCP (Python)
**Underlying engine**: `pyswisseph` (Swiss Ephemeris Python binding)

All tools are deterministic, stateless, pure functions. No caching, no server-side storage between calls (see ADR-018). Field names in every tool's output match `docs/09-output-schema.md` exactly — MCP and REST are two transports over the identical contract (ADR-005).

---

## Call Sequencing

No hard dependencies between tools (ADR-037). Every tool that needs a birth chart takes the same raw birth-data parameters as its REST counterpart (`dob`, `tob`, `tz_offset`, `lat`, `lon`, `ayanamsa`, `node_type` where applicable) and recomputes whatever it needs internally — it does **not** take pre-computed values from a prior `compute_chart` call. This is a deliberate simplification from an earlier draft of this spec, which had chart-dependent tools consume `compute_chart`'s already-computed output to avoid re-deriving the ephemeris; measured recompute cost turned out to be low single-digit milliseconds even for the heaviest tool (`get_transit_hits`, ADR-036), so the efficiency that design was protecting isn't a real cost, and one validation contract per endpoint (shared with REST) is less to keep in sync than two.

Every tool is a sibling — call any of them in any order, in parallel or sequentially, client's choice:

```
compute_chart(dob, tob, tz_offset, lat, lon, ayanamsa, node_type)
get_dasha(dob, tob, tz_offset, lat, lon, ayanamsa, as_of_date, depth)
get_mudda_dasha(dob, tob, tz_offset, lat, lon, ayanamsa, year_offset, as_of_date)
compute_divisional(dob, tob, tz_offset, lat, lon, ayanamsa, node_type, varga)
detect_yogas(dob, tob, tz_offset, lat, lon, ayanamsa, node_type, category)
get_transit_hits(dob, tob, tz_offset, lat, lon, ayanamsa, node_type, start_date, end_date, planets, aspect_types, orb_degrees)

get_panchang(date, lat, lon, tz_offset)       ← no birth-chart dependency at all
get_hora(date, lat, lon, tz_offset)           ← same
list_yoga_detectors(category)                 ← same — static registry, no birth data at all
```

---

## Tool 1: `compute_chart`

**Purpose**: Core birth-chart computation — planetary longitudes, houses, nakshatras, subs, aspects. (Yoga detection lives only in `detect_yogas` — no duplication.)

```json
{
  "name": "compute_chart",
  "description": "Compute a full Vedic + K.P. natal chart from birth data. Both house systems are always computed.",
  "input": {
    "dob": "ISO date, e.g. '1990-01-15'",
    "tob": "24h time, e.g. '14:30'",
    "tz_offset": "string, ISO-style signed offset, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "node_type": "enum: 'true' | 'mean' (default: 'true') - Rahu/Ketu node type, ADR-027"
  },
  "output": {
    "ayanamsa": { "name": "...", "value_degrees": "float", "value_formatted": "DMS string" },
    "ascendant": {
      "sidereal_longitude": "float", "sidereal_longitude_formatted": "DMS string",
      "sign": "string", "sign_lord": "string",
      "sign_degree": "float, 0-30", "sign_degree_formatted": "DMS string",
      "nakshatra": "string", "nakshatra_lord": "string", "pada": "int, 1-4",
      "kp_sub_lord": "string", "kp_sub_sub_lord": "string"
    },
    "planets": [
      {
        "name": "Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Rahu|Ketu",
        "sanskrit": "string", "symbol": "string",
        "sidereal_longitude": "float", "sidereal_longitude_formatted": "DMS string",
        "sign": "string", "sign_lord": "string",
        "sign_degree": "float, 0-30", "sign_degree_formatted": "DMS string",
        "nakshatra": "string", "nakshatra_lord": "string", "pada": "int, 1-4",
        "kp_sub_lord": "string", "kp_sub_sub_lord": "string",
        "retrograde": "boolean", "combust": "boolean",
        "dignity": "enum: exalted | moolatrikona | own | great_friend | friend | neutral | enemy | great_enemy | debilitated (Panchadha Maitri — ADR-025)",
        "speed_degrees_per_day": "float",
        "house_vedic_wholesign": "int, 1-12",
        "house_kp_placidus": "int, 1-12"
      }
      // ... all 9 planets, Rahu/Ketu always present
    ],
    "houses": {
      "whole_sign": "array of 12 {house, sign, sign_lord, occupants, aspected_by} — see 09-output-schema.md",
      "placidus_kp": "array of 12 {house, cusp_sidereal_longitude, cusp_formatted, sign, sign_lord, nakshatra, nakshatra_lord, kp_sub_lord, kp_sub_sub_lord, occupants}"
    },
    "nakshatra_distribution": "map of all 27 nakshatra keys -> array of occupants (planets + 'Lagna')",
    "aspects": {
      "vedic_graha_drishti": "array of {from, to, aspect_type, strength} — Lagna is a valid 'to' target",
      "kp_cuspal": "array of {house, cuspal_sub_lord, interlinked_houses} — cuspal sub-lord interlink technique"
    },
    "warnings": "array, e.g. EPHEMERIS_LOW_PRECISION_FALLBACK if dob falls outside the loaded Swiss Ephemeris files"
  }
}
```

---

## Tool 2: `get_dasha`

**Purpose**: Vimshottari dasha hierarchy for a given date.

```json
{
  "name": "get_dasha",
  "description": "Returns birth-MD balance, full MD sequence, and active MD/AD/PD/Sookshma for a date.",
  "input": {
    "dob": "ISO date",
    "tob": "24h time",
    "tz_offset": "string, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "as_of_date": "ISO date",
    "depth": "enum: 'md' | 'ad' | 'pd' | 'sookshma' | 'prana' (default: 'sookshma')"
  },
  "output": {
    "balance_at_birth": { "lord": "string", "balance_years": "float", "balance_formatted": "e.g. '11y 5m 12d'" },
    "mahadasha_sequence": "array of {lord, start, end, age_at_start, age_at_end} for all 9 MDs from birth",
    "active_at_date": {
      "mahadasha": { "lord": "string", "start": "date", "end": "date", "years_remaining": "float", "percent_elapsed": "float" },
      "antardasha": "same shape, present if depth >= ad",
      "pratyantardasha": "same shape, present if depth >= pd",
      "sookshma": "same shape, present if depth >= sookshma"
    },
    "warnings": "array, e.g. EPHEMERIS_LOW_PRECISION_FALLBACK if dob falls outside the loaded Swiss Ephemeris files"
  }
}
```

---

## Tool 3: `get_mudda_dasha`

**Purpose**: Annual (Varshaphal) sub-dasha based on the solar return (ADR-030). Stateless — derives its own birth-MD balance and locates the solar return from raw birth data, does not require `get_dasha` to have run first.

```json
{
  "name": "get_mudda_dasha",
  "description": "Annual sub-dasha for a given year of life, computed from the solar return.",
  "input": {
    "dob": "ISO date",
    "tob": "24h time, e.g. '14:30'",
    "tz_offset": "string, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "year_offset": "int, e.g. 50 for the 50th year of life",
    "as_of_date": "ISO date, optional, default today - which day within the mudda year to describe"
  },
  "output": {
    "solar_return_date": "ISO date",
    "mudda_md": { "lord": "string", "start": "date", "end": "date" },
    "mudda_ad": { "lord": "string", "start": "date", "end": "date" },
    "as_of_date": "ISO date - the resolved value (today's date if not supplied)",
    "warnings": "array, e.g. EPHEMERIS_LOW_PRECISION_FALLBACK"
  }
}
```

---

## Tool 4: `get_panchang`

**Purpose**: Five limbs of a day with transition timestamps. No birth-chart dependency.

```json
{
  "name": "get_panchang",
  "input": {
    "date": "ISO date",
    "lat": "float",
    "lon": "float",
    "tz_offset": "string, e.g. '-07:00'"
  },
  "output": {
    "date_local": "ISO date",
    "sunrise_local": "ISO datetime, explicit offset",
    "sunset_local": "ISO datetime, explicit offset",
    "vara": { "weekday": "string", "lord": "string" },
    "tithi": "array of {name, number, paksha, lord, start_local, end_local, nature}",
    "nakshatra": "array, same transition shape",
    "nitya_yoga": "array, same transition shape — distinct from the classical yogas returned by detect_yogas",
    "karana": "array of {name, aka, start_local, end_local, nature}",
    "muhurta_flags": {
      "rahu_kaal": "{start_local, end_local}",
      "yamaganda": "{start_local, end_local}",
      "gulika": "{start_local, end_local}",
      "abhijit": "{start_local, end_local}"
    }
  }
}
```

---

## Tool 5: `get_hora`

**Purpose**: 24 planetary hours for a day. No birth-chart dependency.

```json
{
  "name": "get_hora",
  "input": {
    "date": "ISO date",
    "lat": "float",
    "lon": "float",
    "tz_offset": "string, e.g. '-07:00'"
  },
  "output": {
    "date_local": "ISO date",
    "sunrise_local": "ISO datetime",
    "sunset_local": "ISO datetime",
    "day_hora_minutes": "float",
    "night_hora_minutes": "float",
    "horas": "array of 24 {index, start_local, end_local, lord, day_or_night, nature, best_for, avoid_for}"
  }
}
```

---

## Tool 6: `get_transit_hits`

**Purpose**: Find when transiting planets contact natal degrees, in a date range.

```json
{
  "name": "get_transit_hits",
  "input": {
    "dob": "ISO date",
    "tob": "24h time",
    "tz_offset": "string, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "node_type": "enum: 'true' | 'mean' (default: 'true')",
    "start_date": "ISO date",
    "end_date": "ISO date",
    "planets": "array, default all 9 grahas",
    "aspect_types": "enum array: 'conjunction' | 'opposition' | 'trine' | 'square' | 'sextile', default all 5",
    "orb_degrees": "float, 0 < value <= 15, default 1.0"
  },
  "output": {
    "hits": "array of {transit_planet, aspect_type, natal_point, natal_point_longitude, exact_date, orb_entry_date, orb_exit_date, transit_longitude_at_exact}"
  }
}
```

---

## Tool 7: `compute_divisional`

**Purpose**: Vargas (divisional charts) — D9, D10, D12, D30 etc. The varga remapping itself is a pure transform of D1 sidereal longitudes (`compute/divisional.py`), but this tool derives the D1 longitudes from raw birth data rather than taking them as input.

```json
{
  "name": "compute_divisional",
  "input": {
    "dob": "ISO date",
    "tob": "24h time",
    "tz_offset": "string, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "node_type": "enum: 'true' | 'mean' (default: 'true')",
    "varga": "enum: 'D1' | 'D9' | 'D10' | 'D12' | 'D16' | 'D20' | 'D24' | 'D30' | 'D60'"
  },
  "output": {
    "varga": "string, e.g. 'D9'",
    "planets": "array, same shape as compute_chart planets (sign/nakshatra/pada re-derived in the varga frame)",
    "ascendant": "same shape as compute_chart ascendant, re-derived in the varga frame"
  }
}
```

---

## Tool 8: `detect_yogas`

**Purpose**: Classical yoga detection. The 11 detectors themselves are pure functions of sign/house placement (`compute/yogas.py`), but this tool derives those placements from raw birth data rather than taking them as input.

```json
{
  "name": "detect_yogas",
  "input": {
    "dob": "ISO date",
    "tob": "24h time",
    "tz_offset": "string, e.g. '+05:30'",
    "lat": "float, degrees",
    "lon": "float, degrees",
    "ayanamsa": "enum: 'lahiri' | 'krishnamurti' | 'raman' (default: 'lahiri')",
    "node_type": "enum: 'true' | 'mean' (default: 'true')",
    "category": "enum: one of the registry categories (see list_yoga_detectors) | 'all' (default: 'all')"
  },
  "output": {
    "yogas": "array of {name, sanskrit, category, present, confidence, notes, formed_by} — every evaluated detector, present:true or false, not just hits"
  }
}
```
`confidence` (`high`/`medium`/`low`) is a per-detector property, not computed per-chart — see `docs/09-output-schema.md`'s `/v1/yogas` section for the full field contract and why no `classical_reference`/`strength` fields are returned.

---

## Tool 9: `list_yoga_detectors`

**Purpose**: Static catalog of every yoga detector this version evaluates — no chart input, no birth data. Mirrors `/v1/yogas/registry`.

```json
{
  "name": "list_yoga_detectors",
  "input": {
    "category": "enum: one of the registry categories | 'all' (default: 'all')"
  },
  "output": {
    "detectors": "array of {name, sanskrit, category, confidence, rule_summary, notes}"
  }
}
```
Reads from the same in-code registry as `detect_yogas`, so the two can't drift apart.

---

## Error contracts

Input validation failures and `EphemerisRangeError` raise inside the tool function and surface as a standard MCP tool error (`isError: true`, message text from the underlying Pydantic/exception message) — **not** REST's custom JSON error envelope. The envelope (`error: {code, message, field, retry_safe, documentation_url}`) is an HTTP-response-specific convenience and isn't meaningful inside the MCP protocol's own error reporting (ADR-037). Never partial success either way.

## Observability

Each tool call emits: `tool_name`, `input_hash` (for correlation/log grouping only — never a server-side lookup key), `output_bytes`, `duration_ms`, `ephemeris_version`.

## Testing

Golden test set: 50 charts with hand-verified outputs. Any tool change must pass golden set 100% before merge.

Starting golden chart: owner's reference chart (see `docs/07-reference-chart.md`).
