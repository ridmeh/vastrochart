# 06 — 3-Week MVP Sprint

Target: VAstroChart API live, public, paying customers signing up by end of Week 3.

## Honest Hour Breakdown (per week)

Each "week" below assumes **~30 focused hours**. If you can clear 5 days, it's one calendar week. With day-job context-switching, 1-2 calendar weeks.

---

## Week 1 — Core Compute + Schema Lock

**Goal**: `POST /v1/charts/compute` returning canonical JSON. Golden regression harness in place.

### Hour-by-hour breakdown

| Task | Hours |
|---|---|
| Monorepo setup: `uv` workspace, `apps/vastrochart-compute`, Dockerfile, docker-compose, GitHub repo, basic CI | 3 |
| **Finalize `docs/09-output-schema.md`** — this is the API contract; invest here before any code | 4 |
| pyswisseph wrapper: compute planetary positions, Lagna, cusps for Lahiri + Krishnamurti | 4 |
| K.P. sub-lord algorithm (nested Vimshottari proportions) | 2 |
| House assignment (Whole-Sign + Placidus) | 2 |
| Nakshatra distribution + graha drishti (Vedic aspects) | 2 |
| Pydantic response models matching schema exactly | 3 |
| FastAPI `POST /v1/charts/compute` endpoint | 2 |
| Unit tests for each component (planets, houses, nakshatras, subs) | 4 |
| **Golden dataset: 10 reference charts** — export from AstroSage/Jagannatha Hora, encode expected JSON, verify ±2′ | 10 |
| OpenAPI 3.1 spec auto-generation + review | 2 |
| **Total** | **~38 hours** |

**Deliverable**: `docker compose up` → `curl POST /v1/charts/compute` returns valid canonical JSON. 10/10 golden charts pass.

---

## Week 2 — Dasha + Panchang + Hora + MCP + Divisional + Yogas

**Goal**: All compute endpoints shipped. MCP protocol live alongside REST.

| Task | Hours |
|---|---|
| `/v1/dasha` — Vimshottari MD/AD/PD/Sookshma | 3 |
| `/v1/mudda-dasha` — annual sub-dasha | 2 |
| `/v1/panchang` — tithi/nakshatra/yoga/karana with sunrise-based transitions (verify against DrikPanchang reference) | 5 |
| `/v1/hora` — 24 planetary hours per weekday Chaldean order | 2 |
| `/v1/divisional/{varga}` — D9/D10/D12/D30 | 3 |
| `/v1/yogas` — 50 classical yoga detectors (rule-based) | 6 |
| `/v1/transits` — transit hit computation in date range | 3 |
| **FastMCP integration** — expose same tools over MCP SSE at `/mcp/sse` | 2 |
| Register MCP server with Claude Desktop locally; smoke test | 1 |
| Expand golden dataset to cover each endpoint | 4 |
| **Total** | **~31 hours** |

**Deliverable**: Full endpoint suite live locally. Claude Desktop can call VAstroChart MCP tools.

---

## Week 3 — Deploy, Auth, Billing, Launch

**Goal**: Production live at `api.vastrochart.com`. API keys + metered billing working. Public dev portal.

| Task | Hours |
|---|---|
| Terraform IaC: Resource Group, ACR, ACA Environment, Front Door Premium, API Management Consumption, Key Vault, App Insights | 6 |
| GitHub Actions: build + push to ACR + deploy ACA revision | 2 |
| API Management: import OpenAPI, configure API key tiers (Free/Starter/Pro/Scale), rate limits | 3 |
| Stripe metered subscriptions — API Mgmt usage webhook → Stripe billing | 4 |
| Dev portal: Swagger UI + API key signup + Stripe Checkout | 3 |
| Managed Identity + Key Vault wiring; remove all env-var secrets | 2 |
| Observability: App Insights distributed tracing, PII-scrub pipeline, alerts | 2 |
| Landing page (`vastrochart.com`): one page, pricing, "Get API key" CTA | 3 |
| **Legal: processor DPA template, Terms, Privacy Policy** (template → quick lawyer scan) | 2 |
| Launch post (owner's LinkedIn + 2 niche Jyotish-dev communities) | 1 |
| Open waitlist / direct sign-ups | — |
| **Total** | **~28 hours** |

**Deliverable**: `api.vastrochart.com` live. First Stripe charge by end of week.

---

## Week 4+ — Iterate Based On Developer Feedback

Not part of MVP commitment:
- More yoga detectors (expand from 50 → 150)
- Additional ayanamsas (Raman, Fagan-Bradley)
- Bulk compute endpoint (array of charts in one call)
- Webhook events (push notifications when a user hits a transit)
- Terraform provider for VAstroChart (bragging-rights feature for dev marketing)
- OpenAPI client SDKs auto-generated for Python/TypeScript/Go

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Output schema needs breaking change post-launch | Medium | High | **Invest Week 1 Day 1 in schema design**; ship `/v2/` if needed, keep `/v1/` 12 months |
| K.P. sub-lord bug caught by developer | Medium | High | Golden dataset covers sub-lord edge cases (29°59' sandhi, nakshatra boundaries) |
| ACA cold start affects API UX | Low | Medium | Min replicas = 1 (always warm) |
| Ephemeris data file in Docker image bloats | Low | Low | DE431 subset is only ~15 MB; acceptable |
| Swiss Ephemeris AGPL concern | Low | Medium | Comply by publishing MCP server source, OR buy commercial license (~€400 one-time) |
| Low dev-marketing traction | High | Medium | Owner's existing LinkedIn + content marketing; benchmark posts vs Prokerala |
| Stripe metered billing complexity | Low | Low | Standard pattern; Azure API Mgmt has a native usage-reporting webhook |

---

## Success Metrics

- **Week 3**: Public launch. 10 free-tier signups.
- **Month 2**: 3 paying customers. $150 MRR.
- **Month 6**: 20 paying customers. $2K MRR. Includes 1-2 Scale-tier.
- **Month 12**: 50 paying customers. $6K MRR. Break-even on all infra + legal + minimal founder cost.

---

## Open Questions To Resolve Before Week 1

1. **Domain**: `vastrochart.com` available? Backup: `vastrochart.io`, `vastrochart.dev`?
2. **Repo visibility**: Private GitHub during Week 1-2, public (open-core) at launch?
3. **Swiss Ephemeris licensing**: Comply with AGPL (publish source) OR buy commercial? (~€400)
4. **Stripe account**: Personal or form an LLC first? (US LLC takes 1-2 weeks; could ship on personal Stripe, migrate later)
5. **Legal entity decision**: US LLC vs India Pvt Ltd vs sole-prop launch

---

## Dogfood Contract

Owner's AstroApp (main app, separate project) will be the first VAstroChart customer. VAstroChart ships only features AstroApp needs. This prevents over-building and ensures the API has at least one real caller from Week 4.
