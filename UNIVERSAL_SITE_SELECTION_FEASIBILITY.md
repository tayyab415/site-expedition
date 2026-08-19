# Universal US Site-Selection MVP — Feasibility Report

**Research date:** 14 August 2026  
**Decision horizon:** Mireye Build Challenge submission on 15 August 2026, plus the longer-term product  
**Proposed profiles:** Home, Farm, Warehouse / Light Industrial, Data Center  
**Geographic scope:** United States

## Executive verdict

**Build the universal engine, but sell and label it as universal screening—not universal certification.** A common harness can accept a use case, acquire or accept candidate sites, run profile-specific hard constraints and ranking metrics, explain disqualifiers, and generate a verification plan. The same harness can support all four proposed profiles without becoming four unrelated applications.

What is not feasible is an honest launch claim that the system can certify any US property as legally permitted, utility-ready, water-secure, actively for sale, and physically sound. No nationwide source audited here proves all of those facts. Some gaps can be closed for a particular site, but only by local or provider-specific evidence: an official zoning determination or permit, a utility study or will-serve letter, a state water-right record plus legal review, a current licensed listing plus broker confirmation, or an inspection/property-condition assessment.

That limitation is not fatal. It defines the product:

> **An intent-aware site-selection agent that screens and ranks candidate properties for multiple uses, exposes disqualifiers and unknowns, and produces the next verification actions.**

The long-term universal architecture is feasible. The **15 August submission slice is not the time to build four equal-depth products**. The repository already contains a working, deterministic property-vetting harness and evidence packet (`harness/vet.py`) and a narrower prosecutor-style product definition (`PRODUCT.md`). The credible submission path is to demonstrate that deep workflow on one property scenario, while making the profile registry and verdict model visibly extensible. After submission, add the remaining profiles one at a time behind the same contract.

### Deep-research cross-check

This conclusion was separately stress-tested on 14 August 2026 with Gemini `deep-research-max-preview-04-2026`. The completed run performed 194 Google searches and returned a 48,489-character final synthesis. It was used as a lead generator, not as authority: consequential claims were checked against first-party documentation before inclusion here, and generic thresholds or vendor/pricing assertions without primary support were rejected. **The independent run did not change the verdict:** universal screening architecture is feasible; universal legal, engineering, listing, or condition certification is not.

The cross-check did sharpen six product requirements: show the agent's execution graph; use discrete constraint bands where source precision does not support a fine slider; attach provenance to every default threshold; add housing anti-steering controls; use boundary-aware spatial caching; and consider federal transport and protected-species connectors described below.

## What “universal” can honestly mean

| Claim | Feasible? | Evidence-based interpretation |
|---|---:|---|
| One common intake, evidence, policy, ranking, and report engine | **Yes** | Shared architecture; scenario profiles supply different gates, metrics, weights, and verification actions. |
| Screen arbitrary user-supplied US pins/addresses | **Yes** | Mireye accepts US coordinates/addresses, resolves parcels when quality permits, and batches up to 25 locations. |
| Discover live residential candidates | **Yes, with limits** | RentCast exposes nationwide residential, multifamily, and some vacant-land listings. |
| Discover live farm, warehouse, manufacturing, and data-center candidates nationally from an open feed | **No verified MVP source** | Commercial feeds are licensed/partnered; RentCast expressly excludes these non-residential classes. Use supplied or curated candidates until a feed is licensed. |
| Rank sites for Home, Farm, Warehouse/Light Industrial, and Data Center | **Yes** | Physical, environmental, infrastructure-proximity, demographic, and historical evidence is sufficiently broad for first-pass suitability. |
| Certify zoning permission or entitlement | **No, not nationally** | A zoning label is a lead. A use may still require overlays, conditional-use approval, site-plan review, variances, and jurisdiction confirmation. |
| Certify available electrical MW, water/sewer capacity, or enterprise fiber | **No** | Public data describes infrastructure and reported service, not reserved project capacity or construction commitments. |
| Certify a farm’s water right or well yield | **No, not from national observations** | State systems and legal instruments govern rights; an aquifer/well observation is physical context, not a right or yield test. |
| Certify current sale availability or building condition | **No, not from public geospatial data** | Listing freshness and broker confirmation address availability; an inspection/PCA addresses condition. |

## Feasibility by scenario profile

The profiles below are not different applications. Each is a versioned policy package over the same evidence contract.

### 1. Home

**Automatable screening**

- Candidate discovery for residential, 2–4 unit multifamily, 5+ unit multifamily, and some vacant land through RentCast.
- Address/parcel resolution, mapped flood zone, wetlands, terrain, wildfire and other hazard context, nearby infrastructure, land cover, assessor/parcel attributes when available, and commute/proximity calculations.
- Satellite/history evidence such as long-run surface-water behavior, land-cover change, vegetation/heat context, and imagery-backed contradiction checks.
- Budget, property type, bedrooms, acreage, commute, and hazard-tolerance gates supplied by widgets/sliders.

**Must remain verification actions**

- Offer status and price with the listing agent immediately before action.
- Title, easements, HOA restrictions, insurability/premium, taxes, and lender/appraisal requirements.
- Building systems and structural condition through a home inspection. HUD’s own buyer notice says an appraisal is different from an inspection and urges buyers to obtain a home inspection ([HUD form 92564-CN](https://www.hud.gov/sites/dfiles/OCHCO/documents/92564-CN.pdf)).
- Zoning/permit confirmation for additions, accessory uses, multifamily conversion, short-term rental, or other non-default use.

### 2. Farm

**Automatable screening**

- Parcel area, slope, soil properties and limitations, mapped wetlands/floodplain, historical crop class, vegetation/phenology, rainfall/drought, surface-water history, growing-season climate, road/market proximity, and conservation/protected-area intersections.
- Strong public sources include [NRCS Soil Data Access](https://sdmdataaccess.nrcs.usda.gov/), the [USDA Cropland Data Layer](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php), and the [NASS Quick Stats API](https://quickstats.nass.usda.gov/api).
- Earth Engine is particularly valuable here for time-series crop history, drought, vegetation, water, and land-change evidence.

**Must remain verification actions**

- Water-right ownership, priority, quantity, place/purpose of use, encumbrances, transferability, and current standing.
- Well yield, water quality, pumping cost, and legal authority to drill/pump.
- Agricultural zoning, local land-use restrictions, conservation easements, access, leases, and mineral rights.
- Soil sampling, drainage/irrigation infrastructure condition, and suitability for the user’s actual crop or livestock system.

There is no safe national shortcut for water rights. USGS water APIs publish observations, not legal rights ([USGS Water Data APIs](https://api.waterdata.usgs.gov/)). The Western States Water Council now labels WaDE/WestDAAT a **static historical resource**, last updated in March 2026, and directs users to official state systems for current authoritative information ([WaDE status](https://westernstateswater.org/wade/)). California and Texas already require different authoritative connectors ([California CalWATRS](https://www.waterboards.ca.gov/upward/calwatrs/); [Texas TCEQ water-right permits](https://www.tceq.texas.gov/permitting/water_rights/wr-permitting)).

### 3. Warehouse / Light Industrial

**Automatable screening**

- Acreage/developable-area proxies, flood/wetland/environmental constraints, parcel zoning label, road/rail/airport/port proximity, labor-shed context, nearby transmission/substations/gas infrastructure, likely utility territory, historical utility reliability and price proxies, and mass-market broadband reporting.
- Public environmental and transport evidence can identify obvious conflicts and expensive diligence items early.
- User-entered building specifications—clear height, dock doors, floor loading, yard depth, trailer parking—can be treated as gates when supplied by an owner/broker document.

**Must remain verification actions**

- Permitted use and entitlement for the precise operation. “Light industrial” is still not one uniform use; storage, food processing, chemicals, noise, truck traffic, emissions, and hazardous materials trigger different rules.
- Firm electric/gas/water/sewer capacity, pressure/voltage, redundancy, upgrade cost, and service date.
- Phase I environmental site assessment, geotechnical work, fire-code review, and building/property-condition assessment.
- Broker confirmation that the property is available and that advertised specifications remain accurate.

Do not launch a generic **Factory** profile. Manufacturing subtypes have materially different power, water, wastewater, air-permit, hazardous-material, logistics, and building requirements. Add subtype profiles only after their gate definitions are researched.

### 4. Data Center

**Automatable screening**

- Transmission/substation and generation proximity, likely utility territory, utility-level historical price/reliability context, county-level interconnection-queue context, hazards, terrain, water/climate context, road access, airspace/antenna constraints, and reported mass-market fiber availability.
- Mireye’s live `data_center_siting` preset is a strong broad evidence bundle, and Earth Engine can add heat, drought, water history, land change, terrain, and imagery exhibits.
- These signals can confidently answer “where should engineering diligence start?”

**Must remain verification actions**

- Firm MW, redundant feeder topology, substation headroom, interconnection study, upgrade scope/cost, and energization date.
- Enterprise dark fiber/lit capacity, diverse physical routes, carrier commitments, latency testing, and SLA.
- Water/sewer capacity and cooling-water entitlement, or a validated air-cooled design.
- Zoning/entitlement, tax incentives, noise/emissions constraints, and community/political risk.

EIA plant or substation capacity is not spare deliverable capacity at the parcel. LBNL’s queue data concerns proposed generation/storage interconnections, not guaranteed large-load service. FCC broadband reporting describes mass-market availability, not enterprise route diversity or committed capacity.

## Candidate inventory and listing feasibility

### Best immediate source: RentCast, within its declared scope

[RentCast’s official listing documentation](https://developers.rentcast.io/reference/property-listings) says its API can search active and inactive sale/rental listings by address, city/state/ZIP, or a circular area, return up to 500 records per page, and updates individual listings at least daily (new listings typically within 12–24 hours). It claims at least 96% residential coverage, at least 90% 5+ unit multifamily coverage, and some vacant-land coverage. Its [property-type documentation](https://developers.rentcast.io/reference/property-types) expressly says it does **not** cover office, retail, industrial, manufacturing, agricultural, or other non-residential commercial properties.

That makes RentCast suitable for the Home profile and limited land/multifamily discovery—not a universal inventory source. Its current public pricing page shows 50 free calls/month, then $74 for 1,000, $199 for 5,000, and $449 for 25,000 monthly calls ([RentCast API/pricing](https://www.rentcast.io/api)); the documented hard rate limit is 20 requests/second per key ([rate limits](https://developers.rentcast.io/reference/rate-limits)). Re-check pricing before committing because commercial pricing can change.

### Why RESO, Zillow Bridge, and MLS Grid do not make inventory “free”

- [RESO](https://www.reso.org/reso-web-api/) is a transport/data-dictionary standards body. Its own FAQ says it does **not** provide MLS data; credentials come from local MLSs after agreeing to their licensing policies.
- [Zillow Bridge Listing Output](https://www.zillowgroup.com/developers/api/mls-broker-data/mls-listings/) is invite-only, and access is at each MLS partner’s discretion.
- [MLS Grid](https://www.mlsgrid.com/resources) standardizes licensing and API delivery, but its workflow still requires a data subscription, broker/agent customer authorization, the MLS data-license agreement, compliance rules, and an AI-use addendum where applicable.

These are credible post-MVP paths, not instant nationwide inventory.

### Commercial, agricultural, and specialized inventory

No audited source offered a public, self-serve, nationwide API with transparent licensing for all active farm, warehouse, industrial, manufacturing, and data-center sale/lease listings. [Crexi documents a Sales API](https://api.crexi.com/index.html), so commercial inventory integration is not technically impossible, but it is credential-gated and has no public self-serve price; treat it as a partnership/procurement path, not an available MVP dependency. Other specialized marketplaces and data vendors may also license feeds through sales agreements, but they should not be promised until a contract and permitted-use terms are in hand.

For the MVP:

1. Support user-supplied addresses/pins and CSV candidate lists for every profile.
2. Use RentCast only for profile/classes it officially supports.
3. Use an explicitly curated demo dataset for warehouse, farm, and data-center cards, labeled with its source and capture time.
4. Treat “active listing” as a timestamped provider assertion; add a **confirm with broker/owner** action before any commitment.
5. Do not scrape consumer marketplaces. For example, [Realtor.com’s terms](https://www.realtor.com/terms-of-service) and [Redfin’s terms](https://www.redfin.com/about/terms-of-use) expressly prohibit automated scraping/data extraction.

## Mireye: live capability and cost audit

The live public endpoints were checked on 14 August 2026:

- [Field catalog](https://api.mireye.com/v1/meta/fields): **306 fields, 15 presets**.
- Relevant live preset sizes: `site_selection` **72**, `data_center_siting` **106**, `utilities` **27**, `natural_hazard` **19**, and `grid_interconnect` **29**.
- [Machine-readable plans](https://api.mireye.com/v1/meta/plans): pricing, credit, and parcel-group rules.
- [OpenAPI](https://api.mireye.com/v1/openapi.json): current endpoint inventory.

**Important repository drift:** `skills/mireye/mireye-earth/SKILL.md` still describes `site_selection` as 54 fields and `data_center_siting` as 90. Those counts are stale; runtime code must discover preset membership from the live catalog and cache by ETag rather than hard-code local documentation.

### Useful operations

- `/v1/fetch`: deterministic named fields/presets with value, unit, source URL, vintage, fetch time, confidence, status, and partial failures.
- `/v1/fetch/batch`: the same selection over up to 25 supplied candidates.
- `/v1/runs`: async batch execution and CSV/GeoJSON artifacts.
- `/v1/lookup`: address/coordinate resolution plus parcel when match quality allows.
- `/v1/proximity`: driving/straight-line distance, nearest curated infrastructure, anchor screening, and labor shed.
- `/v1/fetch/quote`: unmetered preflight using the same charging logic as execution.

Mireye does **not** expose a general regional property-for-sale search endpoint. Its batch and screening surfaces enrich candidates supplied by the caller; candidate acquisition remains a separate adapter.

### Current credit economics

| Item | Live rule |
|---|---:|
| Ordinary structured fetch | 1 credit per field per location |
| Natural-language `/v1/ask` | 10 credits |
| Geocode | 1 credit |
| Parcel field group | 300 credits/location on Free, Build, Growth; 150 on Scale, Market; charged once if any parcel-group field is requested |
| Overage on paid plans | $1 per 1,000 credits |
| Free | 5,000 credits/month, 20 rpm |
| Build | $19, 25,000 credits, 60 rpm |
| Growth | $99, 120,000 credits, 300 rpm |
| Scale | $499, 750,000 credits, 600 rpm |
| Market | $4,000, 10,000,000 credits, 1,000 rpm |

Concrete implications from the live memberships:

- `data_center_siting` contains 106 ordinary fields and no parcel-group fields: **106 credits/site**. Adding any parcel-group field makes it about **406 credits/site** on Free/Build/Growth or **256** on Scale/Market.
- `site_selection` currently contains 63 ordinary and 9 parcel-group fields: **363 credits/site** on Free/Build/Growth or **213** on Scale/Market.
- A first-pass 10-field screen over 25 candidates is only **250 credits**. Deepen only the finalists.

Therefore use a staged scan:

1. **Cheap screen:** 8–15 decisive non-parcel fields.
2. **Profile screen:** only the extra fields that can change a gate, rank, confidence, or verification action.
3. **Finalist diligence:** parcel group, broad preset, Earth Engine time series, and generated packet.
4. Cache immutable/slow-changing results by location, field, vintage, source TTL, and the actual evidence geometry. Parcel and boundary evidence must be keyed to the resolved parcel/boundary identifier and dataset version; do not reuse a value from an arbitrary H3/geohash cell as though it described every parcel inside that cell. Surface the predicted credit spend before running.

## Earth Engine: powerful evidence layer, not a legal database

[Earth Engine’s catalog](https://developers.google.com/earth-engine/datasets/catalog) provides large public raster/vector collections and lets the application compute consistent time-series evidence. It is especially strong for:

- Historical surface water and flood-event evidence.
- Crop/vegetation history, drought, rainfall, evapotranspiration, and land change.
- Terrain, slope, elevation-model comparison, heat, wildfire/burn recovery, snow, and urbanization.
- Imagery exhibits for a human-readable diligence packet.

It cannot establish zoning permission, entitlement, a water right, firm utility capacity, active listing status, title, or building condition. Remote sensing can reveal contradictions or change; it does not turn an inference into a legal or engineering commitment.

### Access, cost, and licensing

- Earth Engine requests must run through a Google Cloud project registered for commercial or noncommercial use ([access documentation](https://developers.google.com/earth-engine/guides/access)).
- Noncommercial/research use remains available at no additional platform cost for eligible users. Do **not** assume that a future commercial product qualifies merely because this is currently a hackathon.
- For commercial/self-serve use, Google’s [current pricing](https://cloud.google.com/earth-engine/pricing) offers a Limited plan with usage fees only; listed compute starts at **$0.40/EECU-hour** and storage at about **$0.026/GiB-month**. Basic is **$500/month** with included compute/storage credits. Pricing and eligibility should be rechecked before launch.
- Earth Engine has concurrency, task, memory, aggregation, and queue quotas ([quota documentation](https://developers.google.com/earth-engine/guides/usage)). Interactive computations should be bounded and cached; expensive time-series work belongs in async finalist jobs.
- Every catalog dataset has its own provider terms, attribution, temporal coverage, scale, and accuracy. Earth Engine access does not override those terms.

Google Photorealistic 3D Tiles can make the planning board visually compelling, but they must remain a human-facing context/interaction layer, not a cited evidentiary source. Google's [Map Tiles API policies](https://developers.google.com/maps/documentation/tile/policies) prohibit prefetching/caching, image analysis, machine interpretation, object detection, geodata extraction, and tracing derived 3D objects from the tiles. All analytical geometry therefore has to come from separately licensed data. Current [Maps pricing](https://developers.google.com/maps/billing-and-pricing/pricing) lists 1,000 free Photorealistic 3D Tile requests per month and then $6 per 1,000 in the first paid tier; re-check before launch.

## Other high-value official data/API ingredients

Mireye already wraps many of these. Direct connectors remain useful when the profile needs a field Mireye does not expose, a freshest-available record, or an independent witness.

| Domain | Primary source | Good for | Access/constraint and what it does **not** prove |
|---|---|---|---|
| Flood | [FEMA National Flood Hazard Layer](https://www.fema.gov/flood-maps/national-flood-hazard-layer) | Regulatory flood-map context | National map/service; map vintage and unmapped/local drainage remain issues; not a condition report or insurance quote. |
| Wetlands | [USFWS National Wetlands Inventory](https://www.fws.gov/program/national-wetlands-inventory/wetlands-data) | Mapped wetland screening | Free national data; not a jurisdictional delineation or permit. |
| Elevation | [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) | Terrain/slope/elevation | Free national elevation; resolution/vintage varies; not a survey. |
| Soils | [NRCS Soil Data Access](https://sdmdataaccess.nrcs.usda.gov/) | Soil components and interpretations | Free query service; mapping-unit generalization; field/geotechnical testing still needed. |
| Crop history | [USDA Cropland Data Layer](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php) | Annual crop/land-cover history | Free raster; classification, not proof of lease, yield, or water right. |
| Water observations | [USGS Water Data APIs](https://api.waterdata.usgs.gov/) | Stream/groundwater observations and nearby-well context | Sparse and historical at many sites; not a right, capacity, or well-yield guarantee. |
| Water rights | State agencies; e.g. [California](https://www.waterboards.ca.gov/upward/calwatrs/), [Texas](https://www.tceq.texas.gov/permitting/water_rights/wr-permitting) | Authoritative state records/workflows | State-specific schemas and legal context; no single current authoritative national API. |
| Electric utilities/reliability | [EIA-861](https://www.eia.gov/electricity/data/eia861/) | Utility/county presence, system SAIDI/SAIFI, sales/revenue | Free annual files; not exact service boundary, feeder reliability, tariff quote, or spare capacity. |
| Plants/generation | [EIA-860/860M](https://www.eia.gov/electricity/data/eia860/) | Plant/generator location and capacity context | Nearby generation does not mean deliverable parcel capacity. |
| Grid map | [EIA Energy Atlas](https://atlas.eia.gov/) | Transmission, substation, plant proximity | Proximity/status/voltage context; not headroom or a will-serve commitment. |
| Detailed transmission planning | [FERC Form 715](https://www.ferc.gov/industries-data/electric/general-information/electric-industry-forms/form-no-715-annual) | Planning maps/models | Significant material is CEII-controlled ([FERC CEII](https://www.ferc.gov/ceii)); not an open nationwide product API. |
| Generation queues | [Berkeley Lab Queued Up](https://emp.lbl.gov/queues) | County/region generation-storage queue pressure | Generation/storage projects, not large-load interconnection capacity. |
| Gas pipelines | [PHMSA NPMS](https://www.npms.phmsa.dot.gov/GeneralPublic.aspx) | Public corridor/operator screening | Detailed bulk GIS is restricted; pipeline proximity is not local service or capacity. |
| Broadband | [FCC National Broadband Map downloads](https://broadbandmap.fcc.gov/data-download) | Provider-reported technology/advertised-speed availability | Mass-market reporting, not installed enterprise fiber, diverse routes, SLA, or quote; Location Fabric access is licensed. |
| Environmental facilities | [EPA Envirofacts API](https://www.epa.gov/enviro/envirofacts-data-service-api) and [Facility Registry Service](https://www.epa.gov/frs) | Regulated-facility and contamination screening | A lead for environmental diligence, not a Phase I ESA or clean-site certification. |
| Transportation networks | [BTS National Transportation Atlas Database](https://geodata.bts.gov/pages/ntad) | National road, rail, airport, port, and other transport layers | `OPTIMIZE/INFORM` logistics proximity and network context; not proof of parcel ingress, legal truck routes, usable rail service, capacity, or project approval. |
| Protected species/consultation | [USFWS IPaC](https://ipac.ecosphere.fws.gov/) | Early identification of listed species, critical habitat, migratory birds, and other federal consultation context | `GATE/VERIFY` the federal nexus and consultation path; a critical-habitat intersection is not an automatic veto and does not stop all private development ([USFWS critical-habitat explanation](https://www.fws.gov/project/critical-habitat)). |
| Permit history | [Shovels coverage](https://docs.shovels.ai/docs/knowledge-base/data/geographic/coverage-areas.md) | Normalized building-permit history across roughly 2,000 jurisdictions covering about 85% of the US population | Procurement-only future connector: API plans start at $599/month ([pricing](https://docs.shovels.ai/docs/knowledge-base/getting-started/pricing-structure.md)); history can reveal work/signals, not prove that missing work was unpermitted or that a building is sound. |
| Population/labor | [Census APIs](https://www.census.gov/data/developers/data-sets.html), [BLS public API](https://www.bls.gov/developers/) | Demographics and labor-market context | Aggregate geography and survey/model uncertainty; not worker availability at a site. |

Most federal bulk datasets are free, but APIs have keys, quotas, update schedules, and no product SLA. FCC Fabric, detailed NPMS data, parcel vendors, MLS feeds, and many specialized commercial datasets impose licensing or redistribution restrictions. Record license/attribution metadata alongside every source—not only value and vintage.

## The five alleged gaps: did research close them?

### 1. Zoning permission

**Partially for screening; not for national certification.** Mireye/Regrid may return a parcel zoning designation. Regrid offers nationwide parcel access, but describes its standardized zoning as coverage across major metropolitan areas; its current self-serve Premium plan is $500/month for 2,000 parcel records and includes zoning type/subtype ([API](https://regrid.com/api); [plans](https://app.regrid.com/api/plans)). The [National Zoning Atlas](https://www.zoningatlas.org/) can normalize some local codes, but its [terms](https://www.zoningatlas.org/terms) say the site is not warranted as timely/accurate or suitable for legal, engineering, or survey purposes and prohibit automated scraping/download without permission. Local regimes differ fundamentally: [Houston states that it has no zoning](https://www.houstontx.gov/planning/DevelopRegs/) and that its development codes do not address land use. None of these sources proves that the user’s exact project is permitted as-of-right. The closing evidence is local: current official map/text, overlays, parcel history, and where necessary a zoning verification letter, planning determination, conditional-use approval, or permit.

Product behavior: show `POSTED ZONING: AG` or `LIKELY COMPATIBLE`; never `PROJECT PERMITTED` until the authoritative artifact is attached.

### 2. Actual utility capacity

**No national source closes it.** EIA, transmission maps, utility territory, historical reliability, and tariffs can identify the likely provider and rank infrastructure context. FERC OASIS postings concern transmission-path available/total transfer capability ([18 CFR 37.6](https://www.ecfr.gov/current/title-18/chapter-I/subchapter-B/part-37/subpart-B/section-37.6)), not parcel-level distribution capacity; local distribution is generally outside FERC’s Part II jurisdiction ([16 USC 824(b)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title16-section824&num=0&edition=prelim)). Actual MW, pressure/flow, upgrade scope, redundancy, cost, and energization date require the serving utility’s engineering process and a study/letter/contract.

Product behavior: `PROMISING POWER CONTEXT` plus a generated utility data-request packet; `CAPACITY CONFIRMED` only after the provider artifact is ingested.

### 3. Water rights and well yield

**State systems can close the record lookup; they do not eliminate legal/field verification.** WaDE is now historical/static. [USGS Water Data APIs](https://api.waterdata.usgs.gov/docs/) provide physical observations and monitoring-site metadata, not rights or certified parcel yield. The authoritative record is state-specific, and actual transferability/encumbrance may require legal/title review. Well yield requires a certified record or site-specific drilling/pumping test plus local permitting.

Product behavior: `PHYSICALLY STRONG FIT — WATER RIGHT UNVERIFIED`, never infer a right from rainfall, irrigated pixels, nearby wells, or aquifer depth.

### 4. Active sale status

**A licensed listing feed can supply a current assertion, not an all-property guarantee.** RentCast is useful for its supported classes; MLS feeds can improve local authority after licensing. Commercial/farm inventory remains provider-specific. Public assessor/deed records show ownership and completed transfers, not a current willingness to sell.

Product behavior: show source and `lastSeenDate`; require broker/owner confirmation before an offer or site-control action.

### 5. Building condition

**No audited open national source closes it.** Assessor year/attributes, permit history, aerial imagery, and computer vision can triage visible or historical risk. They cannot validate foundations, roof interiors, MEP systems, code compliance, environmental condition, or load-bearing capacity. The closing evidence is a home inspection, commercial property-condition assessment, engineering report, Phase I ESA, and/or trade-specific inspection.

Product behavior: `CONDITION SIGNALS` and explicit inspection actions; never `BUILDING SOUND` from imagery or assessor data.

## Recommended engine architecture

```text
Widget intake / scenario tile
        ↓
Candidate adapters ── RentCast | user pin/address | CSV | curated/licensed feed
        ↓
Identity resolver ─── coordinate ↔ address ↔ parcel; preserve ambiguity
        ↓
Evidence broker ───── Mireye + Earth Engine + direct official/local connectors
        ↓
Profile registry ──── Home | Farm | Warehouse-Light Industrial | Data Center
        ↓
Deterministic policy engine
        ↓
Eligibility → ranking → unknowns → verification plan → cited packet
```

### Evidence contract

Every metric should carry:

- `value`, `unit`, and `status` (`ok`, `absent`, `failed`, `unknown`).
- source owner, source URL, dataset version/vintage, fetched/observed time, TTL.
- geographic resolution and match quality (point, parcel, census geography, utility system, county).
- confidence and whether the source is **authoritative for this decision** or only a proxy.
- license/attribution/redistribution tag and marginal acquisition cost.
- transformation/method version for Earth Engine-derived metrics.

An LLM may map user-friendly widgets to a profile, select already-approved tools, summarize evidence, and draft verification requests. It should **not** invent thresholds, silently turn unknowns into passes, or make the final eligibility decision. Verdict rules should be versioned code/config, with traceable inputs.

Every threshold must declare one of three origins: **cited authority** (for example, a regulation or adopted user specification), **calibrated model rule** (with training/evaluation cohort and version), or **user-declared constraint**. Uncited generic cutoffs must not become hidden defaults. When the evidence is coarse or uncertain, the control should use honest bands such as `avoid / tolerate / ignore` or `low / medium / high priority`, rather than a deceptively precise slider.

### Verdict semantics

| Semantic | Meaning | Effect |
|---|---|---|
| `VETO` | A verified fact violates a declared hard constraint | Candidate is ineligible; show exact evidence and rule. |
| `GATE` | A mandatory positive requirement | `pass`, `fail`, or `unknown`; unknown is not a pass. |
| `OPTIMIZE` | A preference used only after gates | Normalized profile-specific score and user weight; show sensitivity. |
| `INFORM` | Useful context that should not move eligibility/rank by itself | Display with source and caveat. |
| `VERIFY` | Missing evidence that a human/provider/local process must close | Generate owner, artifact needed, instructions, and status. |

Only candidates that pass every required gate should receive a final relative ranking. A candidate with unknown mandatory evidence may receive a separately labeled **provisional screen**, never rank above an actually eligible site merely because data is missing.

### Agent workflow

1. User selects a scenario tile and configures structured widgets: geography, budget/acreage, hard constraints, preference weights, and scan depth.
2. The agent obtains candidates from a lawful adapter or user input.
3. It runs the cheapest decisive gates first and stops spending on vetoed sites.
4. It deepens the top candidates with parcel data and Earth Engine history.
5. It emits `REJECT`, `ELIGIBLE`, or `CONDITIONAL/VERIFY`, with a side-by-side score breakdown.
6. It acts by producing a cited diligence packet and concrete next requests (zoning letter checklist, utility load letter, water-right lookup, broker confirmation, inspection scope).

This satisfies the hackathon’s reason → decide → act requirement without pretending that the agent itself is the regulator, utility engineer, broker, or inspector.

The UI should expose this run as a compact, inspectable DAG: candidate acquisition → identity resolution → cheap gates → profile evidence → finalist deepening → policy verdict → verification actions. Each node should show status, source/cost, and why it ran or was skipped. This makes the agent harness visible without turning the product into a chat transcript.

### Fair-housing and anti-steering boundary

The Home profile needs an explicit housing-policy guardrail. The [Fair Housing Act overview from HUD](https://www.hud.gov/helping-americans/fair-housing-act-overview) and [42 USC chapter 45](https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter45&edition=prelim) prohibit housing discrimination based on protected characteristics. The app should not infer, solicit, rank, or describe homes using protected-class composition or proxies intended to steer users toward or away from neighborhoods. Avoid demographic desirability, crime-based neighborhood scoring, school rankings used as a steering proxy, and generated language such as “good for families” or “safe neighborhood.”

For residential discovery, use property facts and user-controlled functional constraints—price, bedrooms, accessibility needs, commute time, hazards, parcel/building attributes, and explicitly requested amenities. Keep demographic/labor evidence confined to non-housing site-selection contexts with a documented business need and legal review. Log which features affected ranking so prohibited or accidental proxy use can be audited.

## UI and demo implications

The user’s proposed game-like interface is compatible with the architecture and better than sentence-first chat:

- **Scenario tiles:** Home, Farm, Warehouse, Data Center.
- **Planning board:** map/3D context with selectable candidates and evidence layers.
- **Control deck:** sliders, discrete bands, and toggles for hard constraints and preference weights; every control maps to a profile field/rule and shows whether its cutoff is cited, calibrated, or user-declared.
- **Candidate cards:** image, price/source freshness, gate status, top strength, top disqualifier, and unknown count.
- **Comparison mode:** exact field mappings side-by-side, with ranking sensitivity when weights move.
- **Verification quest log:** zoning, power, water, listing, inspection tasks with artifact upload/status.
- **Agent trace:** a collapsible DAG showing which sources and policy nodes ran, failed, short-circuited, or remain blocked, including credits/cost and evidence freshness.

Avoid swipe-only UX for warehouse and data-center decisions: their decisive facts do not fit a beauty card. Cards can drive discovery, but the planning board/comparison and verification log must carry the product.

The visually impressive demo should show one candidate being rejected for a verified hard fact, another becoming eligible, and a third staying conditional because capacity or entitlement is unknown. That demonstrates honesty and agency better than a universal “87/100 suitable” score.

## Phased MVP recommendation

### Phase 0 — 15 August submission: one deep courtroom, universal contract

Use the repository’s existing property-vetting harness and cited evidence packet. Demonstrate a pin/address, Mireye record, independent Earth Engine contradiction, deterministic KEEP/KILL/HUMAN decision, and action packet. If time allows, put a polished lightweight interface over this existing workflow; do not replace the working core.

Ship in the repository:

- The common evidence/verdict contract (`VETO/GATE/OPTIMIZE/INFORM/VERIFY`).
- One fully working profile mapped to the current coastal/property-vetting demo.
- A profile manifest showing the next three profiles and their required/verification fields, clearly labeled not yet live.
- A two-minute demo emphasizing cited reasoning and the generated action packet.

### Phase 1 — usable discovery MVP

- Home profile with RentCast candidate search plus user pins/addresses.
- Structured onboarding and preference controls.
- Cheap Mireye screen, finalist deepening, map/cards/comparison, and verification log.
- Cache, cost quote, source freshness, failure/unknown handling, and reproducible rule trace.

### Phase 2 — universal screening beta

- Farm, Warehouse/Light Industrial, and Data Center profiles over user-supplied/curated candidates.
- Profile-specific Earth Engine recipes and direct state/local connectors where chosen demo regions justify them.
- Utility/water/zoning request packets and uploaded-artifact state changes.
- Explicitly regionalize claims where a state/local connector provides stronger evidence.

### Phase 3 — inventory and verification partnerships

- Licensed commercial/agricultural listing feeds.
- MLS/broker authorization where residential freshness or display rules require it.
- Utility, enterprise-fiber, local planning/zoning, inspection/PCA, and water-right integrations or human-service handoffs.
- Add manufacturing subtypes only after rules, emissions/wastewater, utility, and building needs are defined.

## Definition of done

The MVP is done when it can:

1. Accept a structured scenario and either lawful discovered candidates or user-supplied sites.
2. Resolve identity without hiding ambiguous addresses or parcel mismatch.
3. Produce deterministic gate results with cited, versioned inputs.
4. Never count `unknown`, `absent`, or `failed` data as a pass.
5. Rank only eligible candidates and explain every material score contribution.
6. Show data age, resolution, confidence, source authority, and licensing constraints.
7. Quote/limit Mireye and Earth Engine spend before deep scans and reuse cached evidence.
8. Generate a concrete verification packet for facts the system cannot close.
9. Demonstrate one reject, one eligible result, and one conditional result end-to-end.
10. Describe itself everywhere as a screening/ranking and diligence-orchestration product—not legal, engineering, appraisal, inspection, or title certification.

## Bottom line

The research supports the user’s central intuition: **a universal site-selection harness is buildable and compelling**, especially when Mireye supplies standardized physical-world evidence and Earth Engine supplies historical/visual witnesses. The earlier pushback remains correct only if “universal” means “the app knows and certifies every decisive fact nationally.” It should not mean that.

The strongest product is universal in **workflow and reasoning**, profile-specific in **rules and evidence**, regional where **authority is local**, and explicit about **what must be verified**. That is both feasible and more useful than a generic property-discovery app.
