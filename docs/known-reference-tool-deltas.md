# Known Reference-Tool Deltas

Tracks measured disagreements between VAstroChart's own compute and external
reference tools used for golden-data verification (`docs/07-reference-chart.md`).
A delta logged here is **not** treated as a VAstroChart bug unless/until
investigation says otherwise — see the governance rule at the bottom.

---

## AstroSage vs VAstroChart (pyswisseph, Swiss Ephemeris, built 2026-05-26)

**Measured against**: 3 private dogfood golden charts (gitignored — real
individuals' birth data never appears in this public file; referenced below
as Chart 1/2/3 with no other identifying detail).

**Ayanamsa (Lahiri)**: matches to within 0.03–0.04 arc-minutes across all
three charts. Rules out a Lahiri-variant mismatch as the cause of anything
below.

**Rahu/Ketu**: off by 64–100 arc-minutes (over 1 degree) in all three charts
when VAstroChart computes its default **True Node** (ADR-019). **Confirmed
2026-10-12** (ADR-027): recomputing all three charts with `node_type="mean"`
closes the delta to under 0.3 arc-minutes in every case — AstroSage uses the
Mean Node. Not a bug; `node_type` is now a request parameter so callers can
choose either. Golden regression still checks against the True Node default
and excludes Rahu/Ketu longitude from strict tolerance there (sign/nakshatra
still checked), since that's testing our *default* behavior against
Mean-Node source data by design.

**Sun, Moon, Mercury, Venus, Mars**: consistently within ~0.1–1.7 arc-minutes
across all three charts — well inside the ±2' tolerance.

**Jupiter and Saturn**: consistently the largest deltas among the 7 classical
planets, and the only ones to exceed ±2' in two of three charts:

| Chart | Planet  | Delta (computed − AstroSage) |
|---|---|---|
| 1 | Jupiter | +1.63' |
| 2 | Saturn  | −6.24' |
| 2 | Jupiter | +0.47' |
| 3 | Jupiter | −2.72' |
| 3 | Mars    | −1.72' (inside tolerance, but notably larger than Sun/Moon/Mercury/Venus) |

**Sign, nakshatra, and pada matched exactly for every planet in every chart**,
Jupiter/Saturn included — the delta is small enough to never cross a
classification boundary. This is a longitude-precision disagreement only.

### Working hypothesis (not yet confirmed)

Both ends plausibly use genuine Swiss Ephemeris data, so a 2–6' delta
concentrated on the two slowest/outermost of the 7 classical planets looks
like an **ephemeris file build/version difference**, not a logic bug:
- Ruled out: ayanamsa mismatch (matches to 0.04'), Moshier fallback (confirmed
  `FLG_SWIEPH` bit set during this test, not `FLG_MOSEPH`), topocentric
  parallax and light-time/aberration (both calculated to be two orders of
  magnitude too small to explain a multi-arcminute delta for Jupiter/Saturn).
- Not ruled out: AstroSage's backend may use a different Swiss Ephemeris
  build/epoch-fit than the one VAstroChart downloaded (built 2026-05-26);
  outer-planet perturbation series are exactly where different builds of the
  same ephemeris family tend to diverge most.
- **Not confirmed** — no access to AstroSage's internal engine version to verify.

### Current handling

`apps/vastrochart-compute/tests/golden/test_golden_regression.py` uses the
default ±2' tolerance for all planets **except** Jupiter and Saturn, which use
a documented ±7' tolerance pending resolution. This is a deliberate, narrow
exception — not a general loosening of the golden-data bar.

### To resolve

- Cross-verify Jupiter/Saturn for these charts against a second independent
  tool (Jagannatha Hora, per `docs/07-reference-chart.md`'s preferred source).
- If a second tool agrees with VAstroChart: AstroSage was the outlier, revert
  Jupiter/Saturn to the standard ±2' tolerance.
- If a second tool agrees with AstroSage: investigate VAstroChart's outer-planet
  calculation for a real bug.
- If tools disagree with each other too: this is inherent ephemeris-build
  noise at this precision tier — keep the documented ±7' exception permanently
  and note it in `docs/07-reference-chart.md`.

---

## Governance

Per `docs/07-reference-chart.md`: a tolerance exceedance reflects a real bug,
a reference-tool error, or a legitimate ephemeris version difference. The
owner is the single approver for which applies and for any resulting golden-
entry or tolerance change — this file records findings, it doesn't make that
call unilaterally.
