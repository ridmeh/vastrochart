# 08 — Security & Compliance (Processor-Only Scope)

**VAstroChart is a Data Processor under GDPR, not a Controller.** Developers/apps calling the API are the Controllers of their own users' data. This dramatically narrows our compliance surface.

---

## What Role VAstroChart Plays

- **Data Processor**: We receive birth data on behalf of our customers (the API consumers) and perform computation on their instructions
- **Standard pattern**: Same as Stripe, Twilio, Auth0, OpenAI's API, any SaaS infrastructure provider
- **Not a Controller**: We never decide "why" the data is processed; the customer does

## What VAstroChart Does NOT Have

Because the service is stateless:
- ❌ No user accounts (just API keys)
- ❌ No database for end-user data (zero PII at rest)
- ❌ No reading history, no stored charts, no profiles
- ❌ No end-user authentication (just customer API keys)
- ❌ No GDPR subject access requests (nothing to disclose — we don't have end-user data)
- ❌ No right-to-delete workflows (nothing to delete)
- ❌ No breach notification obligations for end-user data (there's no stored data to breach)

---

## What VAstroChart MUST Have

| Control | Implementation |
|---|---|
| **TLS 1.3 in transit** | Front Door enforces |
| **No PII in logs** | Scrub birth data from request body before any logging. Log request_id, API key prefix, endpoint, status, latency. Never DOB/TOB/location. |
| **No disk persistence** | Compute runs in memory, response returned, GC'd. No temp files. |
| **API key authentication** | API Management stores hashed keys with prefix-visible display. Revocation supported. |
| **Rate limiting** | Per API key per tier. Protects against abuse. |
| **DDoS protection** | Front Door Premium includes DDoS Standard |
| **WAF** | Front Door Premium with OWASP Core Rule Set 3.2 |
| **Dependency security** | pip-audit + Microsoft Defender for Containers in CI |
| **Managed Identity** | Containers access Key Vault without stored secrets |
| **DPA (Data Processing Agreement)** | Template auto-sent to every customer on signup; required for Scale/Enterprise tiers |
| **Data residency** (as needed) | Deploy a second ACA environment in EU if EU customers require it; API Mgmt routes by caller region |

---

## Compliance By Framework

### GDPR
- **Role**: Processor
- **Obligations**:
  - DPA with customers (template provided at signup)
  - Technical and organizational measures (TLS, WAF, Managed Identity, dependency scanning)
  - Sub-processor transparency (we list our sub-processors: Microsoft Azure, Stripe)
  - Breach notification for OUR security (credential leaks, infrastructure compromise) — not for customers' data
  - Right-to-delete: N/A at our layer (we don't store anything)
  - Right-to-access: N/A at our layer
- **What customers do**: They sign our DPA, pass through their users' GDPR rights requests to their own system (which stores the data)

### CCPA
- **Role**: Service Provider (equivalent to Processor)
- **Same mechanisms as GDPR**

### SOC 2 (if pursued)
- **Scope**: Narrow because stateless
- Required controls: access management, change management, availability, security
- Harder: logical & physical access (inherit from Azure), vendor management (Stripe, Microsoft)
- Realistic timeline: Year 2+ if enterprise customers demand it
- Significantly cheaper to achieve than for a stateful product (fewer systems in scope)

### PCI DSS
- **Not applicable** — we never see payment card data (Stripe tokenizes)
- Our PCI scope: SAQ-A level (lightest form)

### HIPAA
- **Not applicable** — no protected health information

### India DPDP Act (2023)
- **Role**: Data Fiduciary (processor equivalent in Indian law)
- Standard contract clauses with Indian customers
- Possible data residency requirement for India customers (deploy ACA in Central India if needed)

---

## Threat Model (Narrow)

### What we protect from
1. **API key theft** → attacker makes expensive compute calls on customer's dime
   - *Mitigation*: Rate limits per key, anomaly alerts, key rotation UI, prefix-visible in UI (not full key)
2. **DDoS** → compute capacity exhausted
   - *Mitigation*: Front Door DDoS Standard + rate limits + max replicas cap
3. **Supply chain** → malicious dependency injected
   - *Mitigation*: pip-audit, Dependabot, pinned versions, Defender image scanning
4. **Credential leak** → Managed Identity bypass, Key Vault access
   - *Mitigation*: Managed Identity audit log, no human access to prod secrets, Azure Sentinel detection rules (optional)
5. **Request body PII in logs/traces** → accidental data retention
   - *Mitigation*: Pydantic validators scrub inputs before logging; App Insights sampling filter drops body content

### What we do NOT need to protect from
- End-user data breach (no end-user data stored)
- Insider access to end-user profiles (no profiles exist)
- GDPR right-to-access failures (nothing to access)
- Backup data leaks (no backups of PII)

---

## Request Logging Discipline

**Allowed in logs/traces**:
- `request_id` (ULID)
- API key prefix (first 8 chars, enough for support)
- Endpoint path
- HTTP status code
- Request content-length (for billing accuracy)
- Compute duration ms
- Response size
- Ephemeris version used

**Never in logs/traces**:
- Request body (contains birth data)
- Response body (contains chart data derived from PII)
- Full API key
- IP address beyond /24 subnet (for geo-anomaly detection, aggregate only)

**Implementation**: Pydantic model with `__repr__` scrubbed; FastAPI middleware strips body from span attributes before export to App Insights.

---

## DPA Template (Processor Agreement)

Ships with every new paid signup. Key clauses:
- VAstroChart acts solely as a Processor
- Compute performed in-memory, no retention beyond request lifetime
- Sub-processors disclosed (Microsoft Azure, Stripe for billing)
- Breach notification within 72 hours of discovery (our infrastructure only)
- Customer indemnifies for their own data handling obligations
- Standard GDPR Article 28 clauses
- SCCs (Standard Contractual Clauses) for EU-to-US transfer

Draft lives in `legal/dpa-template.md` (not yet created — Week 3 task).

---

## Infrastructure Access Model

- **No human SSH to prod containers** — kubectl/az equivalents are via Entra ID with MFA
- **Managed Identity** for all service-to-service auth (zero service-account keys)
- **Key Vault** holds: Swiss Ephemeris license (if commercial), API key hash pepper, Stripe webhook secret
- **CMK not needed** — nothing is encrypted at rest (nothing stored)
- **Audit**: Entra audit log + Key Vault access log + App Insights, retained 90 days

---

## Open Items Before Launch

- [ ] DPA template drafted (lawyer review — 1 hour)
- [ ] Terms of Service + Privacy Policy (template → 1-hour lawyer review)
- [ ] Incident response runbook (`docs/10-runbook.md` — Week 3)
- [ ] Swiss Ephemeris license decision: AGPL comply vs €400 commercial
- [ ] Dependency scanning in CI (pip-audit, Dependabot)
- [ ] App Insights PII-scrub pipeline tested with golden test chart
- [ ] Penetration test scheduled (OWASP ZAP automated at minimum; HackerOne when revenue allows)

---

## Why This Scope Is The Right Scope

Being a Processor instead of a Controller:
- **~10% of the compliance work** compared to a full consumer SaaS
- **Smaller legal spend** (one DPA template vs full GDPR implementation)
- **Smaller engineering budget** for compliance plumbing
- **Faster to launch** (3 weeks vs 6-10 for a controller product)
- **Easier to sell** to enterprise developers (they already have DPA templates for processors)

The main app ("AstroApp") project will take on the Controller role when it comes. Keeping these separate protects VAstroChart's lean compliance surface forever.
