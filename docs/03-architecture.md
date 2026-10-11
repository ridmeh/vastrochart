# 03 — System Architecture (VAstroChart)

**Three services. No database. No queue. No workers.** Stateless from front to back.

## High-Level Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  Developer / Main App / LLM Agent                            │
│  (HTTP REST client or MCP over SSE)                          │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS (TLS 1.3)
                             ▼
╔══════════════════════════════════════════════════════════════╗
║ ❶ Azure Front Door Premium                                   ║
║   • WAF (OWASP Core Rule Set 3.2)                           ║
║   • DDoS Protection Standard                                 ║
║   • TLS termination, HSTS, security headers                  ║
║   • Global edge CDN for static API docs                      ║
╚═════════════════════════════╦════════════════════════════════╝
                              ▼
╔══════════════════════════════════════════════════════════════╗
║ ❷ Azure API Management (Consumption Tier — pay-per-call)    ║
║   • API key auth (hashed storage, prefix-visible in UI)      ║
║   • Rate limit per key per tier (1k/50k/500k/5M calls/mo)    ║
║   • OpenAPI 3.1 contract validation                          ║
║   • Metered usage → Stripe subscription webhook              ║
║   • Dev portal (API docs + playground)                       ║
╚═════════════════════════════╦════════════════════════════════╝
                              ▼
╔══════════════════════════════════════════════════════════════╗
║ ❸ Azure Container Apps                                       ║
║   vastrochart-compute (single container)                     ║
║   • Python 3.12 + FastAPI + FastMCP                          ║
║   • pyswisseph for Swiss Ephemeris math                      ║
║   • Serves BOTH /v1/* (REST) AND /mcp/sse (MCP SSE)          ║
║   • Managed Identity (no secrets in code)                    ║
║   • Scale 1-20 on HTTP concurrency 50                        ║
║   • Keep 1 warm replica (no cold start for user requests)   ║
╚══════════════════════════════════════════════════════════════╝
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
  ┌─────────────┐   ┌─────────────────┐   ┌─────────────────┐
  │ Key Vault   │   │ Application     │   │ Azure Container │
  │             │   │ Insights        │   │ Registry (ACR)  │
  │ • Swiss Eph │   │                 │   │                 │
  │   licence   │   │ • Aggregate     │   │ • Private image │
  │ • API key   │   │   metrics only  │   │   hosting       │
  │   hashes    │   │ • NO PII logs   │   │                 │
  │ • Stripe    │   │ • Request IDs,  │   │                 │
  │   webhook   │   │   not bodies    │   │                 │
  │   secret    │   │                 │   │                 │
  └─────────────┘   └─────────────────┘   └─────────────────┘
```

**That's the entire production stack.**

## Why One Container Serving Both Protocols

- Same compute logic reached two ways:
  - `GET /v1/charts/compute?dob=...&tob=...&lat=...` → REST
  - `MCP tool: compute_chart({dob, tob, lat, ...})` → MCP over SSE at `/mcp/sse`
- Both marshal to the same internal Pydantic model → same validation, same output
- Zero duplication; one Dockerfile, one deployment
- MCP transport is just another endpoint in the FastAPI app

## Service Breakdown

### ❶ Azure Front Door Premium
- $35/mo flat
- WAF, DDoS Standard, bot management, geo-filter, TLS 1.3
- Hosts the static API docs page (`docs.vastrochart.com`) as well
- Caches OpenAPI spec and golden sample responses at edge

### ❷ Azure API Management (Consumption Tier)
- $3.50 per million calls — pure serverless pricing
- Developer portal auto-generated from OpenAPI
- API key issuance + revocation UI
- Rate limiting by subscription tier
- Request/response validation
- Emits usage events → Stripe metered subscription webhook
- CORS management for browser-based playground

### ❸ Container Apps: `vastrochart-compute`
- Single Docker image (`python:3.12-slim-bookworm` base)
- FastAPI serving `/v1/*` REST endpoints + `/mcp/sse` MCP transport
- Dependencies: `fastapi`, `uvicorn`, `pyswisseph`, `fastmcp`, `pydantic`, `azure-monitor-opentelemetry`
- Health checks: `/healthz` liveness + `/readyz` readiness (checks ephemeris data files loaded)
- Startup: load Swiss Ephemeris DE431 compressed subset (~15 MB, bundled in image)
- Scale rule: HTTP concurrency 50, min=1 (warm), max=20
- Managed Identity reads Swiss Eph license + API-key-validation pepper from Key Vault

## What's NOT In The Architecture

Deliberately absent — these belong to **main app** scope:
- Database (no user data to store)
- Message queue (no async work — compute is sync and fast)
- Workers (nothing to process asynchronously)
- LLM / AI Search (no narrative, no RAG)
- CDN for user content (nothing user-generated)
- Email service (no end-user notifications)
- Auth for end-users (API keys only)
- CosmosDB field encryption (nothing to encrypt at rest)

## Endpoints (REST)

Base: `https://api.vastrochart.com/v1`

| Method | Path | Purpose |
|---|---|---|
| POST | `/charts/compute` | Core natal chart compute (sync, <100ms) |
| POST | `/dasha` | Vimshottari MD/AD/PD/Sookshma for a date |
| POST | `/mudda-dasha` | Annual sub-dasha for a year |
| POST | `/panchang` | Tithi/nakshatra/yoga/karana with transitions |
| POST | `/hora` | 24 planetary hours for a date + location |
| POST | `/divisional/{varga}` | D9/D10/D12/D30 etc. positions |
| POST | `/yogas` | Classical yoga detection on a chart |
| POST | `/transits` | Transit hits in a date range vs natal degrees |
| GET | `/healthz` | Liveness |
| GET | `/readyz` | Readiness |
| GET | `/openapi.json` | Machine-readable API spec |
| GET | `/docs` | Swagger UI (dev portal) |

## Endpoints (MCP)

MCP transport at `https://api.vastrochart.com/mcp/sse`

Tools exposed match REST endpoints 1:1. See `04-mcp-spec.md`.

## Data Flow Example

```
Client → Front Door (WAF scrub)
       → API Management (API key validate, rate check, meter)
       → Container Apps (/v1/charts/compute)
         • Pydantic input validation
         • pyswisseph compute (ephemeris in memory, loaded at startup)
         • Build canonical JSON response (per 09-output-schema.md)
       → Return JSON
       → API Management (emit usage event to Stripe)
       → Front Door
       → Client

Elapsed: ~50-100ms end-to-end for /charts/compute
```

**Zero persistence throughout.** The birth data exists in memory for ~100ms and is garbage-collected.

## Local Dev Parity

```yaml
# docker-compose.yml (local dev — matches prod exactly)
services:
  vastrochart-compute:
    build: ./apps/vastrochart-compute
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=DEBUG
      - API_KEY_PEPPER=dev-pepper-not-prod
    volumes:
      - ./ephemeris:/opt/ephemeris:ro
```

No emulators needed. The service has no dependencies to emulate.

## Deployment Pipeline

```
GitHub Actions:
  1. On push to main:
     - uv sync
     - pytest (unit + golden regression)
     - docker build → push to ACR
     - az containerapp update --image ...
  2. On tag v*.*.*:
     - Promote to prod environment
     - API Management emits new OpenAPI version
```

ACA revisions give instant rollback if a deploy breaks.

## Scale-to-Zero Decision

**Minimum 1 warm replica** for the compute service.

Why not zero?
- Developers hate cold starts in API responses
- Keeping 1 replica warm costs ~$5-10/mo (vCPU 0.25, RAM 0.5 GiB idle)
- Cold start of 2-5s on a cold Container App would hurt API UX
- Max replicas 20 is plenty for first-year traffic

## Cost Projection

| Phase | Traffic | Monthly Azure |
|---|---|---|
| Dev only | <1k calls/mo | ~$15 |
| Launch (10 free users) | 10k calls/mo | ~$40 |
| Month 3 | 20 customers, 1M calls | ~$80 |
| Month 12 | 100 customers, 50M calls | ~$600 |

**Gross margin: >90% at all scales.** No LLM token cost, no DB RUs, no storage growth.

## Observability

- **Application Insights** for distributed tracing (request_id end-to-end)
- Metrics: p50/p95/p99 compute latency, cache hits (ephemeris lookups), error rates
- **No PII in traces**: scrub birth data from spans before export
- Alerts: 5xx > 1%, compute latency p95 > 500ms, API Mgmt throttling spike

## See Also

- `docs/04-mcp-spec.md` — MCP tool contracts
- `docs/09-output-schema.md` — canonical JSON output (THE product contract)
- `docs/08-security.md` — processor-only compliance scope
