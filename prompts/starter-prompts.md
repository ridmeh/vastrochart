# Starter Prompts For Claude Code / Cursor

Copy-paste these at the right moment. Saves retyping context.

---

## 🚀 First Session Ever

```
Read CLAUDE.md completely. Then read tasks/week-1-day-by-day.md.
Confirm you understand:
1. The scope discipline rules (no state, no LLM, no persistence)
2. The schema-first rule (Day 1 is schema review, not coding)
3. The golden regression contract

Then start Day 1 Task 1.1.
```

---

## 📋 Any Return Session

```
Read CLAUDE.md and tasks/week-1-day-by-day.md. 
Which day/task are we on? Start the next unfinished item.
```

Short, works every time. CLAUDE.md routes to everything else.

---

## 📜 Day 1 — Schema Sparring Partner

Use when you're reviewing `docs/09-output-schema.md`:

```
I want you to be a tough sparring partner on docs/09-output-schema.md.

For each endpoint's response schema:
1. Challenge every field name — is it the clearest possible word?
2. Flag anything that would be painful to change in v2
3. Suggest fields I probably forgot (based on Vedic + K.P. domain knowledge)
4. Point out inconsistencies between endpoints
5. Validate error envelope completeness

Treat this as the single most expensive design decision of the project.
Our output schema is the contract. Breaking changes mean customer pain.

Start with the response envelope, then /v1/charts/compute, then move through 
the rest in order. Pause between each endpoint for my decisions.
```

---

## 🧮 Day 4 — K.P. Sub-Lord Algorithm

The gnarliest math in the project. Use this prompt:

```
I need to implement the K.P. sub-lord algorithm in 
apps/vastrochart-compute/src/compute/kp_sublord.py.

Rules:
- Each nakshatra (13°20') is divided into 9 sub-arcs using Vimshottari ratios 
  (Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, 
  Mercury 17 = 120 years total)
- Sub arc = (lord_vimshottari_years / 120) × 13°20'
- The sub sequence STARTS from the nakshatra lord (not Ketu)
- Sub-sub applies the same proportions WITHIN the sub

Write:
1. Function `get_kp_sublord(sidereal_longitude: float) -> tuple[str, str, str]` 
   returning (nakshatra_lord, sub_lord, sub_sub_lord)
2. Unit tests covering: start of each nakshatra, mid of each nakshatra, 
   29°59'50" sandhi, 0°00'00" start of Aries, 359°59'59" end of Pisces
3. Doc comment citing the K.P. textbook reference

Floating point: use arc-minute arithmetic internally (multiply by 60) to avoid 
cumulative float errors across sub boundaries.
```

---

## 📅 Week 2 — Dasha Engine

```
I need the Vimshottari Dasha engine in apps/vastrochart-compute/src/compute/dasha.py.

Rules:
- Birth MD is the nakshatra lord of natal Moon
- Balance of birth MD = (unused_nakshatra_arc / full_nakshatra_arc) × lord_years
- Hierarchy: MD → AD → PD → Sookshma → Prana
- At each level, same Vimshottari sequence proportioned within the parent period

Required public functions:
- `compute_dasha_sequence(moon_longitude: float, dob: date) -> list[MahadashaPeriod]` 
  (all 9 MDs from birth)
- `active_dasha_at(moon_longitude: float, dob: date, as_of: date, depth: Depth) 
   -> ActiveDasha` (nested MD/AD/PD/Sookshma)

Match the output schema in docs/09-output-schema.md for /v1/dasha exactly.

Golden tests must verify:
- Birth MD lord matches nakshatra lord of natal Moon
- MD end date = MD start + (lord_years × 365.25) rounded to days
- AD within MD proportions sum to MD duration
```

---

## 🌅 Week 2 — Panchang Engine

```
Build apps/vastrochart-compute/src/compute/panchang.py.

Rules:
- Panchang starts at local sunrise (NOT midnight)
- Compute sunrise/sunset using swe.rise_trans with STAR_RISE_SET_SPEED flag
- Tithi: angular distance (Moon - Sun) / 12°, 30 tithis per month, 
  Shukla (0-15) vs Krishna (15-30) paksha
- Nakshatra: Moon's current nakshatra
- Yoga: (Sun + Moon longitudes) / 13°20', 27 yogas
- Karana: half of a tithi, 11 karanas, Bhadra = Vishti is the classical "avoid"
- Transition times: when each limb's angular measurement crosses the next boundary

Must return transition datetime for each limb within the day. The /v1/panchang 
response in docs/09-output-schema.md shows the exact shape — match it.

Verify against DrikPanchang app for 3 reference dates to catch rounding issues 
at the ~1-minute level.
```

---

## 🕐 Week 2 — Hora Engine

```
Build apps/vastrochart-compute/src/compute/hora.py.

Rules:
- 24 planetary hours per day: 12 day-horas (sunrise to sunset) + 12 night-horas 
  (sunset to next sunrise)
- Day hora length = (sunset - sunrise) / 12
- Night hora length = (next_sunrise - sunset) / 12  
- Sequence per weekday uses Chaldean order: Saturn, Jupiter, Mars, Sun, Venus, 
  Mercury, Moon
- First hora of day = weekday lord (Mo on Monday, Ma on Tuesday, etc.)
- Then rotate through Chaldean sequence for all 24 horas

Match /v1/hora response in docs/09-output-schema.md.

Golden tests: for a known sunrise/sunset date, verify first day-hora lord 
matches weekday lord, and 24th night-hora lord is the planet BEFORE the next 
day's lord in Chaldean sequence.
```

---

## 🏷️ Week 2 — Classical Yogas

```
Build apps/vastrochart-compute/src/compute/yogas.py.

Scope for MVP: 50 yoga detectors covering:
- 5 Pancha Mahapurusha Yogas (Ruchaka/Bhadra/Malavya/Hamsa/Shasha)
- Gaja Kesari Yoga
- Chandra Mangala Yoga
- Dhana Yogas (3-5 variants)
- Raja Yogas (kendra-trikona lord combinations)
- Vipreet Raja Yoga
- Neechabhanga Raja Yoga
- Lakshmi Yoga
- 5-10 Arishta Yogas (negative)

For each yoga, implement a pure function:
`def detect_<yoga_name>(chart: NatalChart) -> YogaDetection | None`

Each detection returns:
- name (English + Sanskrit)
- formed_by (list of specific planet positions that formed it)
- classical_reference (text + chapter + verse)
- strength (0.0-1.0 based on how cleanly the condition is met)

Register all detectors in a YOGA_REGISTRY list; /v1/yogas endpoint iterates it.

Use classical texts from docs/02-domain-knowledge.md. CITE references in 
comments. Never invent a yoga not in classical texts.
```

---

## 🎨 Week 2 — MCP Transport

```
Wire FastMCP transport into apps/vastrochart-compute/src/mcp/.

Goal: expose the same compute functions as MCP tools at /mcp/sse, backed by 
the same Pydantic models.

Rules:
- Zero duplication: MCP tool handlers call the same compute functions as 
  REST handlers
- Tool definitions match spec/mcp-tools-schema.json exactly
- Error responses in MCP use the same error envelope format

Verify by registering the local MCP server with Claude Desktop and testing 
every tool from there.
```

---

## 🚢 Week 3 — Azure Deploy

```
I'm starting Week 3. Target: production live at api.vastrochart.com by end 
of week.

Create infra/ directory with Terraform modules:
- resource_group
- container_registry (ACR)
- container_apps_environment (ACA)
- container_app for vastrochart-compute (min replicas 1, max 20)
- front_door_premium (WAF + DDoS)
- api_management_consumption (metered billing)
- key_vault (Swiss Eph license, API key pepper, Stripe webhook secret)
- application_insights
- managed_identity assignments

Set up GitHub Actions workflow:
- Build Docker image on push to main
- Push to ACR
- Deploy ACA revision via az CLI
- Smoke test the new revision via /healthz before cutover

See docs/03-architecture.md for the target design. 
See docs/08-security.md for the compliance constraints.
```

---

## 💳 Week 3 — Stripe Metered Billing

```
Wire Stripe metered subscription billing.

Flow:
1. Developer signs up at vastrochart.com → Stripe Checkout for tier selection
2. Stripe webhook creates API Mgmt subscription with corresponding tier
3. API Mgmt emits usage events per call
4. Nightly job aggregates usage per API key → reports to Stripe for metered billing

Tiers:
- Free: 1,000 calls/mo
- Starter: $49/mo, 50,000 calls/mo
- Pro: $199/mo, 500,000 calls/mo  
- Scale: $999/mo, 5,000,000 calls/mo

Keep Stripe webhook signature verification airtight — our only payment-related 
code.

API key format: `vk_live_<24 random bytes url-safe base64>` (prefix visible 
in UI, full key hashed in storage).
```

---

## 🔄 Debugging / Stuck

```
I'm stuck on [brief description]. Here's what I tried:
1. [attempt 1]
2. [attempt 2]

The specific error is:
[paste error]

Context: We're on Day [N] Task [X.Y] of tasks/week-1-day-by-day.md.
Question: [specific question or request for diagnosis]

Don't propose rewriting unrelated code. Diagnose this specific issue first.
```

---

## 🧘 Scope Guard

```
Someone (customer, teammate, me in a weak moment) wants to add [feature] 
to VAstroChart.

Check against CLAUDE.md "Scope Discipline" section. Does this cross a line?
If yes, explain which boundary it crosses and suggest where it should live 
instead (main app, developer customer's code, etc.).
```

---

## 📝 Writing An ADR

```
I'm making an architectural decision about [topic]. Write it up as 
ADR-NNN in docs/05-decisions.md following the existing format:
- Decision (one line)
- Context (why we're deciding this now)
- Rationale (why this choice vs alternatives)
- Trade-offs (what we lose)
- When to reconsider (what would make us revisit)

The decision is: [state it clearly].
```

---

🙏 **Tip**: Keep this file open in a side pane while coding. Prompts you don't need to retype save hours over 3 weeks.
