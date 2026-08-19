# Mireye Universal Site Expedition — Complete Grilling Session Record

**Status:** Product direction approved; exhaustive feasibility diagnosis required before implementation  
**Conversation period:** 14–15 August 2026  
**Workspace:** `/home/tayyabkhan/Shared/mireye-challenge`  
**Purpose of this document:** Reconstruct the entire product-grilling session into one reliable source of truth for a fresh feasibility-research agent.

---

## 1. How to read this document

The original conversation used numbered questions, but several replies arrived with missing, repeated, or shifted numbers. Some answers also referred to options from an immediately preceding message without repeating the question. Treating the raw numbers as a strict database would create false mappings.

This document therefore uses three layers:

1. **Final decisions** — the currently approved product direction.
2. **Reconstructed chronology** — what was discussed, challenged, tested, superseded, or retained.
3. **Original-number index** — approximate ranges that help locate a stage of the discussion without pretending every raw number maps perfectly.

Where the precise original question wording was unavailable, the document summarizes the decision theme supported by the user's reply and later confirmations. It does not invent a quotation.

The latest explicit approval governs conflicts. In particular, the final Q98 cutline supersedes earlier production-SaaS scope such as collaboration, background notifications, and broad persistence work.

---

## 2. One-sentence product definition

> A skill-driven, US-only Site Expedition agent that converts structured real-estate requirements into evidence-backed candidate decisions by combining Mireye's cited physical-world facts with selective Earth Engine time/future witnesses, official public data, Google 3D context, and mandatory skeptical review.

This is a screening, comparison, diligence-orchestration, and conceptual-planning product. It is not a legal, engineering, appraisal, inspection, zoning, utility-capacity, water-right, title, or permit certification service.

---

## 3. Why this product exists

People and businesses make expensive real-estate decisions using fragmented information:

- physical hazards and terrain;
- utilities and infrastructure proximity;
- historical environmental behavior;
- logistics and access;
- agricultural or operational suitability;
- property availability and identity;
- local authority and verification requirements;
- what could plausibly be built on the site.

Existing discovery products primarily list properties. Existing diligence tools often display facts. The proposed product should instead run a goal-directed investigation: understand the intended use, screen candidates, reject disqualified sites, deepen uncertain finalists, expose unknowns, challenge the apparent winner, and produce an actionable recommendation.

The Mireye Build Challenge specifically rewards an agent that reasons, decides, and acts over physical-world data, combines Mireye with an unexpected second source, solves a real problem, and identifies a real buyer. A static map or one API call plus a summary is insufficient.

---

## 4. Final approved product boundaries

### Geography and form factor

- United States only because Mireye coverage is US-focused.
- Desktop-first experience.
- Single-user challenge prototype.
- No collaboration, team invitation, roles, or editor mode.
- No account/signup system for the prototype.

### Primary users

- Primary demo buyer: an operations lead or founder of a growing regional distribution business selecting its next facility.
- Broader product users: businesses acquiring operational real estate and individuals evaluating homes or land.
- Home remains an important secondary Mission and must receive domain-appropriate safeguards.

### Missions

The universal engine supports these Mission recipes:

1. Home
2. Farm
3. Warehouse / Light Industrial
4. Data Center
5. Constrained Custom

The engine is universal in orchestration, evidence contracts, skill invocation, and verdict logic. Expertise remains composed from tested capability skills rather than one unrestricted universal prompt.

### Site forms

Each Mission may consider:

- an existing built asset;
- developable land;
- either.

The product must not conflate a location, parcel, building, listing, available property, vacant property, or legally permitted use.

### Entry paths

- **Find a Site:** begin with a Search Region and Mission, obtain lawful or curated candidates, then analyze them.
- **Check a Site:** begin with a user-supplied address or map pin, then analyze it.

Candidate labels:

- `LISTED` — a timestamped authorized source establishes sale/lease availability.
- `USER SITE` — the user supplied the candidate.
- `POTENTIAL` — the location appears promising, but market availability is not established.

### Verdicts

- `STRONG FIT` — every supported mandatory condition passes and the site compares well on preferences.
- `REJECT` — reliable evidence contradicts at least one user-declared mandatory condition.
- `CONDITIONAL` — a material Verification Gap prevents a supported final result.

Unknown, absent, failed, stale, contradictory, or low-authority evidence must never silently become a pass.

---

## 5. Core interaction model

### Structured onboarding, not chat-first onboarding

The user rejected opening the application with a sentence such as “I need a warehouse near Houston.” The approved experience uses:

- Mission tiles;
- Search Region selection;
- Site Form selection;
- budget, size, and geography controls;
- hard constraints;
- weighted preferences;
- sliders only where the underlying data supports meaningful precision;
- discrete bands where fine precision would be misleading;
- toggles for optional investigations and scan depth.

The agent compiles these controls into a **Mission Plan**. The user sees and confirms the plan before expensive work begins. The product may still accept an address or pin, but it should not look like another chatbot.

### Planning-simulator interface

The visual direction is a professional, information-dense planning simulator inspired by SimCity—not a literal cartoon game and not a science-fiction command center.

Approved UI concepts:

- central map or photorealistic 3D planning board;
- candidate cards for discovery and quick comparison;
- swipeable cards may exist as one discovery surface, but cannot carry the entire warehouse/data-center decision;
- structured control deck;
- collapsible Expedition Rail showing active Workstreams and their status;
- side-by-side candidate comparison;
- dynamic scorecards with bars rather than a single opaque score;
- evidence coverage and Verification Gaps separated from Mission fit;
- progressive reveal and live 3D fly-ins;
- professional status language and provenance;
- exact panel placement may evolve during implementation and is not a permanent product requirement.

The UI may show which skills and sources ran, why work deepened or stopped, cost, freshness, and failures. It must not display hidden chain-of-thought or role-play agents as chatbot avatars.

---

## 6. The agent architecture

### The central unit: Site Expedition

A **Site Expedition** is one goal-directed run that may analyze one address, several candidates, multiple cities, a corridor, or a wider Search Region.

The user strongly rejected an architecture that merely calls APIs and writes a summary. The Expedition Engine must:

1. Compile the confirmed Mission Plan.
2. Obtain or accept candidates.
3. Spawn parallel, goal-owned Workstreams.
4. Run inexpensive screening skills first.
5. Reject decisive failures early.
6. Deepen only candidates where more evidence can change the decision.
7. React to contradictions and failures.
8. Replace rejected candidates or widen geography when permitted by the Mission.
9. Commission Earth Engine witnesses only when material.
10. Run Concept Tests on finalists where relevant.
11. Invoke mandatory Skeptic Review before promoting a winner.
12. Reconcile evidence and produce the final decision, counterfactuals, and verification actions.

Workstreams are owned by questions or hypotheses, such as “Can this operation obtain dependable power?” or “Has flood behavior changed?” They are not one agent per API.

### Scan Budgets

- `QUICK` — broad, inexpensive screen.
- `STANDARD` — parallel live investigations and finalist comparison.
- `DEEP` — adaptive witnesses, Source Scout where allowed, Concept Tests, and Skeptic Review.

The approved product behavior is live-first:

- the Expedition and decisions run live;
- source-valid cached evidence may be reused with visible timestamps;
- partial results stream progressively;
- slow work may be shown as pending;
- the prototype does not need production-grade background-job, email, or notification infrastructure.

### The action

The agent acts by changing the state of the real decision:

- rejecting candidates;
- replacing failed candidates;
- allocating investigation budget;
- commissioning a witness;
- narrowing or widening geography;
- promoting a finalist;
- producing an acquisition/verification brief;
- generating and testing a conceptual future site.

External emails, CRM updates, or collaboration actions are unnecessary for the challenge prototype.

---

## 7. Skill-first execution

### The critical correction

An early proposal put live Mireye catalog discovery inside every Expedition. The user rejected this. The final direction is:

- skills contain the agent's operational knowledge;
- the agent should not rediscover Mireye on every run;
- catalog/OpenAPI inspection is development or CI maintenance, used to detect drift;
- runtime skills use reviewed, versioned field manifests and source recipes.

Skills must be short, concise, situational, and invoked only when their information can matter.

Each capability skill should define:

- activation trigger;
- decision question;
- required inputs and geometry;
- exact Mireye fields/endpoints;
- Earth Engine datasets and computations when useful;
- relevant Google or official APIs;
- source authority and independence groups;
- output schema;
- latency and marginal cost expectations;
- retry, fallback, abstention, and stop rules;
- the decision or uncertainty the skill is allowed to change.

Long API schemas belong in adapters or disclosed references, not inside the concise skill body.

### Approved capability-skill direction

Core or near-core skills:

- `resolve-site`
- `screen-site-core`
- `flood-rewind`
- `farm-history`
- `grid-readiness`
- `compare-candidates`
- `scene-context`
- `skeptic-review`

Additional skills after feasibility/testing:

- `route-reality`
- `land-change`
- `labor-access`
- `environmental-record`
- `climate-trajectory`
- `concept-fit`
- constrained `source-scout`

Home, Farm, Warehouse, Data Center, and Custom should be thin Mission recipes that select and parameterize capability skills. They should not become five giant duplicated prompts.

---

## 8. Evidence architecture and source roles

### Mireye

Mireye is the primary present-state evidence broker:

- cited site facts;
- terrain and hazards;
- land cover and buildings;
- utilities, grid, water, and broadband proxies;
- parcel data where cost and match quality justify it;
- field-level source, vintage, confidence, status, and fetch metadata;
- batch screening of supplied candidates.

Current audited catalog facts as of 15 August 2026:

- 306 fields;
- 15 presets;
- `site_selection`: 72 fields;
- `data_center_siting`: 106 fields.

These facts are time-sensitive and must be rechecked during feasibility work.

Mireye does not provide a verified nationwide regional search feed for every commercial, industrial, agricultural, and data-center listing. Candidate acquisition remains a separate adapter or curated/user-supplied input.

### Earth Engine

Earth Engine should add something Mireye does not already supply as a sufficient fact:

- historical change;
- event evidence;
- time-series trajectories;
- custom spatial computation;
- scenario-conditioned future climate;
- a second physical model that exposes disagreement.

Do not call Earth Engine merely to redisplay a current NDVI, elevation, or source already supplied by Mireye.

Important source-independence rule: Mireye JRC water and an Earth Engine computation over JRC data share an underlying source family. The temporal computation adds information but must not be counted as independent corroboration. The evidence graph must record independence groups.

### Google Maps Platform and Google visual products

Approved roles:

- Aerial View: streamed 40-second address orbit where available.
- Photorealistic 3D Tiles / Maps 3D: interactive scene and camera fallback.
- Routes: real road-network time/distance if enabled and successfully tested.
- Maps/geocoding: visual and location context, not market availability or parcel authority.

Google imagery is presentation and human-inspection context. It is not a machine-interpreted analytical source. Licensing and service-specific storage/export rules must be respected.

Google Earth Studio is not required for runtime. Manual editorial clips may be useful, but the tested programmatic orbit came from Aerial View.

### Direct official and other sources

Direct APIs should be called when they add authority, freshness, granularity, or a missing fact beyond Mireye—not simply to reproduce a Mireye field.

Candidate families requiring feasibility review include:

- FEMA and USGS;
- USDA CDL, NRCS Soil Data Access, NASS;
- EPA ECHO, water, sewer, and environmental records;
- EIA-860/861/923, utility/ISO records, and grid queues;
- Census, BLS, and LODES;
- BTS NTAD and FHWA FAF;
- state/local zoning, water-right, permit, and planning systems;
- RentCast or other lawful residential inventory;
- licensed commercial/farm inventory only if credentials and permitted use are real;
- AWS Open Data and GCP datasets where they add nonredundant value.

---

## 9. Past, present, and future

The approved temporal model is:

### `PAST`

Earth Engine skills reconstruct relevant history:

- surface water and flooding;
- crop rotation and rainfall;
- vegetation and drought;
- fire and recovery;
- heat;
- disturbance and development;
- land-use change.

### `PRESENT`

- Mireye cited site facts;
- direct official records when needed;
- current listing/availability assertions where licensed;
- Google/Aerial/3D visual context.

### `FUTURE — ENVIRONMENT`

- published scenario datasets;
- explicit model/scenario/time horizon;
- ranges or ensembles rather than one certain prediction;
- regional-resolution caveats;
- conditional conclusions.

### `FUTURE — PLACE`

- a conceptual building/site preset placed into current context;
- editable program assumptions;
- a Concept Test against known physical constraints;
- generated exterior/interior presentation where useful.

Future output is not permit-ready architecture and must not pretend to know utility capacity, zoning approval, structural design, or constructability not supported by evidence.

---

## 10. Concept Studio

The longer product vision includes:

- `TODAY` — current real site;
- `FIT` — constraints, buildable envelope, and scorecard;
- `FUTURE` — conceptual model placed on the site.

Proposed pipeline:

1. Mireye and Earth Engine establish physical constraints and context.
2. A parametric preset produces coherent conceptual geometry.
3. Generated imagery may produce exterior/interior renders.
4. The agent selects and configures a small number of concepts.
5. Concept Tests compare each concept against known constraints.

Earlier discussion explored ten presets, GLB/IFC/DXF/SVG, agent-created CAD, and uploaded interior drawings. The final challenge cutline is narrower:

- one working future warehouse concept is core;
- several additional presets are stretch;
- existing-building interior specificity requires uploaded drawings/scans and is outside the MVP;
- permit-ready CAD/IFC is outside the MVP.

---

## 11. Tested combination results

Detailed evidence is in [`SKILL_COMBINATION_TEST_RESEARCH.md`](./SKILL_COMBINATION_TEST_RESEARCH.md).

### Strongest proven end-to-end combination

**Mireye flood/terrain facts + Earth Engine flood rewind + DEM disagreement + deterministic decision**

- San Leon: adverse flood/water history and material elevation-model disagreement.
- Austin control: no equivalent water signal and clustered elevation models.
- Existing harness replay produces San Leon `KILL` and Austin `KEEP` under its current demo rules.

Caveats:

- JRC-through-Mireye and JRC-through-Earth-Engine are not independent sources.
- DEM disagreement triggers verification; it does not establish which DEM is correct.
- existing thresholds are demonstration heuristics, not universal calibrated policy.

### Strong newly tested Farm combination

**Mireye current crop/site facts + Earth Engine annual CDL rotation + CHIRPS rainfall history**

- Corrected Iowa pin: cultivated, dominant Corn; annual CDL alternated corn/soy codes.
- Corrected Lubbock pin: cultivated, dominant Cotton; annual CDL remained cotton.
- Tested rainfall averages strongly differed between the sites.
- Initial farm-looking pins landed on uncultivated pixels, proving the need for location/geometry validation.
- SSURGO calls produced retryable timeouts.

This combination adds real temporal information, but does not establish water rights or yield.

### Strong Data Center screening combination

**Mireye grid/heat/water/fiber screen + MODIS observed heat + scenario-conditioned climate path**

- Ashburn and Abilene separated sharply on hot days, voltage context, and water pressure.
- MODIS added observed land-surface heat context.
- one NASA GDDP-CMIP6 scenario path was executed successfully.

Caveat: substation distance, voltage, and counts never prove deliverable MW. Capacity remains a mandatory Verification Gap without a utility/ISO artifact.

### Warehouse status

The Mireye Texas candidate screen worked and produced useful road, rail, substation, fiber, flood, water, and sewer context. However:

- Google Routes is blocked for the configured key;
- legacy Distance Matrix is not enabled;
- true route time remains untested;
- corrected Dynamic World modal built-fraction computation works but lacks independent ground-truth validation;
- availability, truck ingress, utility headroom, and permitted use remain unknown.

Warehouse is still the desired hero Mission, but it must display these unknowns honestly unless feasibility work closes them.

### Visual stack status

- saved University of Chicago Aerial View `videoId`: ACTIVE;
- exact downtown Austin Aerial View: ACTIVE;
- generic university lookup and Austin residential lookup: 404;
- Photorealistic 3D Tiles root endpoint: HTTP 200.

Approved fallback: exact/saved Aerial View lookup, then immediate interactive 3D Tiles.

### Current test-budget state

The latest bounded live pass used 90 Mireye credits and observed 56 remaining credits on 15 August 2026. This balance is drift-prone. The feasibility agent must query the current balance before any authenticated test and use quote endpoints or cached evidence first.

---

## 12. Final approved challenge-prototype narrative

### Hero Expedition: Texas Triangle distribution facility

1. A distribution-business operator configures structured requirements.
2. The agent accepts curated, source-labeled or user-supplied candidates.
3. Goal-owned Workstreams screen hazards, logistics, utilities, and site constraints.
4. A San Leon candidate is rejected through the tested flood-rewind/elevation-disagreement workflow.
5. The agent replaces or deprioritizes rejected candidates and deepens survivors.
6. San Marcos may appear as a provisional finalist under the narrow tested screen.
7. It remains `CONDITIONAL` until route performance, availability, and electrical capacity are verified.
8. Skeptic Review challenges the apparent winner.
9. The UI transitions through `TODAY → FIT → FUTURE` and places one conceptual warehouse preset.
10. Aerial View plays where available; live 3D Tiles provides fallback context.

No fake route, utility-capacity, listing, water-right, zoning, or permit result may be inserted to make the story cleaner.

### Secondary proof

- Farm: current crop/site facts plus annual rotation and rainfall history.
- Data Center: current grid/water/climate screen plus observed heat, while retaining capacity unknowns.
- Home: domain-safe functional constraints and the proven flood-rewind comparison.

Secondary Missions demonstrate adaptation; they need not receive the same visual polish as the hero Expedition.

---

## 13. Final MVP must-haves

### Backend

- skill-first Mission compilation;
- reviewed source/field manifests;
- live Mireye integration;
- selected Earth Engine witnesses;
- source authority, freshness, geometry, resolution, and independence tracking;
- goal-owned parallel Workstreams;
- early veto and candidate replacement;
- selective deepening;
- failure, absence, stale-data, and unknown handling;
- comparison and verdict engine;
- mandatory Skeptic Review;
- one actionable acquisition/verification brief;
- reproducible evidence and decision trace.

### UI proof surface

- Home, Farm, Warehouse, and Data Center Mission tiles;
- structured controls;
- map/3D planning board;
- candidate cards and comparison;
- collapsible Expedition Rail;
- dynamic scorecard bars;
- evidence coverage and Verification Gaps;
- `TODAY`, `FIT`, and one working `FUTURE` concept;
- professional SimCity-like visual direction;
- progressive live status and failures.

### Demo integrity

- real API/dataset workflow;
- honest curated inputs where no lawful inventory feed exists;
- actual live reasoning and decision transitions;
- visible citations and timestamps;
- clear distinction among authoritative facts, proxies, models, and presentation-only content;
- no hidden precomputed result presented as live.

---

## 14. Explicitly excluded from the challenge MVP

- collaboration, invitations, teams, roles, or shared editing;
- production account/signup/authentication system;
- email or external notifications;
- production background-job infrastructure;
- user evidence uploads;
- unrestricted live-source discovery or arbitrary code installation;
- nationwide commercial/farm/data-center listing claims without a licensed source;
- permit-ready CAD, architecture, or engineering;
- ten fully generated architectural presets;
- claims of electrical headroom, enterprise-fiber redundancy, water rights, zoning approval, listing availability, vacancy, building condition, or legal permission without appropriate authority;
- Google imagery machine interpretation or prohibited export/storage;
- scores built from unvalidated thresholds or duplicate underlying sources.

Earlier acceptance of a private Vault and broad export suite belongs to the longer-term product. The challenge MVP needs only lightweight local state if helpful and one actionable brief. Production persistence, full PDF/CSV/GeoJSON/GLB/IFC/DXF export coverage, and account-bound history should follow only after the backend is proven.

---

## 15. Major course corrections during grilling

### Discovery app → decision engine

The user initially considered property discovery with swipeable cards but correctly noted that discovery apps already exist. The differentiated product became site screening, adaptive investigation, and decision support.

### Residential-only → universal Mission engine

The user rejected residential-only scope and introduced farms, warehouses, factories, and data centers. The final answer preserves a universal engine while using tested capability skills for domain knowledge.

### Chat onboarding → structured controls

The user rejected sentence-first chatbot onboarding. The final product begins with Mission tiles, widgets, toggles, bands, and sliders.

### API wrapper → Expedition Engine

The user repeatedly rejected “search plus summary” as non-agentic. The final agent owns Workstreams, adaptive sequencing, candidate replacement, witnesses, and skeptical review.

### Hard-coded rules → concise operational skills

The user objected whenever the system sounded like a fixed decision tree. The final architecture retains deterministic evidence transformations and hard gates while letting concise skills teach the agent which tools, sources, and investigations to invoke.

### Catalog-driven runtime → skill-driven runtime

The user rejected asking the agent to browse Mireye's catalog on every run. Catalog checks moved to development/CI; skills now carry reviewed field recipes.

### Google Earth Studio assumption → tested Aerial/3D split

The conversation initially conflated Earth Studio, Aerial View, and Photorealistic 3D Tiles. Repository artifacts proved the orbital video was Aerial View. The final visual architecture uses Aerial View where available and 3D Tiles as fallback.

### Broad production SaaS → challenge backend prototype

The discussion drifted into accounts, uploads, notifications, Vault behavior, and collaboration. The user corrected the objective: this is a Mireye challenge prototype judged primarily on the backend agent and Mireye use case. Those production features were cut.

### Brainstormed combinations → tested combinations

The user refused to approve source combinations without tests. Live Mireye, Earth Engine, Google, and model-routing checks were then performed. Final recommendations are based on those results and documented failures.

---

## 16. Numbering reconciliation index

This index is intentionally thematic. It prevents false precision while preserving the arc of the numbered grilling.

| Original range | Reconstructed subject | Result |
|---|---|---|
| 1–6 | Usable MVP, audience, coverage ambition, hazards, onboarding, map/cards | Good-looking usable MVP; structured onboarding; broad physical-world information; map plus cards |
| 7–18 | First-time buyers, discovery skepticism, residential vs commercial, universal engine, site forms, data research | Universal Mission engine; business real estate plus Home; site selection over generic discovery |
| 19–29 | Scope ambition, candidate availability, terminology, agent role, flyovers, scorecards | Availability separated from suitability; cinematic 3D; dynamic evidence scorecards |
| 30–40 | Concept Studio, architectural presets, discover/check paths, Earth Engine role | `TODAY/FIT/FUTURE`; land/existing asset support; one engine for discovery and checking |
| 41–48 | Google Maps/data availability, predefined metadata, generated interiors/assets | Google for context rather than inventory; preset-based concepts; generated/curated assets as stretch |
| 49–56 | Hard-coding concerns, agent autonomy, scorecards, physical-world knowledge, feasibility | Agent must select and adapt investigations; evidence bars; physical-world skills |
| 57–63 | Houston limitation, multi-region parallelism, collapsible rails, orchestration visibility | Texas Triangle hero; goal-owned parallel Workstreams; collapsible Expedition UI |
| 64–73 | US-only, desktop, ambition level, collaboration rejection, exports, SimCity presentation | US desktop single-user; no collaboration; professional planning simulator |
| 74–77 | Layout flexibility, collapse/progressive reveal, EE/Google capability use, single user | Layout not permanently fixed; progressive UI; use available Google/EE capabilities lawfully |
| 78–86 | Google product distinction, Vault, live demo, unknowns, validation, Custom, skills, exports | Aerial/3D split; live-first; unknowns never pass; skill registry; broad exports become longer-term |
| 87–92 | Scan behavior, truthful demo, deployment, Home safeguards, uploads, background work | live progressive scans; curated candidates labeled honestly; Home safeguards; uploads/background SaaS cut |
| 93–97 | Skill-first correction, Mireye/EE roles, capability composition, buyer, agent action | concise operational skills; past/present/future; named distribution-business buyer; real decision actions |
| 98 | Final evidence-backed challenge cutline | Approved exactly as summarized in Sections 12–14 |

---

## 17. Questions the feasibility agent must answer before implementation

The next agent must not merely restate the vision. It must diagnose every material claim through source inspection, bounded tests, and failure analysis.

### Mireye

- Which exact endpoints, MCP tools, fields, and presets are current?
- Which existing local Mireye skills are accurate, stale, redundant, or too broad?
- What should each concise operational skill contain?
- What are present credit costs, quotas, parcel-group costs, batch limits, latency distributions, partial-failure patterns, caching rules, and provenance guarantees?
- Can the remaining credit budget support required validation?
- What can Mireye establish versus only proxy?
- How should address, coordinate, parcel, and ambiguity resolution work?

### Earth Engine

- Which tested computations are reliable at parcel, buffer, watershed, and regional scale?
- Which prior experiments are invalid, unstable, or misinterpreted?
- What are realistic interactive and batch latencies?
- Which datasets overlap Mireye and which add independent evidence?
- What geometries, masks, date windows, cloud/radar controls, and scale sensitivity checks are required?
- Can future climate be represented with ensembles and honest uncertainty?
- What are quotas, commercial/noncommercial terms, export constraints, and GCP costs?

### Google / GCP

- Can Routes API be enabled and tested safely on the configured project?
- What billing, key restrictions, quotas, and latency apply?
- What Aerial View coverage/fallback behavior is realistic?
- Can the browser render Photorealistic 3D Tiles reliably in the target stack?
- What content may be stored, streamed, screenshotted, recorded, or exported?
- Which GCP services materially help the agent without becoming infrastructure theater?

### AWS and other data

- Which AWS Open Data datasets add nonredundant evidence?
- Which require significant processing or commercial rights?
- Can AWS credits support any necessary test or pipeline?
- Are EIA, Census, LODES, FAF, EPA, USGS, USDA, state water-right, zoning, or permit connectors accessible, current, and legally usable?
- Which connectors add authority versus merely duplicate Mireye?

### Candidate inventory

- What lawful real-time inventory exists for residential, land, farm, warehouse, industrial, and data-center candidates?
- What credentials, partnerships, display rules, or licenses apply?
- Where must the prototype use curated or user-supplied candidates?
- How will the UI distinguish `LISTED`, `USER SITE`, and `POTENTIAL`?

### Agent and skills

- Can a model reliably route short skills across positive, negative, and ambiguous cases?
- What model/provider is available with current credentials and quota?
- What is the measured routing and reasoning latency?
- Which decisions remain deterministic code/config versus model judgment?
- How are Workstreams parallelized and stopped?
- Can Skeptic Review catch shared-source pseudo-corroboration, stale evidence, and geometry mismatches?
- What happens under API failure, quota exhaustion, partial results, or contradictory evidence?
- What is the expected total cost and wall-clock latency for Quick, Standard, and Deep Expeditions?

### Concept Studio and 3D

- Can one coherent warehouse concept be generated/loaded/placed reliably?
- Which geometry and metadata can be derived lawfully?
- Can a Concept Test operate on separately licensed parcel/constraint geometry without interpreting Google tiles?
- What should be prebuilt versus generated live?
- What are realistic render/model-generation latencies and output formats?

### UI and demo

- Which existing iteration is the best implementation base?
- Can the planning board, cards, Expedition Rail, scorecards, and `TODAY/FIT/FUTURE` views run smoothly on desktop?
- Which demo steps can be genuinely live within two minutes?
- Which slow results require transparent caches?
- Can the app visibly recover from Aerial 404s, source timeouts, missing fields, and conditional outcomes?

### Security, privacy, and operations

- Are API keys server-side and redacted from logs/browser output?
- What user addresses or coordinates are sent to which providers?
- Are cache keys geometry/version aware?
- Can reports reproduce evidence without redistributing prohibited content?
- What tests prevent secrets, paid overages, and misleading claims?

---

## 18. Permissions and guardrails for the feasibility thread

### Authorized

- Read every repository file and relevant local prior-chat/context artifact.
- Inspect configured tool/API availability without printing credentials.
- Call public metadata, documentation, catalog, pricing, quota, and health endpoints.
- Run bounded, low-cost, read-only live API tests after checking quote/balance/cost.
- Run Earth Engine, GCP, and AWS data queries that do not provision durable infrastructure or create material spend.
- Run existing tests, probes, harnesses, servers, and browser previews.
- Create or edit feasibility Markdown reports and clearly identified test artifacts.
- Patch test/probe utilities only when necessary to validate feasibility; do not begin product implementation.
- Spawn specialized research/testing agents for independent categories.

### Requires explicit approval before action

- enabling paid cloud services or changing cloud project configuration;
- provisioning infrastructure;
- purchasing data or credits;
- exhausting a scarce API allowance;
- external messages, registrations, partnership requests, or submissions;
- destructive changes or deletion of material files;
- committing, pushing, deploying, or publishing.

### Prohibited during feasibility

- building the production application;
- presenting cached or synthetic output as a live test;
- exposing secrets in files, logs, tool output, or reports;
- asserting legality, licensing permission, availability, capacity, or authority without primary-source evidence;
- silently converting failed tests into “feasible.”

---

## 19. Required feasibility deliverable

The new feasibility thread should write one principal report, suggested name:

`FULL_FEASIBILITY_DIAGNOSIS.md`

It may create a small `feasibility/` evidence directory if raw sanitized test outputs are necessary. The principal report must remain readable without opening every artifact.

Required report structure:

1. Executive verdict
2. Requirement-by-requirement feasibility matrix
3. Tested architecture and skill graph
4. Mireye endpoint/field/credit/latency diagnosis
5. Earth Engine dataset/computation/latency/independence diagnosis
6. Google Maps, Aerial View, 3D Tiles, GCP, and export-policy diagnosis
7. AWS and direct-public-data diagnosis
8. Candidate-inventory diagnosis
9. Agent model, skill routing, parallelism, and failure-performance diagnosis
10. Concept Studio and 3D feasibility
11. UI/demo runtime feasibility
12. Security, privacy, licensing, and cost risks
13. Test evidence with dates and reproducible commands stripped of secrets
14. What is proven, partially proven, blocked, untested, or infeasible
15. Exact MVP recommendation
16. Exact stretch recommendation
17. Blockers requiring user action
18. Go/no-go verdict before implementation

Every consequential claim should cite a primary source or a reproducible test. The report must distinguish:

- documented capability;
- configured capability;
- successfully tested capability;
- tested failure;
- inferred possibility;
- unavailable or prohibited behavior.

The diagnosis is complete only when every approved MVP component and every significant dependency has one of those statuses, with latency, cost, data-quality, licensing, and fallback implications recorded.

---

## 20. Final approval state

The user explicitly approved the final evidence-backed cutline after Q98. No product implementation should begin until the new exhaustive feasibility diagnosis is complete and the resulting changes, if any, are reviewed.

