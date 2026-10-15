# Yoga Detector Ledger

Source of truth for `compute/yogas.py`'s in-code registry (read by both `/v1/yogas` and `/v1/yogas/registry`, per `docs/09-output-schema.md`). Reviewed and cross-validated by the owner on 2026-10-10 before any implementation began.

**Confidence** is a property of the detector (the rule), not of any one chart:
- **High** — single well-agreed condition, safe to implement as-is.
- **Medium** — the core mechanic is solid but a detail (threshold, which houses, cancellation clause) varies by source or needs a judgment call.
- **Low** — multiple competing formulations exist, or reconstructed from memory — flagged for review before being treated as authoritative.

No chapter/verse citations are asserted here — "BPHS" below means "classically attributed, citation not pinned down," not a verified reference (`CLAUDE.md` no-hallucination rule).

Tally: **11 high**, **14 medium**, **8 named-only (not specified, not in the registry)**.

---

## Pancha Mahapurusha Yoga

Shared rule: a planet in its own sign or exaltation, in a kendra (1st/4th/7th/10th) from Lagna.

| Name (Sanskrit) | Confidence | Condition |
|---|---|---|
| Ruchaka Yoga (रुचक) | High | Mars in Aries/Scorpio (own) or Capricorn (exalted), in kendra from Lagna. |
| Bhadra Yoga (भद्र) | High | Mercury in Gemini or Virgo (own = exalted sign for Mercury), in kendra from Lagna. |
| Hamsa Yoga (हंस) | High | Jupiter in Sagittarius/Pisces (own) or Cancer (exalted), in kendra from Lagna. |
| Malavya Yoga (मालव्य) | High | Venus in Taurus/Libra (own) or Pisces (exalted), in kendra from Lagna. |
| Shasha Yoga (शश) | High | Saturn in Capricorn/Aquarius (own) or Libra (exalted), in kendra from Lagna. |

Note: all five — kendra is checked via Whole-Sign houses (matches the rest of the engine), not K.P./Placidus, which can disagree near a cusp.

## Moon-based (chandra_based)

| Name (Sanskrit) | Confidence | Condition | Notes |
|---|---|---|---|
| Gaja Kesari Yoga (गजकेसरी) | High | Jupiter in house 1/4/7/10 from the Moon. | Some sources add a strength qualifier (not debilitated/combust) — surfaced separately, not baked into pass/fail. |
| Chandra Mangala Yoga (चन्द्र-मंगल) | High | Moon and Mars in the same sign. | Some sources extend to mutual aspect — not included in the base check. |
| Sunapha Yoga (सुनफा) | Medium | Any planet except Sun in the 2nd house from Moon. | |
| Anapha Yoga (अनफा) | Medium | Any planet except Sun in the 12th house from Moon. | |
| Durudhura Yoga (दुरुधरा) | Medium | Both 2nd-from-Moon and 12th-from-Moon occupied (Sun excluded). | Mutually exclusive with Sunapha/Anapha by construction — useful as a sanity check. |
| Kemadruma Yoga (केमद्रुम) | Low | Base trigger only: no planet (Sun excluded) in 2nd/12th from Moon, and none conjunct Moon. | **No cancellation logic specified** — several classical cancellation clauses exist; implementing the bare trigger would over-flag a common, mostly-neutral pattern. |
| Adhi Yoga (अधि) | Low | Benefics (Mercury/Jupiter/Venus) in houses 6/7/8 from Moon. | Unclear whether all three houses must be occupied, by how many benefics, or any occupation in that range suffices. |

## Sun-based (surya_based)

| Name (Sanskrit) | Confidence | Condition | Notes |
|---|---|---|---|
| Budhaditya Yoga (बुधादित्य) | High | Sun and Mercury in the same sign. | Will trigger often (Mercury is never far from the Sun). Some add "not combust" — blocked on the engine's combust-orb decision (see Pending Tasks). |
| Vesi Yoga (वेसि) | Medium | A planet other than Moon in the 2nd house from Sun. | |
| Vasi Yoga (वासि) | Medium | A planet other than Moon in the 12th house from Sun. | |
| Ubhayachari Yoga (उभयचरी) | Medium | Both 2nd-from-Sun and 12th-from-Sun occupied (Moon excluded). | |

## Raja & Dhana — general mechanics (raja_dhana)

Not single named yogas — mechanics that generate many specifically-named yogas. Implement the mechanic plus a representative subset, not every named classical variant.

| Name | Confidence | Condition | Notes |
|---|---|---|---|
| Raja Yoga (kendra–trikona connection) | Medium | Lord of a kendra (1/4/7/10) and lord of a trikona (1/5/9) are conjunct, in mutual aspect, or in parivartana. | House 1 is both kendra and trikona — decide explicitly whether the Lagna lord double-counts. |
| Dhana Yoga (representative, not exhaustive) | Low | 2nd lord & 11th lord connected; OR 9th lord in 11th / 11th lord in 9th; OR 5th lord & 9th lord connected. | Classical/later texts list many more lord-pair combinations under this heading. |

## Vipreet Raja Yoga

A dusthana (6th/8th/12th) lord placed in *another* dusthana house.

| Name (Sanskrit) | Confidence | Condition |
|---|---|---|
| Harsha Yoga (हर्ष) | Medium | 6th lord placed in house 6, 8, or 12 from Lagna. |
| Sarala Yoga (सरल) | Medium | 8th lord placed in house 6, 8, or 12 from Lagna. |
| Vimala Yoga (विमल) | Medium | 12th lord placed in house 6, 8, or 12 from Lagna. |

Note: unclear whether same-house placement (e.g. 6th lord in the 6th) should count or is a separate, distinct situation in some texts.

## Neechabhanga Raja Yoga

| Name | Confidence | Condition |
|---|---|---|
| Neechabhanga Raja Yoga (नीचभंग राज योग) | Low | Base: a planet is debilitated. Candidate cancellation (any one typically sufficient): (1) lord of the debilitated planet's sign is in a kendra from Lagna/Moon; (2) the planet exalted in that sign is in a kendra from Lagna/Moon; (3) the debilitated planet's dispositor is itself exalted; (4) the debilitated planet and its exaltation-sign ruler are in mutual kendras. |

**Highest-risk item in the set** — clause list and precedence not verified against a primary source, reconstructed from memory of BPHS-tradition summaries. Needs sourcing before implementation, not just cross-validation.

## Parivartana & other named combinations (parivartana)

| Name (Sanskrit) | Confidence | Condition | Notes |
|---|---|---|---|
| Parivartana Yoga (परिवर्तन) | High (mechanic) / Medium (classification) | Planet A occupies B's sign and planet B occupies A's sign. | Mechanic is simple and well-agreed; classifying the exchange as auspicious ("Maha"/"Raja") vs. inauspicious ("Dainya") depends on which houses the two planets rule. |
| Lakshmi Yoga (लक्ष्मी) | Medium | 9th lord in own/exalted sign, and Lagna lord is strong (kendra/trikona, or own/exaltation sign). | "Lagna lord is strong" is composite — some room for interpretation on which clause(s) must hold. |
| Saraswati Yoga (सरस्वती) | Medium | Jupiter, Venus, Mercury all in kendra/trikona/2nd houses from Lagna, and Jupiter is strong (own/exalted/friendly). | |

## Arishta Yoga — afflictions

| Name (Sanskrit) | Confidence | Condition | Notes |
|---|---|---|---|
| Guru Chandala Yoga (गुरु चाण्डाल) | High | Jupiter in the same sign as Rahu or Ketu. | |
| Grahan Yoga (ग्रहण) | High | Sun or Moon in the same sign as Rahu or Ketu. | |
| Angarak Yoga (अंगारक) | Medium | Mars in the same sign as Rahu or Ketu. | |
| Vish Yoga (विष) | Medium | Moon in the same sign as Saturn. | |
| Shakata Yoga (शकट) | Medium | Moon in house 6, 8, or 12 from Jupiter. | Some sources use only 6th/8th, others include 12th — confirm which houses count. |
| Daridra Yoga (दरिद्र, representative) | Low | 11th lord placed in house 6, 8, or 12 from Lagna. | Like Dhana Yoga, this heading covers several distinct classical combinations — one representative trigger, not the full definition. |

## Named but not specified (not in the registry)

Recognized by name, but no condition confident enough to register yet:

- **Kaal Sarpa Yoga** — all seven classical planets confined to one side of the Rahu–Ketu axis. Simple mechanic, but widely used in *popular* practice; not confident it traces to a primary classical text — worth deciding whether it belongs in a "classical" detector set at all.
- **Akriti (shape) Yogas** — Gada, Shakata, Vihaga, Vajra, Yava, Kamala, Vapu, Yupa, and related patterns based on how the seven planets distribute across the twelve houses. ~12 of these; no confident per-pattern definitions.
- **Amala Yoga** — benefic in the 10th from Lagna or Moon (uncertain which, or both).
- **Chamara Yoga** — Lagna lord exalted and aspected by/conjunct Jupiter (exact requirement uncertain).
- **Vasumati Yoga** — benefics in houses 3/6/10/11 from Lagna or Moon (uncertain reference point and whether all four houses or a subset).
- **Akhanda Samrajya Yoga** — multi-condition Raja Yoga involving the 9th/10th lords and the Moon; full condition set not confident.
- **Matsya / Kurma Yoga** — further akriti-family shape yogas; no confident condition.
- **Dainya / Daridra-combination variants** — the poverty-combination family likely has more entries than the one representative check above.
