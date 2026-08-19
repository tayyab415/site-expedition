# PRODUCT — the one page that says what we're building

**Date:** 13 Aug 2026 · supersedes ambiguity across OBJECTIVE.md / DEEP_RESEARCH_VERDICT.md /
DELIVERY_COMBOS_VERDICT.md. Those stay as research records; *this* is the product.

---

## One sentence

**A property vetting agent: give it a pin, and it cross-examines the official cited record
against independent satellite witnesses, then rules KEEP / KILL / ASK-A-HUMAN — with a
packet of receipts.**

The user's mental model: *"the skeptic I send in before I sign."*
The judge-facing model: *"a prosecutor, not a property report."*

---

## The system, in five layers

| # | Layer | What it is | Status |
|---|---|---|---|
| 1 | **Eyes** | Mireye (the cited record), Earth Engine (time + height witnesses), Google pretty (context only, never in the packet) | ✅ built (`harness/eyes/`) |
| 2 | **Intelligence** | The part that makes verdicts defensible: (a) *triage* — the record picks which fights to stage; (b) *adjudication* — thresholds calibrated against county null-distributions, source-trust rules (why FABDEM dissents in marsh), vintage arithmetic (map born wrong vs aged out); (c) *consequence* — fights priced in $, street-vs-lot contrast | 🔨 **this is the build** |
| 3 | **Verdict** | KEEP / KILL / HUMAN, in code, deterministic | ✅ built (v0: two hardcoded fights) |
| 4 | **Packet** | kill_letter.md + verdict.json + evidence + timeline SVG, every fact cited | ✅ built (v0) |
| 5 | **Interface** | Whatever renders the packet (web, chat, swipe) | ⏸ later, deliberately |

The **harness** is layers 1+3+4 — it exists and runs (`harness/vet.py --site san_leon` → KILL).
The **product work remaining** is layer 2. The interface is presentation, not product.

---

## What the user experiences (this is also the demo script)

1. Paste a pin (later: an address or a listing URL).
2. Robot pulls the cited record — shows it straight: "AE, 2.37 m, 5% water, wetland." Looks fine.
3. Robot summons the witnesses the record itself makes relevant (coastal + poor drainage → time + height).
4. The fights surface: *dry for 15 years, wetting since 2001, record says 5%, Earth says 10.8%;
   record says 2.37 m, bare-earth model says 0.75 m.*
5. Verdict card: **KILL** — with the one-liner ("you're buying 2021 dirt at a 1995 feeling")
   and the packet attached.
6. Move the pin one street inland → **KEEP**. The flip is the proof it's an agent, not a mood.

---

## Scope fences (what we are NOT building)

- ❌ A map UI / globe app — Google pixels are a prop the robot aims, demo-only.
- ❌ A property report / diligence dump — that's Mireye's own template; no fights, no product.
- ❌ Roof CSI — killed by the Austin permit probe; EE cannot date a reroof at house scale.
- ❌ A buying assistant (listings, prices, scheduling) — Zillow's war, not ours.
- ❌ Auto-filing anything legal — the packet is drafted for a human to send.
- ❌ v1 interface — packet files are the product surface until the harness is credible.

## Kept warm (same robot, later courtrooms — config, not rewrite)

- Statute-clock nonrenewal packet (OBJECTIVE.md — buyer: public adjuster / producer).
- Live listing as the defendant; street swipe (batch 25); `parcel_grade` four-wheres identity fight.
- **Ag pivot:** record = lease/water-right claims; witnesses = phenology, CDL, CHIRPS-drought
  irrigation test. Buyer: farmland investors / ag lenders. Heaviest user of the same eyes.

---

## Build order (layer 2, headless)

1. **Calibration** — ~50 county control points through both witnesses → empirical percentiles
   in the judge (+ free KEEP controls). EE-only, zero Mireye credits.
2. **Fight-selection rulebook** — record patterns → docket (makes it scale past San Leon).
3. **Vintage arithmetic** — FEMA study date vs breakpoint year: "map born wrong" vs "map aged out."
4. **Contradiction pricing** — fights → $ range in the letter (verdict becomes a negotiation).
5. *(then)* street differencing, precedent memory, second courtroom.

## Constraints that shape everything

- Mireye: 156 credits until promo codes; parcel bundle = 300 → terrain/flood presets only; cache-first always.
- San Leon has no Aerial View; Texas NAIP in EE ends mid-2022 — print capture dates, never claim freshness.
- Google imagery never in the cited packet (ToS); NAIP/JRC/FABDEM are public-domain exhibits.
- Verdicts are code. A model may narrate; it may never decide.

## Submission mapping (challenge checklist)

- **Agent** ✅ reason (fights) → decide (verdict in code) → act (packet + advisory).
- **Mireye core** ✅ the record *is* one of the two parties in every fight, plus triage brain.
- **Weird second source** ✅ the satellite archive as an adversarial witness (and later: the listing, the carrier's notice).
- **Buyer** ✅ buyer's agent (v1 chair); PA/farmland lender in later courtrooms.
- **Demo** ✅ the KILL→KEEP flip at two pins; the red-bars timeline; the kill letter.
