# 05 — Architecture Decision Records (ADRs)

Chronological log of key architectural decisions, with context and rationale.

---

## ADR-001: Swiss Ephemeris as compute engine

**Decision**: Use `pyswisseph` as the single ephemeris source.
**Rationale**: Battle-tested; handles edge cases (polar lat, nodes, retrograde). Alternative = 6-12 months of JPL DE441 engineering.
**License risk**: AGPL §13 requires publishing server source to users. Options: (a) comply by publishing MCP server source as open-core, (b) buy commercial Swiss Ephemeris license (~€400 one-time) if we need to keep source private.

---

## ADR-002: Stateless compute, no persistence

**Decision**: VAstroChart stores zero PII. Every request is self-contained; results returned, memory GC'd.
**Rationale**:
- Narrows compliance surface to Processor-only
- Enables scale-to-zero economics
- Zero breach blast radius for end-user data
- Simpler architecture (no DB, no backups, no retention policies)
**Trade-off**: Can't cache results across requests. Mitigation: pyswisseph is fast enough (<50ms) that caching is unnecessary at API tier. If a customer needs cross-request state, they implement it in their main app.

---

## ADR-003: Lahiri default ayanamsa, Krishnamurti opt-in

**Decision**: Default `ayanamsa=lahiri`. Users request `ayanamsa=krishnamurti` for K.P. computations.
**Rationale**: Lahiri is government-of-India standard; K.P. founder used Krishnamurti. ~4′54″ difference matters at sign/pada/sub boundaries.
**Implementation**: Store planet positions tropically; apply ayanamsa at response-build time.

---

## ADR-004: Whole-Sign Vedic + Placidus K.P. in same response

**Decision**: `/charts/compute` returns both house systems by default (both arrays in `data.houses`).
**Rationale**:
- Vedic Parasari uses Whole-Sign; K.P. uses Placidus
- Developers may need either or both; cheaper to compute both once than two separate calls
- Clear labeling prevents silent mixing
**Trade-off**: Slightly larger response payload (~2 KB). Acceptable.

---

## ADR-005: FastAPI + FastMCP in same container

**Decision**: Single container exposes BOTH `/v1/*` REST endpoints AND `/mcp/sse` MCP transport.
**Rationale**:
- Zero duplication: both paths marshal to the same Pydantic models
- Same deployment lifecycle; one image to version and release
- MCP is a transport, not a separate service
**Alternative considered**: Two separate services. Rejected — unnecessary complexity for the same compute.

---

## ADR-006: Azure Container Apps over Azure Functions

**Decision**: Deploy on **ACA**, not Functions.
**Rationale**:
- FastAPI runs natively on ACA
- pyswisseph C extensions clean on ACA, awkward on Functions
- MCP SSE streaming supported natively on ACA
- Same Docker image local → prod (true parity)
- Scale-to-zero still available via KEDA (we choose min=1 for warm UX)

---

## ADR-007: Front Door Premium + API Management Consumption

**Decision**: Edge = Front Door Premium (WAF/DDoS/CDN). Gateway = API Management Consumption tier.
**Rationale**:
- Front Door Premium: WAF + DDoS Standard + bot protection for $35/mo flat
- API Management Consumption: $3.50/million calls — true pay-per-use pricing
- Together: enterprise-grade perimeter + API key tier management at MVP cost
**Alternative considered**: Cloudflare + Kong. Rejected to stay Azure-native for Managed Identity integration.

---

## ADR-008: Managed Identity + Key Vault for all secrets

**Decision**: Every ACA container has a Managed Identity. All secrets accessed via Key Vault. Zero credentials in env vars.
**Rationale**: SOC 2 standard; automatic rotation; audit trail; least privilege via per-service identity.

---

## ADR-009: Metered Stripe billing, no end-user accounts

**Decision**: Billing is subscription + metered via Stripe. API key maps to Stripe customer. **No separate account UI in VAstroChart.**
**Rationale**:
- Stripe Customer Portal handles invoices, payment methods, cancellation
- Fewer screens to build; faster to launch
- Standard pattern (Twilio, SendGrid work this way)
**Implementation**: API Mgmt emits usage events; Stripe webhook validates and reports.

---

## ADR-010: Processor role under GDPR

**Decision**: VAstroChart is a Data Processor; customers are Controllers.
**Rationale**: We never decide "why" the data is processed; we just execute compute on customer instructions. Standard SaaS infrastructure pattern.
**Compliance implications**: Narrow — DPA template, TLS, no PII logging, breach notification only for OUR infrastructure (not for customers' data since none stored).

---

## ADR-011: Output schema is sacred; versioned at URL level

**Decision**: Breaking changes to response shape ship at `/v2/`, `/v3/`. `/v1/` stays stable for 12+ months after any new version launch.
**Rationale**: The schema IS the product. Breaking changes = angry customers rebuilding integrations.
**Implementation**: `docs/09-output-schema.md` is the contract; schema changes require an ADR + migration plan.

---

## ADR-012: Golden regression dataset is non-negotiable

**Decision**: Every endpoint has a golden test set (minimum 10 hand-verified charts). CI blocks on golden regression failures.
**Rationale**: Astrology compute bugs are often subtle (±1' off in a cusp) and hard to spot in review. Golden tests catch regressions before they ship.
**Starting set**: 10 reference charts (various latitudes, including polar edge case; various ayanamsas; various sandhi cases).

---

## ADR-013: One warm replica for the compute service

**Decision**: `vastrochart-compute` ACA app has min replicas = 1, max = 20.
**Rationale**:
- Developers hate cold starts in API responses (2-5s on cold ACA)
- Keeping 1 warm replica costs ~$5-10/mo — rounding error at any revenue level
- Max 20 is plenty for Year 1 traffic

---

## ADR-014: No PII in logs, ever

**Decision**: Request bodies, response bodies, and full API keys are NEVER logged.
**Rationale**: Logs become retained data; retained data is in scope for GDPR; our entire architecture bet is on avoiding that scope.
**Implementation**:
- Pydantic model `__repr__` scrubbed
- FastAPI middleware strips body from span attributes before App Insights export
- API Management logs only key prefix (first 8 chars)
- All compliance includes verification of this in CI

---

## ADR-015: Scope discipline — never add state

**Decision**: Any feature request requiring state (user profiles, chart history, reading storage, favorites, etc.) is **out of scope for VAstroChart.** It belongs in the customer's main app.
**Rationale**: The entire product differentiation and compliance posture depends on stateless-ness. Adding state once breaks the architecture, breaks the DPA model, breaks the pricing (per-compute vs per-user).
**Response pattern**: If asked, suggest the capability belongs in the caller's app layer and offer a pattern (e.g., "cache the chart JSON in your own DB keyed by your user ID").

---

## ADR-016: Dogfood via owner's main app ("AstroApp")

**Decision**: Owner's own main app will be VAstroChart's first customer from Week 4. VAstroChart ships features AstroApp actually needs.
**Rationale**: Having a real caller from day one prevents over-building and validates the API in production.
**Boundary**: AstroApp is a separate project; its scope stays out of VAstroChart's docs.

---

## ADR-017: `tz_offset` as a signed string, not a decimal float

**Decision**: Every endpoint and MCP tool takes `tz_offset` as a string like `"+05:30"` / `"-07:00"`, not a decimal float (`5.5`).
**Rationale**: Matches `docs/09-output-schema.md`'s original REST examples; unambiguous sign/format, matches RFC 3339 offset conventions used elsewhere in the schema. `04-mcp-spec.md` and `spec/mcp-tools-schema.json` previously used decimal floats — reconciled to string on 2026-10-10.

---

## ADR-018: Derived MCP tools take computed values, not `chart_hash` / a cache lookup

**Decision**: `get_mudda_dasha`, `get_transit_hits`, `compute_divisional`, and `detect_yogas` no longer accept a `chart_hash`. Each takes the specific already-computed values it needs (e.g. `natal_planets`, `ascendant_sidereal_longitude`, `moon_sidereal_longitude`) as explicit input, sourced from a prior `compute_chart` call. The Redis caching layer described in an earlier draft of `04-mcp-spec.md` is removed entirely.
**Rationale**: `chart_hash` implied a server-side lookup of a previously computed chart, which requires persistence — directly contradicting ADR-002 and ADR-015. Redis caching likewise contradicted ADR-002's own rationale (pyswisseph is already <50ms; no cache tier exists in `03-architecture.md`). This keeps the server fully stateless while still avoiding redundant ephemeris recomputation: the client holds the `compute_chart` output and forwards the relevant slice to whichever derived tool it calls next, in any order or parallelism.
**Trade-off**: Slightly more verbose call signatures (callers pass longitudes instead of a short hash). Acceptable — matches ADR-002's own escape hatch ("if a customer needs cross-request state, they implement it in their main app").

---

## ADR-019: True Node (not Mean Node) for Rahu/Ketu

**Decision**: Rahu is computed from Swiss Ephemeris's `TRUE_NODE`, not `MEAN_NODE`. Ketu = Rahu + 180° as before.
**Rationale**: Mean vs. True Node can differ by up to ~1.5°, enough to flip a K.P. sub-lord at a nakshatra/sub boundary. Since K.P. sub-lord precision is the stated competitive moat (`docs/01-vision.md`), the more astronomically precise True Node is the safer default. `prototypes/chart_compute.py` updated accordingly.
**When to reconsider**: If golden-chart cross-verification against AstroSage/Jagannatha Hora shows those tools default to Mean Node and developer expectations lean that way, revisit — but default stays True Node unless a strong counter-case emerges.

---

## ADR-020: Both house systems always computed, `house_systems` input is advisory only

**Decision**: `/v1/charts/compute` (and the `compute_chart` MCP tool) always compute and return both `whole_sign` and `placidus_kp` houses, regardless of what the caller requests. The `house_systems` input field is kept for forward-compatibility (e.g. a future `/v2/` that supports Koch or Equal houses) but has no effect on the v1 response shape.
**Rationale**: Directly follows ADR-004's own stated rationale — "cheaper to compute both once than two separate calls." Removes an unresolved Day-1 open question (`tasks/week-1-day-by-day.md` Task 1.3) by picking the simpler, already-justified default.
**Trade-off**: None meaningful — ADR-004 already accepted the ~2KB payload cost.

---

## ADR-021: Envelope refinements — `warnings` array, split ephemeris version, universal `request_id` prefix

**Decision**: The response envelope (`docs/09-output-schema.md`) gains a permanent `warnings: []` field (always present, empty by default). `ephemeris.version` is split into `ephemeris.library_version` (pyswisseph) and the existing `ephemeris.data_source` (DE431 etc.). `request_id` uses a single `req_` prefix + ULID on every endpoint, no per-endpoint prefix variants.
**Rationale**: `version` was ambiguous between the Python binding and the ephemeris data file, which version independently — this would've caused real confusion debugging a golden-regression delta tied to a specific dependency bump. `warnings` gives the envelope a place for non-fatal advisories (starting with Placidus polar degeneracy, ADR-022) without overloading `error` (which implies no `data` payload) or silently dropping information. A single `request_id` prefix avoids callers needing a parsing rule.
**Trade-off**: None meaningful — additive fields only, no shape break.

---

## ADR-022: Placidus polar degeneracy — `null` + warning, not a hard error

**Decision**: When Placidus cusps are geometrically undefined for the given latitude/date (deep polar cases, roughly beyond 66° latitude depending on time of year), `/v1/charts/compute` (and `compute_chart`) return `houses.placidus_kp: null` and add a `PLACIDUS_DEGENERATE_AT_LATITUDE` entry to the envelope `warnings` array. `houses.whole_sign` is computed and returned normally — it never degenerates since it's purely sign-based.
**Rationale**: ADR-020 commits to always computing both house systems, but Placidus is not always mathematically defined. A hard error would fail the entire request over one house system a polar caller might not even need; silently returning numerically-unstable cusps would violate the project's "no hallucinated precision" principle. `null` + warning lets the rest of the response (which K.P. callers may not need at all at that latitude) stay fully usable.
**Verified (2026-10-12)**: `swe.houses_ex` raises `swisseph.Error` cleanly on Placidus degeneracy — it does not silently return degenerate/zero cusps. Tested at summer solstice noon UT, longitude 10°E: lat 66° still resolves; lat 67°+ raises. Implementation in `apps/vastrochart-compute/src/vastrochart_compute/compute/houses.py` catches this and returns `cusps=None`. Also corrected an initial wrong assumption: `houses_ex` returns a flat 12-element list (index 0 = house 1 = Ascendant), not a 13-element list with index 0 unused.
**When to reconsider**: The exact latitude/date threshold wasn't swept exhaustively (only one date tested) — if golden chart_03 (still pending) hits an edge the single test above didn't cover, revisit.
**Real bug found and fixed (2026-10-12, caught by manual curl smoke test, not unit tests)**: `compute/planets.py`'s `compute_ascendant_longitude` independently called `swe.houses_ex(..., b"P", ...)` just to read `ascmc[0]` (the Ascendant) — at polar latitudes this raised the *same* `swisseph.Error` as the dedicated Placidus-cusps call, taking down the entire request (500, not the intended null+warning) because Whole-Sign houses need the Ascendant too and couldn't get it. Fixed by requesting house system `'W'` (Whole-Sign) instead of `'P'` for this call — verified empirically that `ascmc[0]` is identical across house systems at a normal latitude, and that `'W'`/`'E'` both resolve where `'P'` raises at lat 75°. Lesson: the two `houses_ex` call sites (`planets.py` for Ascendant, `houses.py` for Placidus cusps) looked independent but shared a failure mode that only an end-to-end HTTP test surfaced — `apps/vastrochart-compute/tests/unit/test_houses.py`'s polar test only exercised `houses.py` directly.

---

## ADR-023: Node retrograde/speed are always computed, never hardcoded

**Decision**: `retrograde` for Rahu and Ketu is always derived from actual signed ephemeris speed, never hardcoded `True`. Ketu's `retrograde` and `speed_degrees_per_day` mirror Rahu's exactly (same node, 180° apart, identical rate of change). `speed_degrees_per_day` is signed across all planets (negative = retrograde) rather than an unsigned magnitude paired with a separate boolean.
**Rationale**: Caught while reviewing the schema after ADR-019 (True Node switch): the Mean Node is always retrograde by construction, so a hardcoded `retrograde=True` for Ketu (and an unconditional sign-of-speed check for Rahu) was harmless under Mean Node but becomes a real bug under True Node, which can briefly go stationary/direct. Golden chart #4 ("retrograde Rahu" edge case) exists specifically to catch this — it only has teeth if the compute path actually derives retrograde from speed rather than assuming it. `prototypes/chart_compute.py` fixed accordingly (Ketu now inherits Rahu's computed `retrograde`, not a literal `True`).
**Trade-off**: None — this is a correctness fix, not a scope trade-off.

---

## ADR-024: Public, open-core repo from Day 2 — not held private until launch

**Decision**: `vastrochart` is a public GitHub repository from scaffolding onward, not kept private until launch. This also settles ADR-001's open AGPL question: we comply via the "publish source" path, not the commercial Swiss Ephemeris license — the repo being public from day one makes that path trivial rather than a separate step to remember at launch.
**Rationale**: The owner's own AstroApp (main app, separate project) is where the real differentiated product logic lives — interpretation, narrative, UX, business logic. VAstroChart is pure positional/structural compute; there's little competitive downside to the compute engine itself being visible, and `docs/01-vision.md`'s own marketing plan already called for an "open-source MCP client" and a "downloadable golden chart library" to build developer trust. Going public from Day 2 is consistent with that positioning rather than deferred to launch.
**Trade-off**: None significant — no proprietary business logic (pricing, billing, customer data) lives in this repo; that stays in Key Vault/Stripe/the main app.

---

## ADR-025: Full nine-value dignity enum, computed via Panchadha Maitri

**Decision**: `dignity` is a 9-value enum: `exalted | moolatrikona | own | great_friend | friend | neutral | enemy | great_enemy | debilitated`. The five relationship values (`great_friend`/`friend`/`neutral`/`enemy`/`great_enemy`) are computed as the classical **Panchadha Maitri** (five-fold compound relationship): **Naisargika Maitri** (fixed natural friendship table, one planet to another, from BPHS) combined with **Tatkalika Maitri** (temporary friendship — planets 2nd/3rd/4th/10th/11th/12th from each other are temporary friends, else temporary enemies), compounded per the standard table (temporal is binary friend/enemy, natural is friend/neutral/enemy): natural-friend + temporal-friend → great_friend; natural-friend + temporal-enemy → neutral; natural-neutral + temporal-friend → friend; natural-neutral + temporal-enemy → enemy; natural-enemy + temporal-friend → neutral; natural-enemy + temporal-enemy → great_enemy. (An earlier draft of this ADR had this table wrong — corrected 2026-10-12 before implementation, see `apps/vastrochart-compute/src/vastrochart_compute/compute/dignity.py`.)
**Rationale**: Golden-data review (private charts RAK/RIT/SIM) surfaced that the original 6-value enum had no slot for "Friendly," which every cross-checked source tool actually reports. A single `friendly` patch would have been a step backward from classical correctness — the real five-tier relationship scale is standard Jyotish and other tools collapse it to 3 buckets for display, not because the finer grades don't exist.
**Golden-data validation rule**: since source tools (AstroSage) report only 3 collapsed buckets (Friendly/Neutral/Enemy), golden regression checks dignity by **bucket match**, not exact value: `great_friend` or `friend` must match a source `"Friendly"`; `enemy` or `great_enemy` must match a source `"Enemy"`. This is a comparator rule in the test harness, not a schema simplification — the API itself always returns the full 9-value precision.
**Open caveat, not yet verified**: whether AstroSage's 3-bucket "Relation" column reflects the full Panchadha (natural + temporary) compound relationship, or natural friendship alone, is an assumption — most Vedic software does show the compound form in a report like this, but it hasn't been confirmed against AstroSage's own documentation. Revisit if a golden dignity bucket-check fails unexpectedly against a compound-relationship computation.
**Implementation note**: dignity now requires every other planet's current position (for Tatkalika Maitri), not just the sign a planet occupies — more involved than a flat per-sign-lord lookup. See `docs/02-domain-knowledge.md`.

---

## ADR-026: Ephemeris range handling — verified bounds, generic request-error code

**Decision**: Three related additions, all empirically verified against the live library (2026-10-12):
1. **`DATE_OUT_OF_EPHEMERIS_RANGE`** is raised only when a date falls outside Moshier's own usable range (verified: -3001-02-03 to 3003-04-29) — not whenever it falls outside whichever high-precision files happen to be loaded. `compute/exceptions.py`'s `EphemerisRangeError` is raised by `compute/planets.py` when `swe.calc_ut` itself fails, and translated to this error code at the route layer.
2. **`EPHEMERIS_LOW_PRECISION_FALLBACK`** (new warning code) covers the narrower case: date is within Moshier's range but outside the currently-loaded Swiss Ephemeris files (today: ~1800-2399 CE, per `apps/vastrochart-compute/ephemeris/NOTE.md`) — request still succeeds, with lower-precision positions and `ephemeris.data_source: "moshier_analytical"` in the envelope instead of `"DE431"`.
3. **`INVALID_REQUEST`** (new error code) is the generic fallback when a Pydantic validation failure doesn't map to one of the specific field-named codes (`INVALID_DATE`, `INVALID_LATITUDE`, etc.) — the committed list had no catch-all, which is a real gap once an actual validating endpoint exists.

**Rationale**: `houses_ex` (ascendant/cusps) was verified to never fail for date-range reasons at all — it's analytical, not file-dependent — so only `calc_ut` needed this handling. Distinguishing "truly out of range" (error) from "out of *loaded-file* range" (warning, degraded but usable) matters because our currently-bundled files are a deliberately narrow 3-file subset (ADR for the full "DE431 compressed subset" range is still open in `docs/06-roadmap.md`) — treating every out-of-file-range date as a hard error would reject requests the engine can actually answer, just less precisely.
**Verification method**: `swe.calc_ut`/`swe.houses_ex` called directly at increasing distance from year 0 in both directions, with and without `FLG_MOSEPH` forced, to isolate the file-boundary case from Moshier's own genuine limit.
**Trade-off**: `INVALID_REQUEST` widens the committed error-code list beyond what was originally specified; necessary once real request validation exists; documented here rather than added silently.

---

## ADR-027: `node_type` request parameter — True vs Mean Rahu/Ketu

**Decision**: `/v1/charts/compute` (and the `compute_chart` MCP tool) accept an optional `node_type: "true" | "mean"`, default `"true"` (matching ADR-019). Rahu is computed from whichever node type is requested; Ketu always mirrors Rahu + 180°, same retrograde state, regardless.
**Rationale**: True vs Mean Node is a genuine, recognized methodological split — different schools and different tools legitimately default differently (we default True per ADR-019's K.P.-precision argument; AstroSage, used for our golden charts, defaults Mean). This is not the same category of problem as the Jupiter/Saturn delta in `docs/known-reference-tool-deltas.md` (an unexplained precision gap with no known "right" answer) — node type has two well-defined, both-correct answers, so exposing it as a parameter is the right fix rather than picking one and hiding the other.
**Confirms a prior hypothesis**: running all three private golden charts with `node_type="mean"` closes the Rahu/Ketu delta from 64-100 arcminutes down to under 0.3 arcminutes against AstroSage — decisively confirming AstroSage used Mean Node, not an ephemeris discrepancy. `docs/known-reference-tool-deltas.md` updated accordingly (no longer "unconfirmed").
**Implementation**: `compute/constants.py`'s `PLANET_IDS` no longer includes Rahu (whose swe id now depends on `node_type`); a new `NODE_IDS` map holds both. `compute/planets.py`, `compute/chart.py`, `models/chart.py`, and `routes/charts.py` all thread `node_type` through.

---

## ADR-028: Graha drishti, nakshatra_distribution, and K.P. cuspal interlink implementation

**Decision**: Implements the three remaining locked-schema fields for `/v1/charts/compute`: `nakshatra_distribution`, `aspects.vedic_graha_drishti`, `houses.whole_sign[].aspected_by`, and `aspects.kp_cuspal`. Several implementation choices weren't fully pinned by the schema doc and are recorded here:
- **Rahu/Ketu aspect convention**: nodes get the universal 7th-house aspect only, not Mars/Jupiter/Saturn-style special aspects. Classical texts disagree on whether/how nodes cast aspects at all; treating them like the 5 non-special-aspect grahas is a defensible, commonly-used convention, not an asserted classical fact (`compute/aspects.py` docstring flags this explicitly).
- **`aspect_type` label convention**: `"7th"` for the universal aspect; `"{n}th_{m}th"` (e.g. `"4th_8th"`) for a special-aspect planet's pair, used for *either* house in the pair (the label names the rule, not which specific house fired) — matches the one example already in `docs/09-output-schema.md`.
- **K.P. cuspal interlink rule**: a cusp's `interlinked_houses` = the union of (a) houses whose Placidus cusp sign the cuspal sub-lord rules, and (b) the Placidus house the sub-lord planet currently occupies. Standard K.P. cuspal sub-lord significator technique.
- **Correction to ADR-021's wording**: "`houses.whole_sign[].aspected_by` is always derived from `aspects.vedic_graha_drishti`" was imprecise — `vedic_graha_drishti` only records aspects landing on an *occupied* house (a planet or Lagna target), so an aspected-but-empty house would be invisible if `aspected_by` were literally derived from that filtered list. Both are instead built from one shared function, `compute/aspects.py`'s `aspected_houses(house, planet)`, so they can't drift apart — `aspected_by` is independent of occupancy by design.
**Verification**: 7 new unit tests for `compute/aspects.py` (including the classical mutual-7th-aspect sanity check) and 5 for `nakshatra_distribution`; live HTTP smoke test cross-checked a real cuspal interlink result (`[8,9,10]`) by hand against the underlying sign-lordship and occupancy data. 54/54 tests passing.

---

## ADR-029: Vimshottari dasha implementation (`/v1/dasha`)

**Decision**: Implements balance-at-birth, the 9-entry mahadasha_sequence, and nested MD/AD/PD/Sookshma/Prana active-at-date lookup, per `docs/09-output-schema.md`. Key implementation points:
- **Shared segment math**: extracted `compute/vimshottari.py` (`proportion_segments`/`locate_segment`, exact `fractions.Fraction` arithmetic) out of `compute/kp_sublord.py` so K.P. sub-lord and dasha use one proportioning implementation, not two that could silently diverge. Refactor verified behavior-identical against all existing tests before building on it.
- **Period length**: 1 year = 365.25 days exactly for all real date arithmetic, per the project's own starter-prompt convention.
- **`balance_formatted`'s Y/M/D convention**: decimal-year × 12 months, 30-day leftover, carrying 30d→1m and 12m→1y. Validated against golden data (lord matches exactly in all 3 charts; day-level deltas consistent with already-known small Moon-longitude noise, not a new discrepancy) — see `docs/known-reference-tool-deltas.md`.
- **A real bug caught by the golden/synthetic test suite, not written correctly the first time**: the 9-entry `mahadasha_sequence` sums to *less* than 120 years whenever the Moon isn't exactly at its nakshatra's start (it's short by the natal lord's pre-birth-elapsed portion) — only exactly 120 in the degenerate case. My first wraparound implementation for `as_of_date` beyond that used the *truncated* 9-entry total as the repeating cycle length, which is wrong: the true repeating Vimshottari cycle is the full 120 years, and only applies *after* the initial truncated pass completes (every subsequent pass gives each lord its complete fixed years, restarting from the natal lord). Fixed in `compute/dasha.py`'s `_active_md_segment`; added a precise regression test (`test_wraparound_restarts_with_a_full_fresh_natal_lord_period`) plus the looser invariant test that originally caught it.
- **Dates are formatted in the birth location's local time** (the request's `tz_offset`), not UT — matches how dob/tob were specified and how a human reads dasha transition dates.
**Verification**: 15 new unit tests (including the wraparound regression and the `balance_formatted` carry-over edge cases), 1 golden cross-check test against the 3 private fixtures' AstroSage-sourced balance data, 4 HTTP-level tests. 73/73 total passing; confirmed live via curl and in Docker.
**Open, not addressed here**: the >120-years-old wraparound behavior is a reasoned extrapolation, not a verified classical/software convention — flagged in the code, practically near-impossible to hit anyway.

---

## ADR-030: Mudda (Varshaphal) dasha — full-year compression, `as_of_date` added

**Decision**: `/v1/mudda-dasha` compresses the same 120-unit Vimshottari proportional cycle used by natal dasha to span one **full solar year** (~365.25 days), not a 120-real-day sub-slice. 1 Vimshottari-year unit ≈ 365.25/120 ≈ 3.04 days. The birth-nakshatra balance fraction is the same one natal dasha computes, reused unchanged every year — anchored to the solar return instead of birth. An optional `as_of_date` (default today) was added to both the REST input and the `get_mudda_dasha` MCP tool, which originally had neither.
**Rationale**: `docs/02-domain-knowledge.md`'s original wording ("120 days total within a solar year") read literally as a 120-day slice with ~245 uncovered days per year — not a documented or sensible classical design, and not matching how Varshaphal/Mudda dasha actually works (every day of the year has an active lord). Flagged and confirmed with the owner before implementing, rather than guessing silently — getting this wrong would've meant the whole endpoint computed something incorrect with no golden data to catch it. Separately, the original schema had no way to say which day within the solar-return year `mudda_md`/`mudda_ad` describe — a real gap, not a style choice, since without it the response is ambiguous about what moment it represents.
**Implementation**: solar return found via Newton's method on the Sun's sidereal longitude (converges to <1e-6 degrees in practice; Sun's motion is smooth and near-linear over the relevant span). Refactored `compute/dasha.py` to expose `balance_fraction`, `balance_truncated_segments` (now parameterized by `days_per_unit`), and the date-formatting helpers as public functions so `compute/mudda.py` reuses them rather than reimplementing - same pattern as the earlier `compute/vimshottari.py` extraction.
**Verification**: solar return converges to the exact natal Sun longitude (verified to 1e-6 degrees); `MUDDA_DAYS_PER_UNIT * 120 == 365.25` exactly (no gap, by construction); mudda_md lord matches the natal balance lord right at the solar return instant. 9 new tests (5 unit, 5 HTTP - one overlaps), 83/83 total passing, confirmed live via curl and in Docker.

---

## ADR-031: Panchang implementation — Hindu sunrise, Newton's-method transitions, flagged classical tables

**Decision**: `/v1/panchang` computes all five limbs (tithi, nakshatra, nitya_yoga, karana, plus vara and muhurta flags) via exact astronomical root-finding, with classical naming/nature tables kept in a separate module and explicitly confidence-flagged.
- **Sunrise/sunset** use `swe.BIT_HINDU_RISING` (geocentric, disc center, no atmospheric refraction) — verified empirically (2026-10-12) to differ from the library's default civil-sunrise definition (upper limb, with refraction) by several minutes. The classical Hindu definition is the correct one for panchang, not generic Western civil sunrise — this would have been a real, silent correctness bug if left at the default.
- **Transition times** (tithi/nakshatra/nitya_yoga/karana boundary crossings) found via Newton's method on each limb's defining angle (elongation, Moon longitude, Sun+Moon sum, half-elongation respectively) — `compute/boundary_finder.py`, same pattern as the solar-return search (ADR-030).
- **No `ayanamsa` input** (matches the already-locked schema) — panchang is inherently a sidereal/Vedic construct, defaults to Lahiri internally per the project-wide default (ADR-003).
- **Classical lookup tables** (`compute/panchang_tables.py`: 30 tithi names/lords/natures, 27 nitya yoga names/natures, karana names/natures, muhurta weekday-segment tables) are reconstructed from general Jyotish knowledge, **not pulled from a verified live source**. Confidence genuinely varies per table and is noted inline — weekday-segment tables (rahu kaal/yamaganda/gulika) and the 27 yoga names are high-confidence (highly standardized); several tithi deity-lords and fine karana/yoga nature classifications are lower-confidence and should be cross-checked against DrikPanchang (the project's own stated reference, `prompts/starter-prompts.md`) before being treated as authoritative.
**Verification**: strong internal-consistency check, not just unit assertions — 2026-10-10 at the tested coordinates lands exactly on a new moon (tithi 30→1 transition), and independently, the karana sequence for that same window comes out as `Naga(60) → Kimstughna(1, fixed month-start) → Bava(2, first movable)`, exactly matching the classical month-boundary structure with zero special-casing in the compute code. This agreement between two independently-triggered pieces of logic (tithi transition math and karana table structure) is meaningful evidence the wiring is correct, even without an external tool to compare against directly. 22 new unit tests, 3 HTTP tests, 108/108 total passing, confirmed live via curl and in Docker.
**Open follow-up**: cross-verify the flagged classical tables against DrikPanchang for a few reference dates, per the project's own existing verification plan — not done in this session (no live access to that tool).

---

## ADR-032: Hora implementation — Chaldean order unbroken across day/night

**Decision**: `/v1/hora` computes 24 planetary hours — 12 day (sunrise to sunset, equal length) + 12 night (sunset to next sunrise, equal length), with the Chaldean order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon) cycling continuously across all 24, not restarting at sunset. First hora of the day always equals that weekday's own lord. Reuses `compute/sun_events.py`'s Hindu-rising sunrise/sunset (ADR-031) and `compute/dasha.py`'s date-formatting helper.
**Nature classification** (benefic/malefic/neutral) per lord is a well-established classical split. **`best_for`/`avoid_for` activity lists** are lower confidence — a reasonable construction from each planet's classical significations (e.g. Mars → surgery, Saturn → discipline/routine work), not a literally memorized table from one specific hora text. Flagged in code the same way as `compute/panchang_tables.py` (ADR-031) — don't treat as authoritative without cross-checking a classical hora reference.
**Verification**: strong cross-module consistency, not just unit tests — hora #24's end time for a given date/location comes out byte-identical to panchang's independently-computed next-day sunrise for the same inputs (both call `compute/sun_events.py`, but via separate code paths), and hora #1's lord always matches the weekday lord already verified in panchang's own tests. 8 new unit tests, 2 HTTP tests, 118/118 total passing, confirmed live via curl and in Docker.

---

## ADR-033: Divisional charts (vargas) — confidence-graded, D1-D60

**Decision**: `/v1/divisional/{varga}` implements all 9 committed vargas (D1, D9, D10, D12, D16, D20, D24, D30, D60) as a pure transform of D1 sidereal longitudes. A planet's position within its original division "part" is proportionally re-mapped to fill the full 30° of the resulting varga sign (the standard practice), rather than copying the original degree verbatim. Only Whole-Sign houses are computed for a varga (re-derived from the varga's own ascendant, not the natal one) — K.P. sub-lord and Placidus stay D1-only per `docs/02-domain-knowledge.md`.
**Confidence genuinely varies by varga**, flagged per-function in `compute/divisional.py`: **D1/D9/D10/D12** use well-established, consistently-cited starting-sign rules (good confidence). **D16/D20/D24/D30/D60** have real textual variation across Jyotish sources for exact starting-sign rules (D30 additionally for exact degree boundaries) — moderate-to-lower confidence, explicitly flagged rather than presented as uniformly authoritative. D60 in particular uses the simplest "always same sign" rule; some sources describe a direction (forward/reverse) that varies by odd/even sign, not implemented here.
**Process note**: while writing tests, nearly used a specific "well-known" worked example from memory as a test oracle (e.g. "Scorpio's navamsha begins with Taurus") — hand-verifying the arithmetic first showed this specific recollection was likely wrong (the stated *general* rule, which is high-confidence, gives Cancer, not Taurus). Tests instead verify the general rules directly, not potentially-misremembered specific examples — a concrete instance of why this project's "no hallucinations" principle matters even for things that feel confidently recalled.
**Verification**: D1 output cross-checked byte-for-byte against the already-verified natal chart from earlier sessions (ADR-003 default chart) — exact match. 11 unit tests (verifying stated rules, not recalled examples) + 5 HTTP tests, 134/134 total passing, confirmed live and in Docker.
