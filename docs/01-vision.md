# 01 — Product Vision

## The Problem

Astro-tech developers need accurate Vedic + K.P. chart compute. Their options today:

| Option | Problem |
|---|---|
| **Build on Swiss Ephemeris themselves** | 6-12 months of work; most teams don't have the astronomy + Jyotish expertise to do it right (K.P. sub-lord precision, ayanamsa handling, divisional charts, panchang transition times) |
| **Prokerala / AstroSage / third-party APIs** | Closed APIs, inconsistent K.P. precision, limited divisional charts, no MCP support, pricing often opaque, Western astrology mixed in |
| **ChatGPT / Claude direct** | Hallucinates planetary positions. Unusable for anything serious. |

**Gap**: A rigorous, developer-friendly, pay-per-call Vedic chart API with proper K.P. sub-lord precision and clean JSON output.

## The Solution

**VAstroChart**: Stateless chart compute via **MCP + REST**. Developers point their main app or LLM agent at us; we return canonical JSON. They do interpretation, storage, UX.

## Who Pays

| Persona | Pain | Price point |
|---|---|---|
| **Astro-tech indie developer** building a side-project app | Doesn't want to learn Swiss Ephemeris + K.P. theory | $49-199/mo |
| **Established astro-SaaS** currently rolling their own compute (buggy) | Wants to delete their compute code and focus on UX | $199-999/mo |
| **AI agent builder** adding astrology tool to their LangChain stack | Wants an MCP-native tool that just works | $49-199/mo |
| **The owner's own main app** ("AstroApp") | Needs reliable compute without re-building | Internal / unlimited |
| **Researchers / data scientists** doing dasha studies, transit backtests | Needs programmatic bulk access | $199+ |

## Monetization — Metered API Only

| Tier | Price | Calls/mo | Notes |
|---|---|---|---|
| **Free** | $0 | 1,000 | Dev tier, rate-limited, API docs sign-up |
| **Starter** | $49/mo | 50,000 | Indie developers |
| **Pro** | $199/mo | 500,000 | Established apps |
| **Scale** | $999/mo | 5,000,000 | High-volume + SLA + priority support |
| **Enterprise** | Custom | Unlimited | White-label, dedicated DPA, custom SLA |

**No end-user subscriptions.** The customer is always another developer or app.

## Target Numbers (12-month)

- 50 paying API customers × avg $120/mo = $72K ARR
- Owner's own main app traffic (free, internal)
- **Year-1 target: $72K ARR** from API alone (break-even infra at ~20 customers)

Smaller top-line than a consumer SaaS, but:
- **>90% gross margin** (pure compute, no LLM token cost)
- **Lower CAC** (developer marketing is content-driven, not paid acquisition)
- **Lower support cost** (devs self-serve from API docs)
- **Compounding** (customers using VAstroChart in their apps = permanent compute volume)

## Why This Can Work

1. **Nobody owns this niche cleanly**. Prokerala has it but with closed-source Western-mixed vibes and no MCP support. We're the proper serious infrastructure play.
2. **K.P. sub-lord precision is the moat**. Most APIs get this wrong at edge degrees. We don't.
3. **MCP-native matters more every month**. As LLM agents proliferate, MCP tools win the integration race.
4. **Owner has credibility** — the Jyotish knowledge is real, not marketed. Developer customers trust that.
5. **AstroApp as anchor customer** — the owner's own main app validates the API in production from Week 4.

## What We Will Not Do

- End-user accounts, auth, consumer billing
- Reading narratives, interpretations, "what does this mean" layer
- Western astrology (Vedic + K.P. only — focus is the moat)
- Compatibility / match-making computations (not core; add later if demand)
- Gemstone / remedy recommendations (interpretation-adjacent; out of scope)
- Birth-time rectification (interpretation-adjacent; may add as a utility endpoint later)

## Content & Marketing

- **Technical blog**: posts on K.P. sub-lord math, ayanamsa drift, Swiss Ephemeris quirks (owner's existing credibility + technical rigor)
- **Open-source MCP client** for other LLM frameworks (LangChain tool, OpenAI function spec, Anthropic tool spec)
- **API docs page** with live playground (every developer landing page needs this)
- **Golden chart library** downloadable (free, builds trust)
- **Comparison benchmarks** vs Prokerala/AstroSage on edge cases (performance + accuracy)
