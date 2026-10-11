# 07 — Golden Regression Dataset

VAstroChart's correctness guarantee is enforced through a **golden regression dataset**: hand-verified birth charts with their expected JSON outputs. Every endpoint change runs these in CI. A single ±2′ delta on any planetary longitude blocks merge.

> **This is the single most important test asset.** Nobody else in astro-tech open-source has a comparable dataset. Invest the time in Week 1 to build it right.

---

## Dataset Shape

```
tests/golden/
├── chart_01_tropical_mid_latitude.json
├── chart_02_sandhi_edge_degree.json
├── chart_03_polar_latitude.json
├── chart_04_retrograde_rahu.json
├── chart_05_southern_hemisphere.json
├── chart_06_dst_boundary.json
├── chart_07_kp_sublord_boundary.json
├── chart_08_pre_1900_date.json
├── chart_09_future_date.json
├── chart_10_owner_reference.json          ← private, dogfood
└── schemas/
    └── golden_entry.json                   ← JSON schema for each entry
```

Each entry has:
```json
{
  "name": "chart_01_tropical_mid_latitude",
  "description": "Standard tropical chart, mid-latitude, no edge cases",
  "input": {
    "dob": "...",
    "tob": "...",
    "tz_offset": "...",
    "lat": ...,
    "lon": ...,
    "ayanamsa": "lahiri",
    "house_systems": ["whole_sign", "placidus_kp"]
  },
  "source_of_truth": {
    "tool": "AstroSage" | "Jagannatha Hora" | "Parasara's Light",
    "exported_at": "2026-10-10",
    "verified_by": "owner" | "jyotish_mentor_name"
  },
  "expected": {
    /* full canonical JSON response as defined in docs/09-output-schema.md */
  },
  "tolerances": {
    "longitude_arcmin": 2.0,
    "cusp_arcmin": 2.0,
    "dasha_days": 1
  }
}
```

---

## Why 10 Charts (Minimum)

Each chart targets a specific class of bug:

| # | Case | Catches |
|---|---|---|
| 1 | Mid-latitude typical chart | Baseline correctness |
| 2 | Planet at 29°59' of a sign | Sandhi / sign-boundary handling |
| 3 | Polar latitude (lat > 66° or < -66°) | Placidus house system degeneracy |
| 4 | Rahu retrograde at natal | Node computation correctness |
| 5 | Southern hemisphere chart | Hemisphere-sign assumption bugs |
| 6 | Birth within DST transition | TZ offset handling |
| 7 | Planet at K.P. sub-lord boundary | Sub-lord algorithm precision |
| 8 | Pre-1900 date | Historical ephemeris coverage |
| 9 | Future date (2050+) | Future ephemeris coverage |
| 10 | Owner's own chart | Dogfood baseline (private — not in public repo) |

**Expansion target**: 50+ charts by Month 3, covering divisional charts, each major yoga, each K.P. significator pattern.

---

## How To Collect A Golden Entry

For each chart:

1. **Pick a birth record** (publicly known: historical figure, or synthetic test case)
2. **Export from the reference tool**:
   - Primary: Jagannatha Hora (free, authoritative, direct Swiss Ephemeris)
   - Backup: AstroSage web + manual verification
   - Secondary cross-check: Parasara's Light (if available)
3. **Encode the expected JSON** in the shape of VAstroChart's canonical output
4. **Cross-verify** each planet longitude ± 2 arc-minutes between tools
5. **Document discrepancies** between tools (there WILL be some — note them)
6. **Commit to repo** with the `source_of_truth` field populated

**Time per entry**: ~1 hour (export + encode + verify).

---

## The Golden Entry For The Owner's Chart

Owner fills in `chart_10_owner_reference.json` locally. **This file is `.gitignore`'d from the public repo** — it's for private dogfood regression only.

Template to fill in:

```json
{
  "name": "chart_10_owner_reference",
  "description": "Owner's natal chart — private dogfood",
  "input": {
    "dob": "<fill in>",
    "tob": "<fill in>",
    "tz_offset": "<fill in>",
    "lat": "<fill in>",
    "lon": "<fill in>",
    "ayanamsa": "lahiri",
    "house_systems": ["whole_sign", "placidus_kp"]
  },
  "source_of_truth": {
    "tool": "AstroSage + Jagannatha Hora cross-verified",
    "exported_at": "<fill in>",
    "verified_by": "owner"
  },
  "expected": {
    "<fill in with canonical response>"
  },
  "tolerances": {
    "longitude_arcmin": 2.0,
    "cusp_arcmin": 2.0,
    "dasha_days": 1
  }
}
```

---

## Running Golden Regression

```bash
pytest tests/golden/ -v
```

CI blocks merge if any delta exceeds tolerance. Report format:
```
PASS  chart_01_tropical_mid_latitude    All planets within 0.3' tolerance
FAIL  chart_02_sandhi_edge_degree       Mars longitude delta: 2.4' (tolerance 2.0')
```

A tolerance exceedance either:
- Reflects a real bug → fix the compute code
- Reflects reference-tool error → update the golden entry with better source-of-truth
- Reflects a legitimate ephemeris version change → bump the version pin + document in release notes

---

## Golden Dataset Governance

- **Owner is the single approver** for golden-entry changes (prevents compliance drift)
- Every PR that modifies a golden entry must explain WHY the expected value changed
- The dataset itself is versioned alongside the API (`golden-v1`, `golden-v2` on breaking schema changes)

🙏 **This dataset is a competitive moat.** Prokerala/AstroSage don't publish golden sets. VAstroChart doing so (at least a subset of 20-30 synthetic charts) builds developer trust and differentiates on rigor.
