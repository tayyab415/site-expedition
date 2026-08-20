# Challenge MVP implementation contract

**Status:** Frozen by [Freeze the approved challenge MVP contract](./issues/01-freeze-the-approved-challenge-mvp-contract.md)  
**Frozen at:** 2026-08-15  
**Destination-spec addendum:** 2026-08-19 (user reversal; see below)  
**Product authority:** [`grilling_session.markdown`](../../grilling_session.markdown) §§4–14, 20  
**Feasibility authority:** [`FULL_FEASIBILITY_DIAGNOSIS.md`](../../FULL_FEASIBILITY_DIAGNOSIS.md) §§1, 15, 17–18; [`feasibility/REQUIREMENT_LEDGER.md`](../../feasibility/REQUIREMENT_LEDGER.md)  
**Domain language:** [`CONTEXT.md`](../../CONTEXT.md) — use those terms exactly

This is the implementation contract. Later tickets may specify schemas, budgets, candidates, runtime, and UI behavior. They may not reopen the product vision or convert a failed, blocked, untested, or infeasible claim into a pass.

## Destination-spec addendum — 2026-08-19

The 2026-08-15 freeze deferred `land-change`, `labor-access`, `climate-trajectory`, Source Scout, extra architectural presets, interiors, and CAD. **The user did not ask for those cuts.** This addendum restores them as destination spec:

| Restored | Honest label |
|---|---|
| `land-change`, `labor-access`, `climate-trajectory`, constrained `source-scout` | INFORM only. Never score. Home never receives labor-access. Scout is official follow-up, not web discovery. |
| Ten-plus parametric presets, schematic interiors, conceptual DXF/IFC | Visual concept / coordination CAD. Labeled not for permit. |

**Still excluded:** stamped or permit-certified drawings; existing-building interior reconstruction from Google tiles or uploaded as-builts; licensed-parcel FIT; arbitrary source discovery or package installation.

See [`expedition/DECISIONS.md`](../../expedition/DECISIONS.md).

---

## Commitment classes

Every requirement below is tagged with exactly one class.

| Class | Meaning |
|---|---|
| **Committed** | Must ship in the challenge MVP, with the named honest fallback if a live dependency is unavailable. |
| **Honest fallback** | The required substitute when the preferred path is blocked or unproven. Using the fallback is still a pass. Pretending the preferred path worked is a fail. |
| **Conditional proof** | May enter the MVP claim only after a named bounded test passes. If it does not pass before demo lock, remove the claim rather than fake it. |
| **Deferred** | Explicitly out of this challenge build. Stretch only after the destination spec is approved and the MVP gates pass. |

Status words from the feasibility diagnosis (`DOCUMENTED`, `CONFIGURED`, `TESTED_OK`, `TESTED_FAILURE`, `PARTIAL`, `INFERRED`, `BLOCKED`, `UNTESTED`, `INFEASIBLE`) describe evidence, not product desire. A later ticket may upgrade a status only with new dated evidence.

---

## 1. Product identity

**Committed.** A skill-driven, US-only Site Expedition agent that converts structured real-estate requirements into evidence-backed Candidate Site decisions by combining Mireye's cited present-state facts with selective Earth Engine time/future witnesses, official public data when they add authority, Google visual context, and mandatory Skeptic Review.

This is screening, comparison, diligence orchestration, and conceptual planning. It is not a legal, engineering, appraisal, inspection, zoning, utility-capacity, water-right, title, or permit certification service.

**Buyer for the hero Expedition:** an operations lead or founder of a growing regional distribution business selecting its next facility.

---

## 2. Form factor and operating envelope

| Decision | Class | Contract |
|---|---|---|
| Geography | Committed | United States only; Mireye envelope `lat 18..72`, `lng -180..-65`. |
| Surface | Committed | Desktop-first web planning board. |
| Users | Committed | Single-user challenge prototype. No accounts, signup, collaboration, invitations, roles, or shared editing. |
| Persistence | Committed | Lightweight local/replay state only. No production SaaS, private Vault, or account-bound history. |
| Notifications | Deferred | No email or external notifications. No production background-job infrastructure. |

---

## 3. Missions and depth

The engine is universal in orchestration, evidence contracts, skill invocation, and verdict logic. Expertise is composed from reviewed capability skills. Missions are thin recipes, not five duplicated products.

| Mission | Class | Depth |
|---|---|---|
| Warehouse / Light Industrial | Committed | Hero. Structured controls, confirmed Mission Plan, 3–4 curated or user-supplied Texas Triangle Candidate Sites, core screen, flood-rewind when material, question-owned Workstreams, comparison, Skeptic Review, acquisition/verification brief, Aerial-then-3D scene. |
| Home | Committed as thin proof | Secondary recipe. Functional/property constraints only. Housing ranking must never solicit, infer, rank, or describe protected-class composition or steering proxies. Business demographic/labor facts must not leak into Home ranking. |
| Farm | Committed as thin proof | Secondary recipe using already-proven crop/site facts plus annual rotation and rainfall history. Water right remains a Verification Gap. |
| Data Center | Committed as thin proof | Secondary recipe using already-proven grid/heat/water/fiber screen plus observed heat. Deliverable MW, redundant enterprise fiber, and water capacity remain Verification Gaps. |
| Constrained Custom | Committed as constraint | Only a reviewed manifest of the same skills. No arbitrary source discovery or code installation. |

Exact secondary-recipe controls and visible output remain for [Fix the depth of secondary Missions](./issues/12-fix-the-depth-of-secondary-missions.md). Promoting any secondary Mission to hero depth is **Deferred** unless the hero Expedition finishes with unused schedule and credit headroom.

---

## 4. Site Forms, entry paths, and candidate labels

**Committed.**

- Site Forms: existing built asset, developable land, or either. Do not conflate location, parcel, building, listing, Market Availability, vacancy, or legally permitted use.
- **Find a Site:** Search Region + Mission, then lawful or curated Candidate Sites, then analysis.
- **Check a Site:** user-supplied address or pin, then analysis.
- Labels:
  - `LISTED` — only a named authorized provider with listing identity, source, and `last_seen_at`.
  - `USER SITE` — exact user-supplied address or pin; never imply Market Availability.
  - `POTENTIAL` — suitability screen without market evidence. A stale or expired listing becomes `POTENTIAL` plus a broker/owner confirmation action.

**Honest fallback.** No configured licensed feed exists for national warehouse, industrial, farm, or data-center inventory. The hero Expedition uses curated and/or user-supplied Candidate Sites. Consumer-marketplace scraping is prohibited. A public assessor record or vacant appearance is not Market Availability.

Exact Texas Triangle identities, coordinates, capture times, and the approved candidate file remain for [Approve the Texas candidate provenance set](./issues/02-approve-the-texas-candidate-provenance-set.md). Replacement and widening mechanics remain for [Design candidate acquisition, replacement, and widening](./issues/09-design-candidate-acquisition-replacement-and-widening.md).

---

## 5. Verdicts and evidence law

**Committed** product verdicts (not the harness `KEEP`/`KILL` labels):

- **Strong Fit** — every supported mandatory condition passes and the site compares well on preferences.
- **Reject** — reliable evidence contradicts at least one user-declared mandatory condition.
- **Conditional** — a material Verification Gap prevents a supported final result.

**Committed evidence law.** Unknown, absent, failed, stale, contradictory, or low-authority evidence must never silently become a pass. A required-source failure makes the mandatory condition Conditional, never Strong Fit. Evidence Coverage is distinct from Mission fit. Presentation-only Google content contributes zero score.

**Honest fallback for the hero.** Under current evidence, survivors will usually remain Conditional on route performance, Market Availability, and electrical capacity. San Marcos may appear as a provisional finalist under the narrow tested screen; that is not a calibrated universal ranking.

The atom schema, kinds, runtime status, decision effects, Independence Groups, Spatial Support, clocks, cache identity, Contradiction, and Verification Gap objects are frozen in [evidence-contract.md](./evidence-contract.md). Comparison algebra and Skeptic Review procedure remain for [Define verdict, comparison, and Skeptic Review semantics](./issues/08-define-verdict-comparison-and-skeptic-semantics.md).

---

## 6. Interaction model

**Committed.**

- Structured onboarding: Mission tiles, Search Region, Site Form, budget/size/geography, hard constraints, weighted preferences, bands where sliders would fake precision, toggles for optional investigations and Scan Budget.
- The agent compiles a Mission Plan. The user confirms it before expensive work.
- The product may accept an address or pin. It must not look like a chatbot and must not display hidden chain-of-thought or role-play agent avatars.
- Visual direction: professional, information-dense planning simulator. Not a cartoon game and not a science-fiction command center.
- Required proof surfaces: central map or photorealistic 3D planning board; Candidate Site cards; structured control deck; collapsible Expedition Rail; side-by-side comparison; dynamic scorecard bars; Evidence Coverage and Verification Gaps; progressive live status and failures.

Exact layout and interaction remain for [Prototype the desktop planning board](./issues/15-prototype-the-desktop-planning-board.md).

---

## 7. Expedition architecture

**Committed shape.** A Site Expedition is one goal-directed run. It must:

1. Compile the confirmed Mission Plan.
2. Obtain or accept Candidate Sites.
3. Resolve identity once; stop on unresolved ambiguity.
4. Run inexpensive screening first.
5. Apply deterministic hard gates; cancel unneeded work after a reliable Reject.
6. Spawn question-owned Workstreams for survivor questions (hazards/developability, logistics/access, utilities/capacity, environmental/land history, site identity/availability). Workstreams are not one agent per API.
7. Deepen only where more evidence can change the decision.
8. Commission Earth Engine only when it adds a temporal, event, disagreement, or scenario fact Mireye does not already supply as a sufficient present-state fact.
9. Reconcile contradictions without choosing the most favorable model as truth.
10. Run Skeptic Review on finalists before promoting a winner.
11. Produce the verdict, counterfactuals, and one cited acquisition/verification brief from the exact trace.

**Scan Budgets** remain Quick, Standard, and Deep. Numeric credit, dollar, latency, and retry ceilings remain for [Set the live-service budget and replay policy](./issues/03-set-the-live-service-budget-and-replay-policy.md). The state machine remains for [Prototype the Expedition state machine](./issues/07-prototype-the-expedition-state-machine.md).

**Committed model boundary.** The model may interpret controls, choose among allowed investigations, summarize evidence, and propose follow-ups. Code and config must validate Mission-to-skill eligibility, charge estimates, hard-gate semantics, evidence status, source independence, and the final verdict. The model cannot invent a threshold, authorize a source, or turn a failure into a pass. Model routing is not trusted: a Home flood case was consistently misrouted into `farm-history`. Gemini is currently blocked. Anthropic is callable but spend is uninspected.

---

## 8. Capability skills

**Committed concise skills** and allowed decision effects. Long API schemas belong in adapters, not skill bodies. Catalog/OpenAPI inspection is development or CI, not a runtime browse of 306 fields.

| Skill | Class | Allowed effect | Feasibility note |
|---|---|---|---|
| `resolve-site` | Committed | Canonical point/parcel, precision, ambiguity; stop if identity unresolved. Parcel attempt only for a finalist or explicit site. | PARTIAL |
| `screen-site-core` | Committed | `VETO` / `GATE` / `INFORM` / `UNKNOWN` from 6–12 Mission-specific non-parcel Mireye fields. No composite score. | TESTED_OK |
| `flood-rewind` | Committed, selective | Historical water witness or DEM disagreement; disagreement creates a Verification Gap. Default DEM is USGS 3DEP. | TESTED_OK, limited |
| `grid-readiness` | Committed for Warehouse/Data Center | Prioritize and name provider/proxies. Never clear MW, redundant fiber, or water capacity without provider evidence. | PARTIAL |
| `route-reality` | Committed as Workstream | Route time/distance **or** `UNKNOWN`. Never infer ingress or substitute straight-line distance as drive time. | TESTED_FAILURE |
| `scene-context` | Committed | Presentation only. Exact Aerial lookup if ACTIVE, else immediate Maps 3D. Zero score contribution. | PARTIAL |
| `skeptic-review` | Committed | Deterministic prechecks first; constrained model classifier second. Must not decide the hard verdict. | PARTIAL |
| `compare-candidates` | Committed | Deterministic comparison and provisional verdict from the evidence graph. | PARTIAL |
| `farm-history` | Committed in Farm recipe | Crop/rain history and constraints. Water right always separate authority. | PARTIAL |
| `environmental-record` | Conditional proof | Identify facility/permit record and Phase I follow-up after a Mireye hit. Not a clean-site certification. | PARTIAL |
| `land-change` | Deferred unless validated | Change interval/type only after window/scale stability and independent check. | PARTIAL, unvalidated |
| `labor-access` | Deferred | Business-only; needs real Routes and a user-declared staffing constraint. | UNTESTED |
| `climate-trajectory` | Deferred for hero; optional Farm/DC stretch | Regional scenario-conditioned range, never parcel prediction. | PARTIAL, one path |
| `concept-fit` | Conditional proof | `PLAUSIBLE` / `CONFLICT` / `UNKNOWN` from independently licensed geometry. Never permit/engineering approval. | UNTESTED |
| `source-scout` | Deferred | Constrained only; no unrestricted live-source discovery. | — |

**2026-08-19 addendum.** `land-change`, `labor-access`, `climate-trajectory`, and constrained `source-scout` are INFORM workstreams on Standard/Deep. They never score. Home never receives `labor-access`. `concept-fit` remains deferred (no licensed parcel).

Starting Warehouse non-parcel screen fields (catalog v0.14.0, not permanent thresholds): `elevation`, `slope_degrees`, `fema_flood_zone`, `within_floodplain_polygon`, `intersects_wetland`, `coast_distance_m`, `nearest_major_road_distance_m`, `nearest_major_road_class`, `nearest_long_haul_rail_corridor_distance_m`, `nearest_substation_distance_m`, `fiber_broadband_available`, `within_water_service_area`, `within_sewer_service_area`, `nearest_hazardous_facility_distance_m`. A development-time catalog check must fail if a required field disappears or changes type/source.

Versioned manifests and compiler rules remain for [Design Mission Plans and reviewed skill manifests](./issues/06-design-mission-plans-and-reviewed-skill-manifests.md).

---

## 9. Source roles and honest fallbacks

### Mireye

**Committed** as the live primary present-state broker. Runtime hard gates use deterministic `/fetch` or `/fetch/batch`, not `/ask`. Always quote before a metered run. Prefer coordinates over addresses (addresses sent to Mireye are retained for audit/cache for 30 days unless resolved client-side).

**Honest fallback.** On 2026-08-15 the Free plan had **56** credits remaining (reset 2026-09-01). A six-candidate ten-field screen costs 60; one `site_selection` costs 363 because it includes a 300-credit parcel group. Implementation must start cache/fixture-first with visible stale/live labels, wait for reset, or obtain explicit extra credits. Do not buy credits automatically. Do not run further metered validation without a recorded budget.

### Earth Engine

**Committed** as a selective witness, not a Mireye redisplay. Proven hero witness: JRC monthly history plus USGS 3DEP disagreement on the San Leon / Austin controls. JRC-through-Mireye and JRC-through-Earth-Engine are the same source family: temporal transformation adds information, not independent corroboration.

**Honest fallback.** FABDEM community asset is CC BY-NC-SA 4.0 and must not be the default production path. Replace with USGS 3DEP; any second DEM is optional and separately cleared. Hackathon EE access does not prove commercial production rights. Inspect registration class, tier, and remaining EECUs before a live demo.

### Google visual stack

**Committed.** Exact Aerial View lookup → play if ACTIVE → immediate 3D fallback. Retain only `videoId`; never persist signed playback URLs or video bytes. Google pixels and meshes are presentation-only: no machine interpretation, geometry extraction, scoring, or prohibited export.

**Honest fallback.** Aerial 404 is a documented non-event, not a failure of the Expedition. Browser Maps 3D rendering remains PARTIAL until the target desktop is measured.

### Routes

**Committed as a Workstream that may be UNKNOWN.** Current configured key: `403 API_KEY_SERVICE_BLOCKED`. Legacy Distance Matrix is not enabled.

**Honest fallback until [Resolve Routes for the hero Expedition](./issues/04-resolve-routes-for-the-hero-expedition.md) closes:** show Mireye straight-line infrastructure proximity as a different metric; keep route-dependent requirements Conditional / `UNKNOWN`; name a verification action. Do not fabricate drive time, truck ingress, legal truck route, turn radius, or access control. Changing key restrictions or enabling APIs requires explicit user approval.

### Direct official sources

**Committed when they add authority** after a Mireye hit or fill a missing authority. Duplicating the same FEMA/EIA/USDA value is not corroboration. NWI is non-regulatory. EIA/LODES/FAF never prove parcel capacity, worker availability, or driveway suitability.

### AWS

**Deferred.** No necessary MVP fact. Exclude unless a later stretch question cannot be answered more simply and the user approves any spend.

---

## 10. Concept Studio (`TODAY` / `FIT` / `FUTURE`)

| Layer | Class | Contract |
|---|---|---|
| `TODAY` | Committed | Live Aerial if ACTIVE, else Maps 3D. Human context only. |
| `FIT` | Conditional proof | Constraint and buildable-envelope display only from independently licensed parcel/constraint geometry. |
| `FUTURE` | Conditional proof | One prebuilt, rights-cleared warehouse glTF/GLB with declared footprint, height, setback-as-assumption, dock/yard assumptions, and orientation controls. Concept Test must pass on one positive, one known-conflict, and one ambiguous/low-quality boundary **without Google tiles present**. |

**Honest fallback.** If the three-case Concept Test does not pass before demo lock, remove `FUTURE` (and `FIT` if it depends on the same unproven geometry) rather than show visual theater.

**2026-08-19 addendum.** Parametric presets, schematic interiors, and conceptual (not stamped) DXF/IFC are in. Live generative CAD from Google tiles, permit-ready IFC/DXF, and existing-building reconstruction stay out.

Inputs remain for [Establish the warehouse concept inputs](./issues/10-establish-the-warehouse-concept-inputs.md). The include/defer decision remains for [Prove or defer Concept Studio](./issues/11-prove-or-defer-concept-studio.md).

---

## 11. Demo integrity

**Committed** two-minute truthful shape (exact beats remain for [Assemble the truthful two-minute demo contract](./issues/18-assemble-the-truthful-two-minute-demo-contract.md)):

1. Choose Warehouse and confirm a prewritten structured Mission Plan.
2. Load 3–4 explicitly curated or user Candidate Sites with source labels.
3. Run a small live Mireye core screen only if credits are approved or reset; otherwise replay source-valid, visibly timestamped cache.
4. Reject San Leon on supported flood facts.
5. Replay the Earth Engine flood witness live or from a source-valid dated cache.
6. Compare survivors; show route, Market Availability, and capacity as Verification Gaps unless later tickets close them.
7. Run constrained Skeptic Review.
8. Show the acquisition/verification brief.
9. Show Aerial if exact ACTIVE, otherwise 3D fallback.

**Must never appear as live:** a new Aerial render, broad parcel scans, arbitrary live inventory, utility capacity confirmation, entitlement, an untested Concept Studio, or a hidden precomputed result.

**Required visible recovery:** Aerial 404 → 3D; Routes 403 → `UNKNOWN`; Mireye partial failure → retain successful fields; stale cache → timestamp and replay label; veto → cancel expensive downstream work; required unknown → Conditional.

---

## 12. Security, licensing, and spend (standing constraints)

**Committed constraints** for later guardrail design. Exact controls remain for [Specify security, privacy, licensing, and spend guardrails](./issues/16-specify-security-privacy-licensing-and-spend-guardrails.md).

- Server-side secrets; no browser-embedded Maps or Mireye keys.
- Quote-before-fetch; local maximum-credit guard below account allowance; explicit opt-in for any parcel-group field.
- Cache key must include provider, dataset/API version, field/recipe version, geometry hash or parcel id, spatial support, date window, scale, mask/orbit settings, and transformation version. Never key on a display slug alone. Never label cached evidence live.
- Preserve status, TTL, notes, and `partial_failures` (current harness strips them).
- Remove the signed Aerial playback URL from `uchicago-aerial-view.html`; retain `videoId` only.
- Do not use FABDEM as the default height witness.
- Iteration 7's open `0.0.0.0` + `Access-Control-Allow-Origin: *` + unrestricted tile proxy is not an acceptable production-shaped demo server.
- Reports reproduce derived numbers, public-source citations, assumptions, and the decision trace — not prohibited imagery or licensed raw parcel/listing payloads.

---

## 13. Explicitly excluded

These stay out of the challenge MVP even if later tickets have leftover time:

- Collaboration, invitations, teams, roles, shared editing, accounts, signup, email, notifications, production background jobs.
- User evidence uploads, unrestricted live-source discovery, arbitrary code installation, consumer-marketplace scraping.
- Nationwide commercial / farm / data-center listing claims without a licensed adapter.
- Stamped / permit-certified CAD/IFC, engineering or architectural certification, existing-building interior reconstruction from tiles or uploaded drawings. Conceptual coordination CAD and schematic program interiors are in (2026-08-19 addendum).
- Claims of utility headroom, redundant enterprise fiber, water rights/capacity, zoning approval, listing availability, vacancy, building condition, title, permits, or legal permission without the responsible authority.
- Machine interpretation, geometry extraction, prohibited caching, or prohibited export of Google imagery and 3D content.
- Production SaaS persistence, private Vault, broad export suites, account-bound history.
- AWS workloads, paid cloud enablement, key-restriction changes, credit purchases, or extra Mireye spend without explicit user approval.

---

## 14. Implementation may begin only when

The destination specification may authorize a build agent only after later tickets have recorded:

1. A credit ceiling the current account can honor, with live vs replay labels.
2. Truthful Candidate Site labels and a lawful curated/user file.
3. Routes either tested successfully or visibly excluded as `UNKNOWN`.
4. Concept Studio independently proven or removed from the MVP claim.
5. Deterministic routing, verdict, and failure guards around the model.
6. The full evidence contract and source-independence graph.
7. A two-minute demo whose live and cached steps are visibly distinguishable.

Until then, this map continues to plan. It does not implement the product.

---

## 15. What this contract does not decide

Left to later tickets: numeric budgets; the approved Texas candidate file; evidence schema fields; Mission Plan compiler details; Workstream DAG; verdict algebra; replacement/widening rules; GLB provenance; Concept include/defer; secondary-recipe UI depth; process/runtime boundaries; which iteration to keep; planning-board interaction; enforceable security controls; the test pyramid; the timed demo script; and the final sequenced build checklist.
