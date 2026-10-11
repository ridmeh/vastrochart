# CLAUDE.md

**Read this first every session.** This is the project operating manual for Claude Code / Cursor / any AI coding agent.

---

## Project: VAstroChart

Stateless Vedic + K.P. astrology chart compute API. MCP + REST. **"Stripe for astrology compute."**

- Owner uses this on their own charts first (dogfood principle)
- First real customer is the owner's main app (a separate future project called "AstroApp")
- Monetization: metered API, developer-facing, Stripe billing

---

## 🚨 Scope Discipline — DO NOT CROSS THESE LINES

| ❌ Never add | ✅ Always honor |
|---|---|
| User accounts, profiles, auth for end-users | API keys only |
| Database for end-user data (CosmosDB, Postgres, SQLite) | Pure in-memory compute |
| Reading engine, narrative generation, LLM calls | Pure positional/structural output |
| Classical text RAG, Qdrant, AI Search | None — belongs in main app, not here |
| Deliverable workers (Excel/Word/PDF generation) | JSON only |
| Any persistence of birth data, including logs | TLS in flight, GC after response |
| Breaking changes to `/v1/*` response shape | Ship at `/v2/` instead |

**If asked for any of the above, respond**: *"That's main app scope, not VAstroChart. VAstroChart stays stateless compute."*

---

## 🔁 Golden Rules

1. **The output schema (`docs/09-output-schema.md`) is sacred.** Lock it in Day 1 before any coding. All downstream work derives from it.
2. **Golden regression blocks merge.** `tests/golden/*.json` must pass before any PR merges.
3. **Label 📿 Vedic vs 🎯 K.P.** everywhere — in docs, in API responses, in logs, in code comments.
4. **No PII in logs.** Request body never logged. Request ID only.
5. **Pure functions wherever possible.** Chart compute, dasha, panchang, hora are all stateless pure functions. Keep them that way.
6. **Pydantic for every I/O boundary.** Input validation + output serialization both use Pydantic v2 models.

---

## 🛠️ Build & Test Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest                                                                   # all tests (all workspace members)
uv run --package vastrochart-compute pytest apps/vastrochart-compute/tests/golden/   # golden regression only
uv run --package vastrochart-compute pytest -k "test_kp_sublord"               # specific test

# Local development
docker compose up                   # full stack locally, matches prod image
uv run --package vastrochart-compute uvicorn vastrochart_compute.main:app --reload --port 8080

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check
uv run --package vastrochart-compute mypy apps/vastrochart-compute/src

# Build Docker image
docker build -t vastrochart-compute:dev apps/vastrochart-compute/
```

---

## 📁 Repo Layout (Target)

```
vastrochart/
├── CLAUDE.md                       ← you're reading this
├── README.md                       Public-facing readme
├── pyproject.toml                  uv workspace root
├── docker-compose.yml              Local dev
├── apps/
│   └── vastrochart-compute/        The one service
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── src/
│       │   ├── main.py             FastAPI + FastMCP app factory
│       │   ├── compute/
│       │   │   ├── planets.py      Sidereal planet positions
│       │   │   ├── houses.py       Whole-Sign + Placidus
│       │   │   ├── nakshatras.py   27 nakshatras + padas
│       │   │   ├── kp_sublord.py   K.P. sub-lord algorithm (the moat)
│       │   │   ├── dasha.py        Vimshottari hierarchy
│       │   │   ├── mudda.py        Annual sub-dasha
│       │   │   ├── panchang.py     Five limbs with transitions
│       │   │   ├── hora.py         Planetary hours
│       │   │   ├── vargas.py       Divisional charts
│       │   │   ├── yogas.py        Classical yoga detectors
│       │   │   └── transits.py     Transit hit search
│       │   ├── models/             Pydantic models matching output schema
│       │   ├── routes/             FastAPI endpoints
│       │   └── mcp/                FastMCP tool exposition
│       └── tests/
│           ├── unit/
│           └── golden/             Hand-verified reference charts
├── tools/                          Developer tooling (NOT shipped)
│   ├── image-to-golden/            Claude vision → JSON for test fixtures
│   └── golden-validator/           Validation harness for golden fixtures
├── docs/                           Project documentation (read these!)
├── spec/                           API schemas
├── prototypes/                     Starter code (chart_compute.py)
├── tasks/                          Day-by-day task breakdown
├── prompts/                        Prepared prompts for key phases
└── infra/                          Terraform (added Week 3)
```

---

## 📚 Where To Find Context

For deeper context, read these in order:
1. `README.md` — public positioning
2. `00-KNOWLEDGE-TRANSFER.md` — full session bootstrap
3. `docs/09-output-schema.md` — **THE product contract**
4. `docs/03-architecture.md` — system design
5. `docs/04-mcp-spec.md` — MCP tool contracts
6. `docs/05-decisions.md` — 16 ADRs explaining "why"
7. `docs/06-roadmap.md` — 3-week sprint plan
8. `docs/08-security.md` — processor-only compliance scope
9. `docs/02-domain-knowledge.md` — astro concepts reference
10. `tasks/week-1-day-by-day.md` — granular daily task list

For prepared starter prompts for key phases: `prompts/starter-prompts.md`

---

## 🎯 Coding Conventions

- **Python 3.12+** (match pin in `pyproject.toml`)
- **Type hints required** everywhere; `mypy --strict` passes
- **Pydantic v2** models for every I/O boundary
- **FastAPI** for REST, **FastMCP** for MCP transport, both in one app
- **structlog** for logging, with PII-scrubbing processor
- **pytest** for tests, including `pytest-asyncio` for async paths
- **ruff** for lint + format (both in one tool)
- **Function size**: aim for <40 lines; split when it feels crowded
- **Docstrings**: short, state purpose; no need to document types (hints do that)
- **Classical references**: when implementing a yoga or dignity rule, cite the source in a comment (`# BPHS Ch 36 V33`)
- **DMS formatting**: always provide both `_degrees` (decimal) and `_formatted` (DMS string) in output

---

## 🧪 Testing Philosophy

- **Unit tests** for every compute function (planets, houses, sub-lord, dasha, etc.)
- **Golden regression**: 10+ hand-verified reference charts; every endpoint change runs them
- **Property-based tests** where applicable (hypothesis library) — e.g., sum of planet nakshatra arcs = 360°
- **Edge cases documented**: polar lat, retrograde Rahu, sandhi (29°59'), DST transition, pre-1900 dates
- **CI blocks merge** on golden regression failures

---

## 📏 Communication Style For This Project

- Technical peer-to-peer; owner is a senior engineer with 20+ years in Java/Python/Azure
- Keep responses short unless the owner asks for depth
- When discussing timeline, break into coding/testing/golden-data/infra so hour counts are honest
- No hallucinations — if a classical reference is uncertain, say so
- When implementing something non-obvious, write the ADR entry in the same commit (`docs/05-decisions.md`)
- Challenge the owner when scope would compromise the architecture

---

## 🚦 Common Pitfalls To Avoid

| Pitfall | Guard |
|---|---|
| Caching across requests (adds "state") | Use Redis later only for RL counters; never cache compute results in VAstroChart |
| Adding user_id to logs | Log request_id only |
| Letting response shape "evolve" | Any shape change requires `/v2/` endpoint + ADR |
| Hardcoding ayanamsa | Always parametrize; default Lahiri, support Krishnamurti/Raman |
| Mixing systems in output | Every astro claim labeled `system: "vedic"` or `system: "kp"` |
| Forgetting Rahu/Ketu | Nodes are planets in Vedic; always include in output |
| K.P. house = Vedic house | They differ (Whole-Sign vs Placidus); return both separately |
| Rounding too early | Compute at full float precision; round only at output serialization |

---

## 📝 First-Session Checklist

If this is your first session on the project:
1. Read this file completely ✅
2. Read `tasks/week-1-day-by-day.md` to see the current day
3. Read `docs/09-output-schema.md` (the product contract)
4. Confirm the current day's tasks with the owner before coding
5. **Do not code before `docs/09-output-schema.md` is locked** — this is Day 1 Task 1

---

🙏 You are a sharp senior engineer helping another sharp senior engineer. Honesty, scope discipline, and schema stability over everything else.
