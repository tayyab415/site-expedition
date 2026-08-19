# Deep research verdict — idea selection (12 Aug 2026)

Four parallel research agents (~25–45 sources each, primary where possible): frontier scan,
Shadow Scout prior art, Texas paper-trail audit, methane/EPA feasibility. Full agent reports
summarized here; this file is the decision record.

## The board

| Idea | Verdict | Why |
|---|---|---|
| **Counter-Adjuster** (policyholder-side satellite evidence agent) | **BUILD — flagship** | Virgin territory. Insurer side is all satellite-AI (Moody's/CAPE, ZestyAI); policyholder side has nothing. 2025–26 state laws (LA 24-mo imagery freshness, MI disclosure, GA 60-day) created appeal rights 18 months old. >40% of homeowner claims closed with $0 in 2024. Buyers: homeowners, public adjusters, roofers (ecosystem already monetizing rebuttals). Mireye citations = legal ammunition; EE change detection = forensic timestamp; Aerial View/Street View = exhibits. Frontier scan score 9×9. |
| **Title Pirate Interceptor** (vacant-land fraud triage) | **BUILD — second detector, same skeleton** | 62% of 2025 title fraud = vacant land; FBI warnings; ALTA 49 forgery endorsements shipped 2025 → industry now prices this risk and needs signal. Core trick: real owners leave 40 years of satellite fingerprints (mowing, fencing); pirated parcels are untouched. Buyer: title underwriters, per transaction. 9×8. |
| **Shadow Scout** (stealth data-center detection) | **HOLD — narrow gap, crowded, 6–12 mo window** | Commoditized: known-site satellite tracking (SemiAnalysis 5k+ sites + CNN coming; SynMax+IIR weekly 2,600 projects since Jun 2026; Epoch free), records-side land assembly (Enverus "Sites Unseen" 272 GW; WoodMac bought LandGate Jun 2026). Open gap (FAS Dec 2025: "primarily conceptual"): automated *discovery* via change detection over power-proximate parcels + automated ownership forensics, for non-hyperscaler buyers (counties, utilities, journalists). Honest reframe: "detect what the filings don't say" (xAI Memphis: 35 unpermitted turbines, proven only by chartered thermal flights). Risk: DC-pad vs warehouse-pad false positives. |
| **Orbital Whistleblower** (EPA methane dossier filer) | **KILLED as product; salvageable as demo stunt** | EPA Super-Emitter Program frozen until 22 Jan 2027 (no new certifications); methane fee revoked via CRA Mar 2025 + statutory charge delayed to 2034; only 7 notifications ever filed (all Kern County, Jan 2025, all by Carbon Mapper — the only certified notifier, and this is their roadmap). MethaneSAT dead (Jun 2025). Salvage: open automated attribution engine replaying the 7 real Kern County events and reproducing EPA's confirmed operator attributions from public data (EMIT V002 direct from LP DAAC — the GEE mirror is 22 months stale; OGIM in GEE; TX RRC nightly). Buyers weak: NGOs, CalSMP, UNEP MARS. |

## The shared skeleton (this is the harness)

All four are one machine: **adversarial evidence-dossier agent** =
Mireye cited facts (the record + legal ammunition) × EE satellite forensics (the physical truth
+ the timestamp) × jurisdiction-aware reasoning (which law/deadline/venue) → dossier + action.
Parcel Rewind (built, `rewind/`) is the forensic engine. Counter-Adjuster is the flagship skin;
Title Pirate is detector #2; Shadow Scout detector #3 if pursued.

## Key facts to reuse

- **Insurance backlash laws**: Louisiana 24-month aerial-image freshness; Michigan image disclosure; Georgia 60-day nonrenewal notice; NY S9156 pending. NPR/United Policyholders coverage.
- **Moody's acquired CAPE Analytics** (Jan 2025); ZestyAI wildfire model rate-approved in 6 states.
- **Google shipped Geospatial Reasoning agents** (Oct 2025) — generic "ask the Earth" is Google's; defensible ground = adversarial, cited, deadline-driven workflows.
- **Texas paper trail top 5** (for any construction-detection feature): TCEQ stormwater NOIs (>1 acre, days-fresh, operator-named, free), FAA OE-AAA crane filings (point+sponsor, pre-construction, free API), ERCOT monthly ≥75 MW large-load report + free public API (NPRR1267; SB 6 → more PUCT filings from 2026), TX Comptroller Ch.380/381 agreement DB (14-day statutory reporting, names LLCs+sites), city Socrata permit feeds (Austin 3syk-w9eu, Dallas e7gq-4sah, SA). Structural fact: TX counties can't require building permits in unincorporated areas → physical detection matters most exactly where stealth builds go. JETI excludes data centers statutorily.
- **ERCOT correction (live-verified 12 Aug 2026)**: the monthly ≥75 MW large-load status report (NPRR1267, PUCT-approved Jul 2025) is **not yet live** — today only aggregated, entity-anonymized PDF decks exist; watch for the launch (will carry load type "data center", TSP, zone, size range, but no exact location/identity). The usable feed today is the **generation-side GIS Report**: unauthenticated JSON listing `ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=15933` → `mirDownload?doclookupId=<DocID>` (monthly XLSX: interconnecting entity, POI substation, county, MW, COD; what the `gridstatus` Python lib uses). interconnection.fyi mirrors it daily. LBNL Queued Up = generation-only, county-level, 5–18 months stale — backfill only. SB 6 disclosures go to utility/ERCOT, not the public.
- **Tripwire-stack corrections (live-verified 12 Aug 2026)**: TCEQ e-NOIs are effective *immediately* on STEERS e-filing (7-day wait is paper-only) → smaller head start than assumed. The daily Socrata WQ general-permits dataset (`6pm5-am5m`) contains **zero TXR15 construction NOIs** — construction NOIs require browser-grade scraping of `www2.tceq.texas.gov/wq_dpa` (blocks non-browser clients). Texas Comptroller has a free official API (`api.comptroller.texas.gov`, x-api-key) for LLC→taxpayer resolution — cheaper than $1/search SOSDirect; SOS "Weekly New Filings" bulk feed is $20/mo (watch for fresh SPV LLCs). FAA OE-AAA REST API is free/no-auth/real-time (`oeaaa.faa.gov/oeaaa/services/caseList/date/OE?start=...&end=...`, XML with sponsor + decimal lat/lng + `CRANE$*` types; sponsor is often the crane contractor — cluster spatially, don't filter by name). FCC ULS weekly dumps: microwave `LO`/`PA` records carry path coordinates; ASR `RA.dat` embeds the linked FAA study number (direct crosswalk). Extra tells: TX Ethics Commission lobbyist-by-client XLSX (daily, hyperscalers register pre-announcement), USACE 404 public notices have RSS (SWF/SWG districts), STB rail-spur petitions name the served facility, TWDB drillers DB has a nightly full bulk zip.
- **Permit-feed reality check**: Austin excellent (Socrata, lat/lon+valuation, daily), San Antonio good (CKAN API, incl. pre-issuance applications), Fort Worth OK (ArcGIS REST, no coords), **Dallas feed dead since 2020** (Accela UI only), Houston weekly XLSX only. Ch.312 abatements are the actual county-level data-center vehicle but report ~1 yr late — faster: county commissioners-court agendas (must notice before approval). Watch JETI for *dispatchable generation* apps (gas turbines co-locating with DC campuses). TDLR TAS registrations (commercial >$50k) are a statewide proxy where counties issue nothing.
- **Shell-LLC unmasking**: TX SOS ($1/search, bulk orders), Comptroller franchise DB (free), registered-agent clustering; OpenCorporates paid.
- **Methane data plumbing** (if ever revisited): EMIT CH4 in GEE = V001, ends Oct 2024 — stale; V002 via LP DAAC/CMR ends Sep 2025, nothing 2026. Carbon Mapper STAC API (non-commercial, 30-day lag). OGIM v2.7 in GEE (`EDF_OGIM_current`). HIFLD Open shut down Aug 2025 (mirrors: source.coop/seerai). EPA attribution rule: owners/operators within 50 m of plume origin.
- **Hackathon jury insight**: NASA Space Apps 2025 (11.5k submissions) — zero adversarial/forensic parcel agents among winners; the lane is empty.

## Next technical validation (before committing to Counter-Adjuster)

Can we actually date a roof replacement / prove imagery staleness at single-house scale?
- NAIP (0.6–1 m, ~2-yr epochs): roof color/material change should be visible — test pairs.
- Annual satellite embeddings (10 m): does a reroof move the embedding? Test on known cases.
- Sentinel-2 (10 m): likely too coarse alone; brightness delta maybe.
- Fallback wow: even if roof-dating is marginal, *vegetation/structure change dating* around the
  parcel + imagery-freshness audit (what date was the insurer's image?) still powers the appeal.
