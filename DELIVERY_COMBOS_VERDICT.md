# DoorDash / Uber × Mireye × GEE/3D — research verdict (12 Aug 2026)

Two parallel research agents (~30 + ~30 sources). Full detail summarized; decision record.

## API ground truth (what's actually callable)
- **No official DoorDash MCP.** Official agent surfaces: Claude connector (consumer ordering, human-confirmed), `dd-cli` (waitlisted, built for AI agents, Jul 2026), **Drive API** (white-label delivery, INSTANT free sandbox: quote→accept→create→webhooks, JWT auth; production is approval-gated, no timeline). Merge offers a third-party DoorDash-Drive MCP (14 tools).
- **Uber Direct = best demo vehicle.** Self-serve API keys (credit card), and **Robo Courier** test mode simulates a full delivery lifecycle incl. photo/PIN/signature proof-of-delivery + webhooks — cinematic end-to-end demo, no human dispatch, no prod approval.
- **Driver-side data is CLOSED.** No official Dasher/driver API anywhere; DoorDash killed Para (read offer payloads). Gridwise/Solo use Argyle permissioned scraping, ~daily latency. No agent can see a driver's live offers legitimately.
- **The injectable weakness:** both platforms re-geocode the dropoff string as free text (Uber ignores your lat/lng by default!), reject ambiguous addresses with opaque 4xx, have NO "can't find address" event. The only channel for place knowledge is the free-text `dropoff_instructions`/`dropoff_notes` field (Drive's own doc example is a gate code). That field is the seam.

## Problem evidence (real numbers)
- Up to 20% of e-comm packages fail first attempt; ~$17–73 cost each; ~25–50% of delivery failures are address/access-driven (wrong pin, gates, unit maze). USPS UAA mail ~$20B/yr industry cost.
- Apartments ≈30% of US homes; 30+ min/day lost hunting units. Beans.ai owns indoor/complex wayfinding (cuts failures ~25%) but does NOT do hazards/terrain/flood/lighting/dogs.
- Safety: 80 gig workers murdered on the job 2017–22; 361 carjacked; 41% of DC delivery workers harassed/assaulted; USPS logs ~6,000 dog attacks/yr. Amazon has proprietary paw-print dog flags; nobody else.
- **Flood/weather — the emotional anchor:** >50% of flash-flood drownings are vehicle-related (~127/yr); 80% of S. Texas flood deaths at low-water crossings. **Joleen Jarrell, 60, Uber driver, swept off a Mesquite TX bridge Aug 2022 minutes after an $18 fare.** Platforms only have a market-wide kill switch (Grubhub kept dispatching into Hurricane Hilary vs stay-home orders; Grubhub cyclist in waist-deep Ida floodwater = 11M views). Nothing warns per-route/per-address.
- Money leaks: refund abuse ~$103B/yr (restaurants eat it; ~1/3 of delivery refunds estimated fraudulent); "never delivered" violations deactivate honest drivers on customer's word (only defense = drop photo + GPS). Porch piracy ~$37B/yr.

## Prior-art gap
Nobody gives a driver/fleet a per-address PHYSICAL-WORLD briefing. Pieces exist in silos: Beans=indoor units, Amazon=dogs (walled), CAP Index/DoorProfit=crime-records-only, NWS=county polygons, what3words=encoding only. None combine physical environment (terrain, driveway, flood, lighting, gate/complex layout) with 3D/satellite imagery. None visual.

## The 5 plays
- **A. Last-100-feet briefing card** (apartments/gates/rural/night) — broadest everyday pain, most natural 3D-flyover demo. Buyer: platforms/fleet DSPs (failed-delivery $, retention); weak fallback = driver subscription.
- **B. Severe-weather address/route dispatch guard** (the Joleen Jarrell problem) — strongest story + most unique Mireye+GEE fit (flood facts + SAR-through-clouds + flood-frequency; nobody in market has this). Buyer: platform safety/liability, gig-fleet insurers (slow buyers = risk).
- **C. Delivery-dispute truth layer** ("was it really never delivered?") — clearest money trail; = Counter-Adjuster skeleton in a delivery uniform (evidence dossier: pin vs true door in 3D). Buyer: platform fraud teams, merchant SaaS.
- **D. Night-safety per-address context** — real willingness to pay, but redlining optics risk; frame as "best-lit path to door," not neighborhood scoring.
- **E. Rural deliverability re-scoring** — turn red "undeliverable" pin green with an Aerial View approach packet. Buyer: regional carriers, grocery, food-access programs.

## Recommendation
Build the **place-intelligent dispatch layer that sits BEFORE the delivery API call**: verify address vs Mireye parcel-grade geocode → detect gate/apartment-maze/dog/flood-route problem from Mireye+GEE+imagery → auto-write perfect `dropoff_instructions` + choose deliverable/undeliverable action → place via Uber Direct (Robo Courier) or Drive sandbox → webhooks play out on a photorealistic 3D scene. One artifact — "type any US address → cinematic 3D approach briefing (pin-confidence, parking, gate, door, dog/crime flags, live flood/weather on the route) → agent dispatches with the right instructions" — covers A+B+C in one demo. Reuses the parcel-rewind/geocode work and the Aerial View test already in repo.
