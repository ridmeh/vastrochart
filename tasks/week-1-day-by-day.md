# Week 1 — Day-By-Day Task List

Granular breakdown. Each task is small enough to tick off in <2 hours. **Do not skip ahead.** Day 1 schema work must complete before Day 2 coding begins.

> 💡 **For Claude Code**: start the session with *"Read CLAUDE.md and tasks/week-1-day-by-day.md. Which day/task are we on? Start the next unfinished task."*

---

## 🗓️ Day 1 — SCHEMA LOCK (NO CODING)

**Highest leverage day of the entire project. ~6-8 hours.**

- [ ] **Task 1.1** — Read full VAstroChart kit: README, 00-KNOWLEDGE-TRANSFER, docs/01-vision, docs/03-architecture, docs/09-output-schema (30 min)
- [ ] **Task 1.2** — Review `docs/09-output-schema.md` with Claude as sparring partner (2 hr):
  - Challenge every field name — too long? too short? ambiguous?
  - Verify Devanagari + IAST naming consistency
  - Decide: do we return `_formatted` DMS strings OR let caller format? (recommended: return both)
  - Decide: `tz_offset` as "+05:30" string or decimal 5.5? (recommended: string, ISO 8601 compliant)
  - Decide: separate ayanamsa computation visibility in response?
  - Challenge error envelope shape
- [ ] **Task 1.3** — Finalize house system handling (1 hr):
  - Default to `["whole_sign", "placidus_kp"]` or require caller to specify?
  - What if caller requests only `placidus_kp` — do we still compute Lagna?
- [ ] **Task 1.4** — Freeze versioning policy (30 min):
  - `/v1/` baseline
  - `api_version: "1.0.0"` in every response envelope
  - Breaking change policy documented in `docs/05-decisions.md`
- [ ] **Task 1.5** — Create `apps/vastrochart-compute/src/models/` layout plan (1 hr):
  - Draft Pydantic model names (BirthData, PlanetPosition, HouseVedic, HouseKP, etc.) — not code yet, just names
- [ ] **Task 1.6** — Commit `docs/09-output-schema.md` v1.0.0 to the repo as the sealed contract (10 min)

**End of day deliverable**: `docs/09-output-schema.md` tagged v1.0.0. No further changes without ADR + migration plan.

---

## 🗓️ Day 2 — Scaffold + Hello World

**~6 hours.**

- [ ] **Task 2.1** — Initialize `uv` workspace with monorepo layout (30 min):
  ```bash
  uv init --package vastrochart-compute apps/vastrochart-compute
  ```
- [ ] **Task 2.2** — Add core dependencies to `apps/vastrochart-compute/pyproject.toml`:
  - `fastapi>=0.115`
  - `uvicorn[standard]>=0.30`
  - `pyswisseph>=2.10`
  - `fastmcp>=0.2`
  - `pydantic>=2.9`
  - `structlog>=24`
  - `azure-monitor-opentelemetry` (defer until Week 3)
- [ ] **Task 2.3** — Set up `ruff` + `mypy --strict` + `pytest` + `pytest-asyncio` as dev deps
- [ ] **Task 2.4** — Download Swiss Ephemeris DE431 compressed subset (~15 MB) to `apps/vastrochart-compute/ephemeris/`; `.gitattributes` LFS if large; or bundle in Docker
- [ ] **Task 2.5** — Write `src/main.py` with FastAPI app + `GET /healthz` + `GET /readyz` (readyz checks ephemeris data path exists)
- [ ] **Task 2.6** — Write `Dockerfile` (python:3.12-slim-bookworm base, multi-stage, non-root user)
- [ ] **Task 2.7** — Write `docker-compose.yml` for local dev
- [ ] **Task 2.8** — Run `docker compose up`, verify `curl localhost:8080/healthz` returns `{"status":"ok"}`
- [ ] **Task 2.9** — Set up GitHub Actions CI: lint, type-check, test on push

**End of day deliverable**: scaffolded repo with health check passing, CI green.

---

## 🗓️ Day 3 — Core Compute (Planets + Lagna + Nakshatras)

**~8 hours.**

- [ ] **Task 3.1** — Port `prototypes/chart_compute.py` basics into `src/compute/planets.py` (2 hr):
  - Function: `compute_planet_positions(jd, ayanamsa) -> list[PlanetPosition]`
  - All 9 planets (Sun through Rahu), compute Ketu as Rahu+180
  - Return full sidereal longitude, retrograde flag, speed
- [ ] **Task 3.2** — `src/compute/nakshatras.py` — nakshatra + pada + sign + sign_lord lookup (1 hr)
- [ ] **Task 3.3** — `src/compute/dignity.py` — planet dignity (exalted/moolatrikona/own/neutral/enemy/debilitated) (1 hr)
- [ ] **Task 3.4** — `src/compute/houses.py` — Whole-Sign house assignment given Lagna (1 hr)
- [ ] **Task 3.5** — Placidus cusps via `swe.houses_ex(..., b'P', FLG_SIDEREAL)` (1 hr)
- [ ] **Task 3.6** — Pydantic models matching `docs/09-output-schema.md` field by field (2 hr)
- [ ] **Task 3.7** — Unit tests: known position → known sign/nakshatra/pada for each planet

**End of day deliverable**: `compute_planet_positions()` works; unit tests pass.

---

## 🗓️ Day 4 — K.P. Sub-Lord + First API Endpoint + First Golden Chart

**~8 hours. The sub-lord algorithm is the moat — nail it.**

- [ ] **Task 4.1** — `src/compute/kp_sublord.py` — nested Vimshottari proportions within a nakshatra (2 hr):
  - Function: `get_sub_lord(sidereal_longitude: float) -> (nakshatra_lord, sub_lord, sub_sub_lord)`
  - Sub sequence = Vimshottari dasha order starting from nakshatra lord
  - Each sub arc = (lord_vimshottari_years / 120) × 13°20'
  - Sub-sub applies same proportions WITHIN the sub
- [ ] **Task 4.2** — Hand-verify sub-lord computation at sandhi (29°59'50") against classical examples (1 hr)
- [ ] **Task 4.3** — Compose full `/v1/charts/compute` endpoint in `src/routes/charts.py` (1 hr)
- [ ] **Task 4.4** — Export your own reference chart from AstroSage or Jagannatha Hora (1 hr):
  - Save screenshots for later image-to-golden workflow (Week 2)
  - Encode expected JSON manually in `tests/golden/chart_01_reference.json`
  - This file is .gitignore'd from public — private dogfood
- [ ] **Task 4.5** — Write `tests/golden/test_golden_regression.py` harness that compares live output to expected within tolerance (1 hr)
- [ ] **Task 4.6** — `pytest tests/golden/` → must pass (1 hr debugging if deltas appear)
- [ ] **Task 4.7** — Document any discrepancies vs AstroSage in `docs/known-reference-tool-deltas.md` (new file) (1 hr)

**End of day deliverable**: `POST /v1/charts/compute` returning canonical JSON; 1 golden chart passing regression within ±2'.

---

## 🗓️ Day 5 — Edge Cases + Golden Expansion + MCP Transport

**~8 hours.**

- [ ] **Task 5.1** — Add 4 more golden charts covering edge cases (3 hr):
  - Polar latitude (lat > 66°)
  - Southern hemisphere
  - DST boundary birth time
  - Pre-1900 date
- [ ] **Task 5.2** — Fix any bugs discovered through expanded regression (2 hr budget)
- [ ] **Task 5.3** — Wire FastMCP transport at `/mcp/sse` exposing `compute_chart` tool (1 hr):
  - Same Pydantic models reused
  - MCP tool definition pulls from `spec/mcp-tools-schema.json`
- [ ] **Task 5.4** — Register local MCP server with Claude Desktop; smoke test (30 min)
- [ ] **Task 5.5** — Update `docs/05-decisions.md` with any new ADRs from this week (30 min)
- [ ] **Task 5.6** — Write Week 1 retrospective in `docs/retro-week-1.md` — what took longer, what was faster (30 min)

**End of day deliverable**: Core chart compute live via both REST and MCP. 5 golden charts passing. Ready for Week 2 (dasha + panchang + hora).

---

## ✅ Week 1 Done Criteria

- [ ] `docs/09-output-schema.md` v1.0.0 locked
- [ ] `POST /v1/charts/compute` returns full canonical JSON
- [ ] FastMCP server exposes `compute_chart` tool at `/mcp/sse`
- [ ] 5 golden charts in `tests/golden/`, all passing
- [ ] CI green on main branch
- [ ] `docker compose up` runs the stack locally
- [ ] Owner has registered local MCP in Claude Desktop and verified against own chart

If any item above is NOT done, do NOT start Week 2.

---

## 📊 Tracking

Keep this file as the source of truth. Check items off (change `[ ]` to `[x]`) as you complete them. Commit after each session so you can see weekly velocity.

Honest expectation: with context-switching, Week 1 ≈ 7-10 calendar days. Full focus ≈ 5 days.
