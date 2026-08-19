# Handoff — Site Expedition runtime

> **Current status (2026-08-15):** the original six Warehouse handoff steps are
> complete. The broader follow-on slice is also integrated: freshness and
> contradiction semantics, bounded parallel Workstreams, lawful candidate
> replacement/widening, Farm and Data Center temporal witnesses, reviewed
> Custom manifests, expanded onboarding controls, HTTP security controls,
> official EPA ECHO/FRS drill-down, and a dependency-free real-browser gate.
> Current verification is **115 unit tests + 11/11 held-out gates + 8/8 live
> E2E + 7/7 browser flows** on both loopback and HTTPS. The old
> “Build the rest” steps below remain as acceptance-history, not an open queue.

**For:** a new agent session that will build the rest.  
**Date frozen here:** 2026-08-15  
**Repo:** `/home/tayyabkhan/Shared/mireye-challenge`  
**Product root:** `expedition/`  
**Host:** GCP VM `t3-agent-1` (user `tayyabkhan`). The human is **not** on this VM.

Paste the session prompt. Then follow **Build the rest** in order. Read pointed files; do not reopen product vision.

---

## Session prompt (paste this)

```
You are continuing the Mireye Site Expedition challenge build in
/home/tayyabkhan/Shared/mireye-challenge.

Read expedition/HANDOFF.md first. It is the working brief. Then read, in this
order, only what the current step needs:

1. CONTEXT.md — domain language. Use those terms exactly.
2. expedition/DECISIONS.md — frozen build decisions.
3. .scratch/site-expedition-build-plan/mvp-contract.md — commitment classes.
4. The files named in the HANDOFF step you are on.

Build the rest of the hero Warehouse Expedition. Do not start a second product.
Do not reopen grilling. Do not invent LISTED inventory, Strong Fit from
unknowns, or FIT from Google tiles / parcel-group spends.

Workspace rules:
- PYTHONPATH=. from the repo root.
- python3 -m unittest discover -s expedition/tests and python3 -m expedition verify
  stay green after every change.
- Never import expedition/verify/gates.json from engine, UI, or adapters.
- Quote before every metered Mireye call. Soft 20,000 / hard 25,000 / expedition 150.
- No parcel-group fields unless the human opts in.
- Verdicts stay in expedition/verdict.py. Models narrate and review only.
- Google tiles and Aerial are PRESENTATION. They never score.
- Routes go through ADC + quota project gen-lang-client-0261050164, never the Maps key.
- Earth Engine via .venv-ee. Flood-rewind failure must not abort a FEMA veto.
- The product board is / (expedition/ui). /probe is the test harness.
- The human is not on this VM. Keep the app on loopback and put a trusted
  Cloudflare quick tunnel in front of it for a clickable URL. Authentication is
  mandatory; never print expedition/var/access-token. Run e2e yourself. Ask the human only for
  a real blocker (credit raise, Luna deployment, key-restriction change).

Start at HANDOFF step 1 (route-reality). Stop when the two-minute demo script
in expedition/var/DEMO.md exists and you have walked it once on replay.
```

---

## Direction

This is a **skill-driven, US-only Site Expedition**: structured Mission → confirmed Mission Plan → Candidate Sites → cited Evidence Atoms → deterministic Reject / Conditional / Strong Fit → comparison, Skeptic Review, acquisition/verification brief → TODAY scene (Aerial if ACTIVE, else photorealistic 3D).

It is screening, comparison, diligence orchestration, and conceptual planning. It is not a listing service, permit, appraisal, utility-capacity letter, or water-right grant.

**Hero Mission:** Warehouse / light industrial. Home, Farm, and Data Center share the same backend and a thinner board.

**Find a Site** = curated or user list. **Check a Site** = user address or pin. Labels: `LISTED` only with a licensed assertion; otherwise `USER SITE` or `POTENTIAL`. Survivors usually stay **Conditional** on Market Availability, electrical capacity, truck ingress, and (until wired) route time.

Authority stack (do not replace with OBJECTIVE.md / PRODUCT.md — those are earlier skins):

| Read | Why |
|---|---|
| [`CONTEXT.md`](../CONTEXT.md) | Ubiquitous language |
| [`expedition/DECISIONS.md`](DECISIONS.md) | Frozen spend, Routes, models, eval, flood/height |
| [`.scratch/site-expedition-build-plan/mvp-contract.md`](../.scratch/site-expedition-build-plan/mvp-contract.md) | Committed / honest fallback / conditional proof / deferred |
| [`.scratch/site-expedition-build-plan/evidence-contract.md`](../.scratch/site-expedition-build-plan/evidence-contract.md) | Atom schema, independence, Spatial Support |
| [`grilling_session.markdown`](../grilling_session.markdown) | Why the contract looks like this |
| [`FULL_FEASIBILITY_DIAGNOSIS.md`](../FULL_FEASIBILITY_DIAGNOSIS.md) | What was actually tested vs inferred |

Tickets under `.scratch/site-expedition-build-plan/issues/` are planning questions. Several are already answered in code. Prefer the live `expedition/` tree over an open ticket.

Stale on disk (do not treat as current): `expedition/var/E2E_REPORT.md` (written before the 3D board and Concept Test). `OBJECTIVE.md` and `PRODUCT.md` describe earlier products.

---

## Already true (do not rebuild)

Checkable as of 2026-08-15. Re-run the commands rather than trusting this paragraph if the tree has moved.

| Piece | Where | Proof |
|---|---|---|
| Mission Plan compiler | `plan.py` | Warehouse/farm/home/data_center fields + skills + hard constraints |
| Evidence Atom contract | `evidence.py` | Kinds, effects, independence, cache identity |
| Deterministic judge | `verdict.py` | SFHA → `mapped_sfha` Reject; `is_cultivated=false` → `not_cultivated` Reject; always-on gaps force Conditional |
| Credit ledger | `credits.py`, `var/credit_ledger.json` | Soft 20k / hard 25k / expedition 150. Used **103** |
| Engine | `engine.py` | `run_site` / `run_mission`, coverage, scorecard bars (not a composite score). Accepts inline `candidate` for Check-a-Site |
| Mireye adapter | `adapters/mireye.py` | Fixture → `var/cache/mireye` → live `/v1/fetch`. Quote-before-fetch. Never `/ask` for hard gates |
| EE adapter | `adapters/earth.py` | NASADEM + JRC. Loads `.venv-ee`. JRC shares independence group `JRC_GSW` |
| Routes adapter | `adapters/routes.py` | ADC + replay cache, called from the bounded Workstream scheduler |
| Models | `adapters/model.py` | Vertex `gemini-3.5-flash-lite` + `MINIMAL`, then `gemini-3.7-flash` + `LOW`. Azure Luna returns HTTP 400 |
| Held-out gates | `verify/gates.json` + `verify/score.py` | 11/11. Engine/UI must never import this file |
| Concept Test | `concept.py` | 3 cases, no Google, no parcel fetch. `FUTURE=visual_concept`, `FIT=deferred` |
| Product board | `ui/index.html`, `ui/app.js`, `ui/styles.css`, `ui/serve.py` | `/` onboarding → confirm plan → Cesium TODAY 3D (key proxied) / aerial / OSM. FUTURE box overlay. Check-a-Site lat/lng |
| Protected HTTP boundary | `security.py`, `ui/serve.py` | Mandatory bearer-to-HttpOnly session exchange, same-origin enforcement behind trusted HTTPS proxy, body/rate/connection bounds, five-second pre-header timeout |
| Environmental drill-down | `adapters/epa.py` | Official ECHO/FRS facility detail only after a Mireye RMP hit; same EPA independence group; Phase I ESA remains required |
| Browser/load gates | `verify/browser_smoke.py`, `verify/scene_startup.py`, `verify/stress_http.py` | Real Chromium UI screenshots, sub-four-second visible map, protected tunnel flow, slow-client recovery, bounded 16-client replay load |
| Probe harness | `ui/probe.html` | `/probe` — not the product |
| Parametric warehouse | `assets/warehouse.gltf` | CC0 40×80×10 m box |
| Pins + fixtures | `data/candidates.json`, `data/mission_sites.json`, `data/fixtures/mireye/*.json` | See locked pins below |

```bash
cd /home/tayyabkhan/Shared/mireye-challenge
PYTHONPATH=. python3 -m unittest discover -s expedition/tests
PYTHONPATH=. python3 -m expedition verify
PYTHONPATH=. python3 -m expedition serve    # http://127.0.0.1:8030  product /  harness /probe
```

`--live` spends Mireye credits. Replay is the default.

---

## Completed acceptance history

Each step has a completion criterion. Finish the step you are on before starting the next. Keep Home / Farm / Data Center working; they share this engine.

### 1. Wire `route-reality` into the Warehouse Expedition

`adapters/routes.py` is live. `compile_plan(..., route_anchors=...)` already adds the skill. `engine.run_site` never calls it. The board never sends anchors.

- Default Warehouse anchors (declare on the Mission Plan, not inferred): Port of Houston `{lat: 29.73, lng: -95.12}` and a San Antonio customer pin `{lat: 29.424, lng: -98.494}`. A site must not route to itself; skip that anchor when the Candidate Site **is** Port Houston.
- On Standard/Deep Warehouse (and Data Center if cheap): after the core screen, if the site is not already a reliable Reject, call `route_atom` once per remaining anchor. Replay from a small cache under `var/cache/routes/` when `live=false`.
- Attach `route_duration_s` as FACT when Routes returns; otherwise UNKNOWN. Straight-line Mireye road distance stays a different metric. Truck ingress stays a Verification Gap either way.
- Surface the atom on the scorecard / comparison (time or `UNKNOWN`). Live Routes does not spend Mireye credits; still cache it.

**Done when:** `PYTHONPATH=. python3 -m expedition run --mission warehouse --candidate san_marcos_tx` (replay) includes a `route-reality` workstream and a `route_duration_s` atom or an explicit UNKNOWN; San Leon Reject still cancels the workstream; held-out verify stays 11/11.

### 2. Skeptic Review on finalists, not a checkbox

`skeptic_review` in `adapters/model.py` is optional via `review=true`. The contract wants it on survivors before anyone looks like a winner.

- After `run_mission`, run Skeptic on non-Reject packets (or the comparison graph of survivors). Deterministic prechecks first; model second. The model must not change `verdict.py`.
- Show the Skeptic stamp on the rail. Keep the checkbox as an override to force it on Rejects too, not as the only way to get a review.
- Vertex Flash-Lite is the default. Leave Azure Luna unwired until a deployment actually answers.

**Done when:** a Warehouse `run_mission` replay of the five curated sites attaches a Skeptic object to each Conditional survivor without the client sending `review: true`, and San Leon remains Reject with or without Skeptic.

### 3. Aerial lookup, then TODAY 3D

Contract: exact Aerial View if ACTIVE, else Maps 3D. Iteration-7 already recorded Aerial **404** at San Leon and Austin Winfield. That is a documented non-event.

- Server-side lookup only. Retain `videoId` if ACTIVE. Never persist signed playback URLs or video bytes. Kind `PRESENTATION`, effect `NONE`.
- Board: if ACTIVE, offer play; otherwise stay on the existing Cesium 3D path and print “no Aerial orbit at this pin”.
- Reuse the Maps key already proxied in `ui/serve.py`. Key file: `~/.config/mireye-challenge-maps.env`. The key is tile/Aerial/Maps-restricted — Routes through it is `403`.

**Done when:** a site packet can carry `aerial_video_id` as PRESENTATION or a typed 404 note, the 3D board still loads, and verify is green.

### 4. Check-a-Site by address

The board accepts lat/lng as `USER SITE`. Address entry should resolve once, then stop on ambiguity.

- Prefer coordinates for Mireye `/v1/fetch` (addresses sent to Mireye are retained ~30 days).
- Geocode with Mireye `POST /v1/geocode` or `lookup` only when Live is on, or reuse a cached resolve. Read `accuracy_type` / `parcel_grade`. `range_interpolation` is not rooftop. Ambiguity → ask, do not pick.
- Replay with no cache: refuse the screen and say so. Do not invent a fixture.

**Done when:** a Live Check-a-Site of `3605 Winfield Cove, Austin, TX 78704` resolves to the locked Austin pin and screens as Conditional; an ambiguous or out-of-envelope input does not silently land on a neighbor.

### 5. Comparison that is not a score

`run_mission` already returns a comparison table. Add deterministic ordering: Rejects last or clearly separated; survivors ordered by fewer blocking gaps, then by declared preferences (road class, route time if FACT). No composite number. Counterfactual one-liner per survivor (“would Reject if flood-intolerant and zone were AE”).

**Done when:** the Warehouse five-site comparison lists San Leon as the Reject and the other four as Conditional with gap counts, and the board table matches the packet.

### 6. Two-minute demo script

Write `expedition/var/DEMO.md` from a run you actually walked, replay first.

Required beats (contract §11):

1. Warehouse tile → confirm the compiled Mission Plan.
2. Five curated pins with `POTENTIAL` / `USER SITE` labels (not `LISTED`).
3. Run Expedition on replay (or a budgeted live core screen — quote first; ~14 credits/warehouse site at current field lists).
4. San Leon Reject on `mapped_sfha`. Flood-rewind attaches as witness, not as the veto.
5. Survivors Conditional: Market Availability, capacity, ingress; route time FACT or UNKNOWN.
6. Skeptic on finalists.
7. Brief with cited actions.
8. TODAY 3D (Aerial 404 → 3D). FUTURE box optional and labeled “visual concept, not a permit”.

**Done when:** `expedition/var/DEMO.md` names the live vs replay of each beat, the public URL you used, credit delta, and the one command to restart the board.

---

## Locked pins (do not re-guess)

First San Marcos guess `29.879,-97.939` was Zone AE. These are the locked coordinates in `data/candidates.json`:

| id | lat, lng | Role |
|---|---|---|
| `san_leon` | 29.475732, -94.966533 | Warehouse/Home Reject — mapped SFHA |
| `san_marcos_tx` | 29.883, -97.941 | Warehouse Conditional — Zone X, ~12 m road |
| `alliance_tx` | 32.976, -97.319 | Warehouse Conditional |
| `port_houston` | 29.73, -95.12 | Warehouse Conditional |
| `joliet_il` | 41.525, -88.083 | Warehouse Conditional |
| `manhattan_midtown` | 40.748, -73.985 | Farm Reject — not cultivated. Midtown is not farmland. “New York” is not a veto |
| `elba_ny` | 43.077, -78.181 | Farm Conditional — cultivated soybeans |
| `iowa_corn` | 42.032, -93.52 | Farm Conditional |
| `lubbock_cotton` | 33.5, -101.75 | Farm Conditional |
| `austin_winfield` | 30.2363775, -97.7807633 | Home Conditional — 3605 Winfield Cove |
| `ashburn_va` | 39.0438, -77.4874 | Data Center Conditional — capacity gap |
| `quincy_wa` | 47.2343, -119.8525 | Data Center Conditional — capacity gap |

Mission membership: `data/mission_sites.json`.

---

## File map

| Path | Role |
|---|---|
| `expedition/engine.py` | Integrated Expedition orchestration, temporal witnesses, replacement, comparison |
| `expedition/orchestration.py` | Bounded deterministic parallel Workstream DAG and trace |
| `expedition/candidates.py` | Lawful candidate identity, provenance, replacement, and widening |
| `expedition/manifests.py` | Strict reviewed Custom Mission manifests |
| `expedition/security.py` | CSP, origin checks, rate limits, body limits, optional bearer gate |
| `expedition/plan.py` | Mission recipes, structured controls, route anchors, Custom manifests |
| `expedition/verdict.py` | Only place a verdict is decided |
| `expedition/evidence.py` | Atom + gap constructors |
| `expedition/credits.py` | Ceilings |
| `expedition/concept.py` | Concept Test. FIT stays deferred |
| `expedition/adapters/mireye.py` | Present-state `/fetch` |
| `expedition/adapters/earth.py` | Flood-rewind witness |
| `expedition/adapters/temporal.py` | Farm CDL/CHIRPS and Data Center MODIS witnesses |
| `expedition/adapters/routes.py` | Drive time. Call from engine |
| `expedition/adapters/epa.py` | Official EPA ECHO/FRS drill-down after a Mireye RMP hit |
| `expedition/adapters/model.py` | Skeptic / narration |
| `expedition/ui/serve.py` | Protected board + tile proxy + APIs; bounded sockets/threads. Keys stay on the server |
| `expedition/ui/app.js` | Product board client |
| `expedition/ui/probe.js` | Harness only |
| `expedition/verify/gates.json` | Held-out. Scorer only |
| `expedition/verify/score.py` | Compares packet to gates after the run |
| `expedition/verify/e2e_live.py` | Optional live probes |
| `expedition/verify/browser_smoke.py` | Dependency-free Chromium/CDP UI and screenshot gate |
| `expedition/verify/scene_startup.py` | Fast visible-map gate; catches blank Cesium/3D startup regressions |
| `expedition/verify/stress_http.py` | Slow-header, recovery, and bounded replay-load gate |
| `expedition/tests/` | 115 unit and integration tests at current handoff |
| `expedition/data/fixtures/mireye/` | Replay payloads, including `alliance_tx.json` and `port_houston.json` |
| `expedition/var/cache/` | Live-written replay. `var/` is gitignored except the ledger pattern |
| `expedition/var/credit_ledger.json` | Spend truth |
| `iteration-7/serve.py` | Prior 3D + Aerial notes. Copy patterns, not CORS `*` |
| `.venv-ee` | Earth Engine Python. System `python3` has no `ee` |
| `~/.config/mireye-mcp/credentials.json` | Mireye token. Never print |
| `~/.config/mireye-challenge-maps.env` | `GOOGLE_MAPS_API_KEY` |
| ADC + `gcloud auth application-default set-quota-project gen-lang-client-0261050164` | Routes + Vertex |

Mireye skill (catalog, fetch, geocode): `.cursor/skills/mireye-earth/SKILL.md`. MCP server `mireye-earth` is configured. Hard gates still go through `adapters/mireye.py` `/v1/fetch`, not `mireye_ask`.

---

## Spend and secrets

- Ledger at handoff: **244 / 20,000** soft (hard 25,000). The final live E2E spent exactly 43 credits. Warehouse live screen ≈ 14 credits/site at the current 14-field list. Five live Warehouse sites ≈ 70. Quote first.
- Parcel-group / `site_selection` preset is ~300 credits because of parcel. Stay off it.
- Mireye plan on this machine had ~115k remaining after early probes; the **build** ceiling is the ledger, not the vendor plan.
- Never embed the Maps or Mireye key in HTML. `serve.py` already proxies `/v1/3dtiles` and `/g2d/{z}/{x}/{y}`.
- Do not set `Access-Control-Allow-Origin: *` on the tile proxy (iteration-7 did; the contract forbids that shape).

---

## How to serve and show the human

```bash
# start board (do not pkill -f this command in the same shell — it matches itself)
cd /home/tayyabkhan/Shared/mireye-challenge && EXPEDITION_TRUST_PROXY=1 PYTHONPATH=. python3 -m expedition serve
```

Kill by the python PID only. Cloudflare quick tunnel (path may vary):

```bash
~/.t3/tools/cloudflared/2026.5.2/linux-x64/cloudflared tunnel --url http://127.0.0.1:8030 --no-autoupdate
```

Current verified public URL (quick tunnels expire): `https://stylish-connections-twins-requirement.trycloudflare.com/`

Product: `/`. Harness: `/probe`.

The browser is locked until the private token from `expedition/var/access-token`
is exchanged for an expiring HttpOnly session cookie. Do not paste the token
into chat, logs, URLs, screenshots, or documentation.

---

## Release boundary

- This is a secure, shippable hackathon demo, not durable public production hosting.
- The stdlib HTTP server has timeouts, rate/body/connection bounds, and bounded
  backpressure, but it is not a production reverse proxy or TLS terminator.
- The Cloudflare quick tunnel is temporary and expires.
- ECHO/FRS is lagged and incomplete; it never substitutes for a current Phase I ESA.
- Licensed national inventory, authoritative capacity, zoning approval, water
  rights, FIT parcel geometry, and cloud monetary instrumentation remain deferred.
- Progressive result streaming remains unimplemented; completed Workstreams are
  preserved within a finished packet and provider failures are isolated.

---

## Guardrails

- Unknown, failed, stale, or low-authority evidence → Conditional or gap, never a silent pass.
- JRC-through-Mireye and JRC-through-EE are one Independence Group (`JRC_GSW`). They do not corroborate each other.
- Default height witness: USGS 3DEP (Mireye) vs NASADEM (EE). FABDEM is not on the default path.
- Home Mission: no demographic ranking, no labor facts.
- Data Center: never claim deliverable MW, redundant enterprise fiber, or water capacity.
- Farm: water right is always a Verification Gap. Elba NY is cultivated; Manhattan is not.
- FUTURE is a labeled visual concept after `concept.py`. FIT stays deferred until independently licensed parcel/constraint geometry exists without a default-path parcel spend.
- Out of this build: accounts, collab, uploads, notifications, SaaS persistence, marketplace scraping, licensed national inventory, permit-ready CAD, Azure Luna debugging unless asked.

---

## If you are blocked

Ask the human only for: crossing the 20k soft cap, enabling a parcel-group field, changing Maps key restrictions, a working Azure Luna deployment name, or extra vendor credits. Everything else — replay, Routes ADC, Vertex, EE venv, tunnel, board bugs — is on you.
