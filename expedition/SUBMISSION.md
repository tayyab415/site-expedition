# Site Expedition — Mireye Build Challenge submission

A US-only site-selection agent: describe what you need in plain words, get
honest triage, ranked geographies, real cited map pins, and a deterministic
screening verdict with a cited follow-up brief. Warehouse is the visual hero;
Farm, Home, Data Center, and reviewed Custom missions run on the same engine.

## Buyer

The buyer's-side agent. V1 chair: a buyer's agent vetting sites before an
offer (warehouse/industrial developer, farmland investor, homebuyer's
representative). The agent works for the buyer and against the listing: its
job is to find the kill, not to sell the site. Later courtrooms on the same
skeleton: public adjusters and ag lenders (see `../PRODUCT.md`).

## The agent loop (reason → decide → act)

- **Reason.** GPT-5.6 Luna (Azure) proposes a Mission Plan from the typed ask;
  Vertex Gemini narrates Skeptic Review over the finished comparison. The
  model proposes and narrates — it never decides.
- **Decide.** A deterministic compiler owns every gate: mission recipes,
  hard constraints (FEMA SFHA veto, cultivated-land requirement), size bands,
  verdicts (Reject / Conditional / Strong Fit), and the honesty notes. Code
  re-appends its notes after the model merge, so the model cannot narrate
  them away. Expected outcomes live in held-out gates the engine never reads.
- **Act.** Mireye coordinate screens, Earth Engine witnesses, Google Routes
  facts, OpenStreetMap discovery, Aerial/3D scenes, and a cited
  acquisition/verification brief per finalist.

## Mireye + the non-obvious second sources

- **Mireye API**: `/v1/fetch` coordinate screens (never address fetches on
  the default path), `/v1/geocode` for Check-a-Site, batch quotes before any
  metered call, a hard credit ledger the demo cannot move.
- **Earth Engine as witness, never inventory**: JRC monthly water and
  NASADEM/FABDEM height testify around a flood veto; USDA CDL crop history
  answers "does corn actually grow here"; CMIP6 gives labeled regional
  climate context. Witnesses support or contest a verdict; they never cause
  or rescue one.
- **OpenStreetMap discovery**: candidate pins are real, cited map features
  (each links its OSM element), ranked nearest-need first, always labeled
  POTENTIAL. No listing is ever asserted; Market Availability stays a named
  Verification Gap because there is no lawful self-serve national listed
  feed (`DISCOVERY_SOURCES.md`).
- **Google Maps / Aerial View / photorealistic 3D**: presentation only,
  effect NONE, never scored.

## The wow path (two minutes, zero credits)

Live prototype: https://site-expedition-1027824348124.us-central1.run.app

`DEMO.md` is the walked script. Short version: type **"corn plantations in
New Jersey"** → the agent keeps your geography (New York band covers northern
NJ), tells you what it can't cover, warns that corn is atypical there and
names the witness that will check, then shows real Jersey-side farm pins —
and the Warehouse hero runs a full replay screen ending in a FEMA reject with
a time-lapse flood witness. Refusals are part of the demo: a cafe ask, a
solar farm, or a "coffee plantations in us" ask each get an honest answer
instead of warehouse pins.

## Honesty ledger

- **Replay fixtures are real captures.** Discovery fixtures are live
  Overpass responses captured 2026-08-20 with real OSM ids and element URLs.
  Empty results are never persisted. Mireye/EE/Routes replays are labeled
  caches from real calls; uncached replay returns `409 replay_cache_miss`
  rather than inventing data.
- **Coarse tables are named as such.** Crop belts and state-adjacency
  fallbacks are hand-curated from USDA cropland patterns; they only suggest
  or warn — the CDL witness decides. The roadmap replaces them with Mireye
  batch probes + EE zonal statistics per region.
- **The model never sees held-out gates**, and verdict thresholds live in
  code (`verify/gates.json` is read only by the scorer, after the run).

## Verification

- 253/253 unit/integration tests, including a catered end-to-end harness
  (typed need → intent → plan → replay discovery, wrong-metro and no-LISTED
  guards) and an adversarial intent suite (refusals, negations, crop belts,
  typo asks, model-merge honesty).
- Browser smoke 8/9 (the ninth streams Google 3D tiles in headless
  software-rendered Chromium and predates this week's changes; not
  reproduced in a real browser).
- The demo walk was re-run 2026-08-20 on replay with the credit ledger
  byte-identical before and after.

## Run it

```bash
cd mireye-challenge
PYTHONPATH=. python3 -m expedition serve   # token at expedition/var/access-token
EXPEDITION_TRUST_PROXY=1 cloudflared tunnel --url http://127.0.0.1:8030 --no-autoupdate
```

Authentication is mandatory on public tunnels; the browser exchanges the
private token for an expiring session cookie.

## Deliberately deferred

Licensed national listing inventory (LISTED requires a license), region
ranking from Mireye batch + EE zonal stats (the coarse belts are its
placeholder), screening discovered map pins in the batch run (they screen
one at a time today), and durable production hosting.
