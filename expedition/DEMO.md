# Site Expedition — two-minute demo

First walked end to end on **2026-08-15** (warehouse hero). Discovery act
added and re-walked on **2026-08-20**.

- Product: `/` (the `/probe` route is only the test harness)
- Hero run: **replay**; intent parsing, geographies, map pins, all five
  Warehouse screens, Routes facts, Earth Engine witnesses, Aerial 404
  metadata, and Skeptic Review come from labeled caches and checked-in
  fixtures. The demo spends **0 Mireye credits**.
- Optional live garnish: GPT-5.6 Luna proposing the Mission Plan from the
  typed ask. If Luna is down the deterministic parser produces the same
  controls; only the model's narration is absent.
- The quick-tunnel URL expires. Restart the board with this one command:

```bash
cd /home/tayyabkhan/Shared/mireye-challenge && PYTHONPATH=. python3 -m expedition serve
```

## The two-minute path

### 0:00 — Ask in plain words (replay + optional Luna)

1. Open `/`, unlock with the private deployment token, select **Farm**.
2. Type into "What are you trying to do?": **corn plantations in New Jersey**.
3. Click **Read this** and read the response out loud:
   - Luna proposed; the compiler still owns the gates.
   - *"New Jersey has no direct locate coverage; the nearest covered metro
     stands in: new_york."*
   - *"Corn is not a typical crop near new_york in USDA cropland patterns.
     The farm-history witness checks what actually grows there."*
   - Chips show the compiled controls: farm, New York, soil-water priority.

Say: "It keeps my geography, tells me what it can't cover, and warns me the
crop is unusual here — then lets the evidence decide, not the vibes."

Alternates that show range: a cafe ask is refused honestly ("not a use this
agent can screen"), "coffee plantations in us" gets the Hawaii/Puerto Rico
note, "solar farm" is called energy rather than agriculture.

### 0:25 — Real pins, not inventory (replay)

Confirm the plan. The scout dock fills from checked-in OpenStreetMap
captures: four real farm features around the New York band — two of them in
New Jersey, nearest first, each linking to its OSM element. Every label is
**POTENTIAL**; nothing is ever labeled `LISTED`.

Say: "These are cited map features ranked by distance to the need. Market
availability stays an explicit Verification Gap."

### 0:45 — Switch to the Warehouse hero for a full screen (replay)

1. Select **Warehouse / light industrial** (already unlocked).
2. Leave **Standard**, **Existing asset or land**, and **Reject mapped SFHA** selected.
3. Read the compiled Mission Plan before clicking **Confirm Mission Plan**:
   - hard condition: `not_mapped_sfha`;
   - declared route anchors: Port of Houston and San Antonio customer pin;
   - skills include `route-reality`, `flood-rewind`, and `skeptic-review`.

Say: “The user confirms a structured Mission Plan before any screen. These route anchors are declared requirements, not model guesses.”

The board opens on a lightweight Google aerial map. This is deliberately the
fast first paint and does not use WebGL; TODAY 3D is loaded only when selected.

### 0:55 — Four honest Candidate Sites (replay)

Show the four cards and pins in the Texas Triangle: San Leon, San Marcos, Alliance / Fort Worth, and Port Houston (Joliet belongs to the Chicago region and no longer leaks into a Texas search). Every label is **POTENTIAL**. Nothing is labeled `LISTED`; Market Availability remains a Verification Gap.

Say: “This is curated comparison, not fake inventory.”

### 1:05 — Run the Site Expedition (replay)

Keep **Live Mireye** off and click **Run Expedition**. The comparison is deterministic and has no composite score:

1. San Marcos — Conditional, 4 blocking gaps.
2. Port Houston — Conditional, 4 blocking gaps.
3. Alliance / Fort Worth — Conditional, 4 blocking gaps.
4. San Leon — Reject, separated last.

Survivors are ordered by fewer blocking Verification Gaps, then declared road/route preferences. Each has a visible counterfactual.

### 1:15 — San Leon veto and witness (replay)

Select **San Leon coastal pin**.

- Verdict: **Reject · `mapped_sfha`** from FEMA present-state facts.
- `route-reality`: **cancelled — veto already reliable**.
- `flood-rewind`: **done — replay**; JRC monthly water and NASADEM height remain witnesses and do not cause or rescue the veto.
- TODAY scene: **no Aerial orbit at this pin (404); using TODAY photorealistic 3D**.

Say: “The deterministic FEMA hard gate rejects first. Flood-rewind is supporting history, not the veto.”

### 1:25 — Conditional survivor and route reality (replay)

Select **San Marcos I-35 / rail pin**.

- Verdict: **Conditional**.
- Blocking Verification Gaps: Market Availability, electrical capacity, truck ingress, and zoning permission.
- Route FACTs: **3h 03m to Port of Houston** and **52m to the San Antonio customer pin**.
- Truck ingress remains a separate Verification Gap; drive time does not prove a legal truck route or driveway geometry.

Say: “Routes closes route time only. Proximity never becomes capacity, and route time never becomes ingress.”

### 1:35 — Skeptic Review on finalists (replay)

On San Marcos, point to the rail stamp:

`SKEPTIC REVIEW · gemini-3.5-flash-lite · clean`

The same cached comparison-graph review is attached automatically to all four Conditional survivors. The checkbox is only an override to review Rejects too. The model narrates and reviews; it does not change the deterministic verdict.

### 1:45 — Cited acquisition/verification brief (replay)

Scroll the right rail to **Brief**.

- Read the concrete owner/broker, utility, civil/traffic, and zoning actions.
- Show the named source links below the actions (for San Marcos: USGS, FEMA, wetlands/coast, road/rail, and infrastructure sources as present in the packet).

Say: “The brief comes from this trace. It asks for the missing authorities instead of pretending nearby infrastructure is permission or capacity.”

### 1:55 — TODAY and optional FUTURE (replay presentation)

The default **TODAY aerial** map should already be visible. Select **TODAY 3D**
to load Google photorealistic 3D on demand. If 3D content does not become
visible within ten seconds, the board returns to the fast map with an explicit
message. Google imagery is `PRESENTATION` with effect `NONE`; it never scores.

Optional: click **FUTURE** and point to the exact label:

`FUTURE visual concept — parametric box, not a permit. Does not score.`

`FIT` stays disabled because there is no independently licensed parcel/constraint envelope on the default path.

## Check-a-Site acceptance check

This was tested separately because it is the only live Mireye spend in this handoff.

1. Select **Home**, confirm its Mission Plan, and turn **Live Mireye** on.
2. Enter `3605 Winfield Cove, Austin, TX 78704`.
3. Mireye returned a rooftop resolve at `30.236403, -97.780753`; the product matched it to the frozen Austin Candidate Site pin `30.2363775, -97.7807633`, retained the raw geocode metadata, and labeled it **USER SITE**.
4. The live 11-field coordinate screen returned **Conditional**. It did not send the address through `/v1/fetch`.
5. A subsequent replay UI walk reproduced the Conditional result and typed Aerial 404 fallback.
6. An incomplete `Springfield` input returned `clarify` with no selected coordinate. Uncached replay returns `409 replay_cache_miss` rather than inventing a fixture.

Mireye retains a live address resolve for about 30 days; the board says this before resolving. Coordinates are preferred.

## Walk evidence

- `expedition/var/browser-smoke/01-auth-gate.png` — protected-deployment unlock.
- `expedition/var/browser-smoke/02-warehouse.png` — inspected four-card Warehouse board with real Google 3D content.
- `expedition/var/browser-smoke/03-future.png` — inspected rights-cleared GLTF in FUTURE mode.
- `expedition/var/browser-smoke/04-farm.png`, `05-data-center.png`, `06-custom.png` — inspected Mission-specific views without FUTURE leakage.
- `expedition/var/browser-smoke/07-replay-miss.png` — inspected terminal replay-cache-miss state; no stuck running rail.
- `expedition/var/browser-smoke-tunnel/` — the same seven flows passed through protected HTTPS with zero unexpected console/network diagnostics.
- `expedition/var/stress-http.json` — slow-client cutoff, recovery, and bounded replay-load report.
- `expedition/var/board-warehouse-replay.png` — inspected, software-WebGL TODAY 3D, Conditional finalist, route facts, Skeptic stamp.
- `expedition/var/board-san-leon-reject.png` — inspected, San Leon Reject and cancelled route work.
- `expedition/var/board-check-address-replay.png` — inspected, rooftop USER SITE and Conditional replay.
- `expedition/var/board-public-future.png` — inspected from the public tunnel; optional FUTURE label.

Final verification commands:

```bash
PYTHONPATH=. python3 -m unittest discover -s expedition/tests
PYTHONPATH=. python3 -m expedition verify
python3 -m expedition.verify.browser_smoke
python3 -m expedition.verify.scene_startup
python3 -m expedition.verify.stress_http
```

Current result (2026-08-20): **253/253 unit/integration tests**, including the
catered end-to-end harness (14 need-to-pins cases on replay fixtures) and the
adversarial intent suite (refusals, negations, crop belts, model-merge
honesty). Browser smoke passes 8 of 9 steps; the known failure is
`warehouse_3d` (streaming 250 Google 3D tiles inside 18 s in headless
software-rendered Chromium) — it fails identically on commits that predate
this week's changes and has not been reproduced in a real browser. The stress
gate history (16/16 slow-client closes, 80/80 bounded replay load) is from the
2026-08-15 walk.
