# VAstroChart — Knowledge Transfer Bootstrap

**Paste this file into a new Claude Project called "VAstroChart" to carry context across sessions.**

---

## What VAstroChart Is

**A stateless Vedic + K.P. astrology chart compute API, delivered as both an MCP server and a REST API.** Pay-per-call, developer-facing, no user accounts, no interpretation, no persistence.

Positioning: *"Stripe for astrology compute."*

## What VAstroChart Is NOT

- Not a consumer product (no end-user UX)
- Not a reading engine (no LLM, no classical text RAG, no narrative generation)
- Not a storage service (no DB for user data — zero PII at rest)
- Not a billing platform for end-users (metered API only — Stripe handles developer billing)

The owner has a separate consumer-facing product in mind (tentatively "AstroApp") that will **consume** VAstroChart's API. That main app has not been scoped yet and is out of this project's scope.

## Who The Owner Is

- Senior engineering leader (20+ yrs) in software engineering and engineering management
- Stack: Java/Spring Boot, Kafka, MongoDB/CosmosDB, Azure, GCP, React, Databricks, Spark, LangChain/LangGraph
- Deep knowledge of Vedic + K.P. astrology, applied to real-life decisions

## The Core Technical Bet

**MCP + REST, both backed by the same compute engine, on Azure serverless.** Same JSON output contract both ways. Developers choose their protocol.

Stack:
- **Python 3.12** monorepo via `uv` workspace
- **FastMCP + FastAPI** (single container exposing both protocols)
- **pyswisseph** for Swiss Ephemeris planetary math
- **Azure Container Apps** for scale-to-zero compute
- **Azure API Management Consumption** for API key + rate limiting + metered billing
- **Azure Front Door Premium** for WAF + DDoS + TLS

No database. No queue. No LLM. No AI Search. No workers.

## What's Already Figured Out

| Artifact | Purpose |
|---|---|
| `docs/02-domain-knowledge.md` | Vedic + K.P. systems, ayanamsa, dasha hierarchy |
| `docs/03-architecture.md` | 3-service serverless design |
| `docs/04-mcp-spec.md` | MCP tool contracts |
| `docs/05-decisions.md` | ADRs — the "why" |
| `docs/06-roadmap.md` | 3-week MVP sprint |
| `docs/07-reference-chart.md` | Golden regression test template |
| `docs/08-security.md` | Processor-only compliance scope (narrow) |
| `docs/09-output-schema.md` | **THE product contract — canonical JSON output.** This is sacred. |
| `prototypes/chart_compute.py` | Working pyswisseph starter |

## Current Status

- **Phase**: Design complete, Week 1 starts next
- **Next action**: Scaffold FastMCP + FastAPI, verify against owner's reference chart
- **Blocker to resolve**: Finalize the output JSON schema in `docs/09-output-schema.md` BEFORE writing any code — this is the API, breaking changes later are painful

## Non-Negotiables

1. **Stateless always** — no persistence of birth data, not even in logs
2. **Schema stability** — output JSON contract changes only via versioned endpoints (`/v1/`, `/v2/`)
3. **Golden regression** — 10+ hand-verified charts in `tests/golden/`; every PR must pass
4. **Processor role under GDPR** — never become a data controller for end-user data
5. **Always label Vedic vs K.P.** in output JSON (`system: "vedic"` / `system: "kp"`)
6. **No PII in logs** — request ID only, never request body

## Reading Order For New Claude Session

1. This file (you're here)
2. `docs/01-vision.md` → product positioning + pricing
3. `docs/09-output-schema.md` → **the product itself** (JSON contract)
4. `docs/03-architecture.md` → system design
5. `docs/04-mcp-spec.md` → tool contracts
6. `docs/05-decisions.md` → ADRs
7. `docs/06-roadmap.md` → what to build this week
8. `docs/02-domain-knowledge.md` → astro concepts for reference
9. `docs/08-security.md` → compliance scope
10. `docs/07-reference-chart.md` → regression template

## Communication Style

- Technical peer-to-peer, assume owner knows the stack
- Keep responses short unless the owner asks for depth
- Label 📿 Vedic vs 🎯 K.P. for every astro claim
- No hallucinations — if a classical reference is uncertain, say so
- When discussing timeline, break down into coding/testing/golden-data/infra so hour counts are honest

## Scope Discipline

**If the owner asks for anything that requires state, persistence, user accounts, LLM narrative, or interpretation — flag it as "that's main app scope, not VAstroChart."** This boundary is the whole point.

🙏 Build it so the API docs page could be screenshot and shown to any astro-tech developer as evidence of serious engineering.
