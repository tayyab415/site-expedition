# Delivery/gig angle — research record (12 Aug 2026)

Two research agents: (1) DoorDash/Uber agent-API capabilities audit, (2) driver pain + last-mile
prior art. This file is the decision-grade summary.

## Capability ground truth (verified against primary docs)

- **No official DoorDash MCP.** Official agent surfaces: Claude connector (consumer ordering,
  human-confirmed), `dd-cli` (official CLI for AI agents, July 2026, **waitlisted**), ChatGPT app,
  Gemini on-device. Third-party: Merge MCP wraps Drive API (14 tools, BYO credentials).
- **DoorDash Drive API**: white-label delivery to arbitrary addresses. Instant free sandbox
  (developer.doordash.com, self-issued JWT), quotes→create→webhooks (DASHER_CONFIRMED etc.),
  `dropoff_instructions` (docs example is literally a gate code), photo/PIN/signature options,
  `dropoff_verification_image_url`. **Production access restricted, no timeline.**
- **Uber Direct**: self-serve signup (direct.uber.com, credit card), OAuth2, official SDK.
  **Robo Courier test mode** = simulated courier traverses full delivery lifecycle incl. all
  proof-of-delivery types, webhooks fire. Best end-to-end demo path, no approval needed.
- **Driver-side data: closed.** No official Dasher/driver API anywhere. DoorDash killed Para
  (removed tip data from app payload). Gridwise/Solo use Argyle permissioned account-linking,
  ~daily latency, no active-offer feed. Do not design around driver's live offers.
- **The documented place-blindness** (our seam): both platforms re-geocode dropoff as free text
  (Uber ignores dropoff lat/lng by default), 4xx field errors on ambiguity, no "courier can't
  find address" event, and the ONLY intelligence channel is free-text dropoff_instructions/notes.

## Problem numbers (sourced in agent report)

- Failed first-attempt deliveries up to 20%; ~$17–18 direct cost each ($73 perishables);
  ~25% of delivery issues from bad address data; access/location-driven failures ~50% per
  access vendors. USPS UAA mail: $1.3B/yr agency cost.
- Apartments ≈30% of US residences; 30+ min/day lost hunting units; Beans.ai claims unit data
  cuts failed deliveries 25%.
- Safety: 80 gig workers murdered 2017–22 (31 in 2022); 361 carjacked/28 killed; 41% of DC
  delivery workers harassed/assaulted; USPS ~6,000 dog attacks/yr, two carrier deaths 2022.
- **Flood anchor story: Joleen Jarrell, 60, Uber driver, drowned Aug 2022 at a Mesquite TX
  low-water crossing minutes after an $18 fare.** >50% of flash-flood drownings are
  vehicle-related; 80% of South-TX flood deaths at low-water crossings. Platforms' only tool
  is a market-wide kill switch (DoorDash suspended San Diego for Hilary while Uber Eats/Grubhub
  kept dispatching against stay-home orders; Ida Grubhub-cyclist video, 11M views).
- Refund abuse ~$103B/yr; ~1/3 of restaurant delivery refunds estimated fraudulent; drivers
  deactivated on "Never Delivered" claims with only photo+GPS as defense.
- Delivery deserts: only 37% of rural residents have any major delivery service; 2.9M people in
  low-income tracts with zero options; rural drop ~$50 vs $10 urban.

## Prior-art gap (verified)

Beans.ai = indoor/complex wayfinding only (no hazards/terrain/flood/lighting/dogs, not 3D).
Amazon's paw-print dog flags = proprietary, walled. Gridwise/Solo = earnings only.
what3words = encoding only. Crime-score micro-apps = police records only.
**Nobody gives drivers or dispatch a per-address physical-world briefing; nothing is visual/3D.**

## The build: "Shotgun" (working name) — the agent riding shotgun on every delivery

One agent, three moments:
1. **Before dispatch (sender/platform side):** address dossier — Mireye geocode `