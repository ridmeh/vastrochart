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
**Open verification item**: The exact failure signal from `swe.houses_ex` for this case (return code vs exception vs silently-wrong values) needs confirming empirically against `tests/golden/chart_03_polar_latitude.json` during implementation — not yet verified against the live library.
**When to reconsider**: If pyswisseph's actual behavior at the boundary turns out to be a smooth degradation rather than a clean failure signal, the detection threshold/logic in this ADR will need revising once empirically tested.

---

## ADR-023: Node retrograde/speed are always computed, never hardcoded

**Decision**: `retrograde` for Rahu and Ketu is always derived from actual signed ephemeris speed, never hardcoded `True`. Ketu's `retrograde` and `speed_degrees_per_day` mirror Rahu's exactly (same node, 180° apart, identical rate of change). `speed_degrees_per_day` is signed across all planets (negative = retrograde) rather than an unsigned magnitude paired with a separate boolean.
**Rationale**: Caught while reviewing the schema after ADR-019 (True Node switch): the Mean Node is always retrograde by construction, so a hardcoded `retrograde=True` for Ketu (and an unconditional sign-of-speed check for Rahu) was harmless under Mean Node but becomes a real bug under True Node, which can briefly go stationary/direct. Golden chart #4 ("retrograde Rahu" edge case) exists specifically to catch this — it only has teeth if the compute path actually derives retrograde from speed rather than assuming it. `prototypes/chart_compute.py` fixed accordingly (Ketu now inherits Rahu's computed `retrograde`, not a literal `True`).
**Trade-off**: None — this is a correctness fix, not a scope trade-off.
