# VAstroChart

**Stateless Vedic + K.P. astrology chart compute API. MCP + REST. No state. No LLM. No interpretation.**

Input: birth data (DOB, TOB, lat, lon, ayanamsa).
Output: canonical JSON — planets, houses, nakshatras, sub-lords, dasha, panchang, yogas.

**Positioning**: "Stripe for astrology compute." Developers and apps consume the API; VAstroChart never stores or interprets. Interpretation, user accounts, reading narratives, deliverables all live in the **main app layer** (a separate product — tentatively "AstroApp" — not scoped here).

Started: October 2026

---

## 📂 Repo Map

```
VAstroChart/
├── README.md                   ← you are here
├── 00-KNOWLEDGE-TRANSFER.md    ← paste into a new Claude Project to bootstrap context
├── docs/
│   ├── 01-vision.md            API-as-a-service positioning, pricing
│   ├── 02-domain-knowledge.md  Astro concepts the compute engine must get right
│   ├── 03-architecture.md      Stateless serverless on Azure (3 services, no DB)
│   ├── 04-mcp-spec.md          MCP tool contracts
│   ├── 05-decisions.md         Architecture Decision Records
│   ├── 06-roadmap.md           3-week sprint to launch
│   ├── 07-reference-chart.md   Golden regression test case (template)
│   ├── 08-security.md          Processor-only compliance (narrow surface)
│   └── 09-output-schema.md     THE product contract — canonical JSON output
├── spec/
│   └── mcp-tools-schema.json   MCP tool JSON schemas
└── prototypes/
    └── chart_compute.py        pyswisseph starter — runs today
```

---

## 🎯 One-Line Summary

**Pay-per-call astrology chart compute API** on Azure serverless. Developer-facing. Zero PII storage. Three services total: Front Door → API Management → Container Apps. Launches in 3 weeks.

**Cost: ~$15/mo dev · ~$80/mo at 1M calls · ~$600/mo at 50M calls · >90% gross margin**

---

## 🚫 What VAstroChart Is NOT

- Not a consumer product
- Not a reading engine (no LLM, no classical corpus, no narrative)
- Not a storage service (no user accounts, no chart history)
- Not a billing platform for end-users (just metered developer API billing)
- Not an opinion-giver (returns pure positional + classical structural data)

Interpretation, user experience, business logic → **main app layer**, not here.

---

## 🧪 Dogfood Principle

The owner's main app (AstroApp, scoped separately) will be the first VAstroChart customer. If it works for them, it works for other developers.
