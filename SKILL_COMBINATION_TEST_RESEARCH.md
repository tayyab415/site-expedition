# Site-selection skill combinations: evidence audit and real-site test plan

**Research date:** 15 August 2026  
**Scope:** Home, Farm, Warehouse / Light Industrial, and Data Center in the United States  
**Constraint:** Repository audit and no-cost/public checks only. No authenticated Mireye, Google Maps Platform, or other metered request was made; no credential was read or printed.

## Verdict

The product architecture should remain **skill-first**, but the final skill recipes should not be declared from brainstorming alone. The repository has enough prior work to identify a small set of promising combinations, and also enough failures to show where a combination is not yet trustworthy.

The best near-term design is:

1. Short capability skills with fixed, versioned Mireye field recipes—not a live catalog-reading ritual and not one huge prompt per Mission.
2. Mireye for cited present-state screening and parcel/site facts.
3. Earth Engine only where it adds a time dimension, an event witness, or a second model—not to re-fetch the same static source.
4. Google Maps Platform for address/route/visual context, never as a substitute for property availability, entitlement, or physical evidence.
5. Direct official APIs only when they add an authority or fact Mireye does not already provide. Calling FEMA, NWI, EIA Atlas, or NRCS directly merely to reproduce a Mireye field is redundant.
6. A mandatory reconciliation skill that distinguishes independent corroboration from two transformations of the same underlying dataset.

The strongest combination already demonstrated end to end is **Mireye flood/terrain facts + an Earth Engine water-history witness + a second elevation model**. It correctly separates a wetting, low-coastal San Leon site from a dry Austin control. Farm phenology, travel-time logistics, utility reliability, future-climate scenarios, and parcel-scale land-change detection still need controlled tests before becoming scoring inputs.

## Live combination tests performed after the audit

The primary agent then ran a bounded live test pass on 15 August 2026. It spent 90 Mireye credits, reducing the free-plan balance from 146 to 56, and made small reviewed field requests rather than calling full presets. Google Maps Platform and Earth Engine checks used the already-configured project credentials. No key or bearer token was printed or written into the repository.

### Home: Mireye present-state screen plus selective historical witness

At **3605 Winfield Cove, Austin**, a six-field live Mireye screen returned a rooftop, parcel-grade geocode; FEMA Zone X; no mapped SFHA intersection; elevation 205.53 m; a 213.54 m2 Overture building footprint; a major road 287 m away; and a hospital 876 m away. At the **San Leon coastal pin**, the same screen returned Zone AE, mapped SFHA intersection, elevation 2.37 m, a hospital 4.28 km away, and a permanent Overture building-footprint failure.

This confirms that a small `screen-site-core` recipe can separate these cases cheaply. The existing Earth Engine `flood-rewind` and DEM reconciliation should activate only for the adverse or uncertain coastal case; running them for every Home candidate would add latency without information gain.

### Farm: Mireye current crop identity plus Earth Engine history

The first farm probe intentionally demonstrated a locator failure mode: points near Ames and Lubbock that looked regionally plausible landed on pixels classified as uncultivated. Corrected pins produced the following live Mireye results:

- Iowa (`42.032,-93.52`): cultivated, five-year dominant crop **Corn**, no current drought polygon, and no mapped SFHA intersection.
- Lubbock (`33.5,-101.75`): cultivated, five-year dominant crop **Cotton**, current **D0** drought, and no mapped SFHA intersection.
- USDA SSURGO prime-farmland lookups timed out for both corrected pins and were correctly returned as retryable failures.

Earth Engine then added information Mireye's five-year mode did not expose. USDA CDL history for 2016-2024 showed the Iowa pin alternating codes 5 and 1 (soybeans/corn) every year, while the Lubbock pin remained code 2 (cotton) every year. CHIRPS annual precipitation averaged approximately **894.5 mm** at the Iowa pin and **465.6 mm** at the Lubbock pin over the tested period.

This is a genuinely complementary combination: Mireye identifies current/typical crop and soil/hazard context; Earth Engine reveals rotation and rainfall history. It does not establish water rights or future yield.

### Warehouse: cheap Mireye screen works; route reality is currently blocked

An eight-field Mireye batch screened three Texas candidates:

- Alliance/Fort Worth: major road 1.04 km, long-haul rail 1.18 km, substation 3.50 km, outside mapped SFHA; EPA water and sewer lookups timed out retryably.
- Port Houston: motorway 1.62 km, long-haul rail 1.04 km, substation 1.07 km, fiber present, outside mapped SFHA; EPA water and sewer again timed out retryably.
- San Marcos: primary road 12 m, long-haul rail 279 m, substation 1.04 km, fiber present, inside mapped water and sewer service areas, outside mapped SFHA.

These facts make San Marcos look strongest under this narrow screen, but they do **not** prove parcel availability, truck ingress, utility headroom, or customer travel time.

The corrected Dynamic World experiment used the spatial fraction of 10 m pixels whose modal top-1 label was `built` within a 1 km buffer, not mean class probability. Built fractions changed from 0.1918 to 0.2326 around Alliance, 0.5251 to 0.5704 around Port Houston, and 0.9409 to 0.9434 around San Marcos between 2018-2020 and 2023-2025. This is now a validly named measurement, but it remains experimental until checked against NLCD or known development and window sensitivity.

Google Routes `ComputeRouteMatrix` returned `403 API_KEY_SERVICE_BLOCKED` for the configured project. The legacy Distance Matrix endpoint also returned `REQUEST_DENIED` because it is not enabled. `route-reality` therefore cannot be claimed as working in the current prototype.

### Data center: strong screen, explicit capacity gap

A ten-field Mireye comparison sharply separated two known contexts:

- Ashburn: 28 days/year above 32 C, 13.05 C annual mean, 1.27 km to a 230 kV substation, 23 substations within 10 km, 230 kV maximum line within the local radius, water supply/use index 0.166, fiber present, and outside mapped SFHA.
- Abilene: 102 days/year above 32 C, 18.18 C annual mean, 1.12 km to a 69 kV substation, 27 substations within 10 km, 138 kV maximum local line, water supply/use index 0.379, fiber present, and outside mapped SFHA.

MODIS added observed land-surface heat context: recent summer daytime LST was approximately 31.95 C around Ashburn and 39.01 C around Abilene. This corroborates a materially different cooling environment, but does not replace design-temperature calculations.

The screen is highly useful for prioritization, yet neither nearby voltage nor substation count establishes deliverable MW. `grid-readiness` must end with a capacity verification gap unless a utility or ISO artifact closes it.

### Future scenario and visual stack

An Earth Engine `NASA/GDDP-CMIP6` test using MIROC6 and SSP2-4.5 successfully compared 2010-2014 with 2035-2039 summer mean daily maximum air temperature. The illustrative deltas were +0.97 C at Ashburn, +2.46 C at Abilene, +1.33 C at the Iowa farm pin, and +1.92 C at the Lubbock pin. This proves the computation path, not a production forecast: a real `climate-trajectory` skill needs an ensemble/range, model/scenario labels, and regional-resolution caveats.

The saved University of Chicago Aerial View `videoId` remains ACTIVE with its 2022-06-19 capture date. Exact lookup for 500 W 2nd St in Austin returned another ACTIVE 40-second orbit captured 2023-12-02. Generic University of Chicago and 3605 Winfield Cove address lookups returned 404. The Photorealistic 3D Tiles root endpoint returned HTTP 200. The proven presentation sequence is therefore: saved or exact Aerial View lookup, then immediate live 3D Tiles fallback.

### Skill-routing model check

A concise four-Mission routing prompt was prepared, but the configured Gemini API could not execute it: Gemini 3.1 Pro returned quota exhausted with a zero free-tier allowance, and Gemini 2.5 Flash reported that it is no longer available to new users. This leaves model-based skill selection untested; it does not invalidate the source tests above.

## Evidence labels used in this report

- **Previously proven:** A raw result and executable method exist in this repository.
- **Newly verified:** Rechecked on 15 August 2026 through a public, unauthenticated endpoint or direct artifact inspection.
- **Partially proven:** The data call worked, but the decision logic, geometry, threshold, or ground truth is not validated.
- **Untested:** Supported by primary documentation, but no valid repository result demonstrates it for this app.
- **Invalid as scored:** A prior output exists, but the transformation or interpretation is not fit for product scoring.

## What the repository actually proves

### Mireye

**Newly verified:** `GET /v1/meta/fields` reports **306 fields and 15 presets**. `site_selection` has 72 fields and `data_center_siting` has 106. The public plan endpoint reports one credit per ordinary fetched field and a separate 300-credit parcel-record charge on the Free/Build/Growth plans when any licensed parcel field is requested. These are current public responses, not counts copied from an old skill ([field catalog](https://api.mireye.com/v1/meta/fields), [plan catalog](https://api.mireye.com/v1/meta/plans)).

This makes two design choices important:

- Skills should carry reviewed field manifests and occasionally validate those manifests against the public catalog during development. The agent should not browse all 306 fields during each Expedition.
- Parcel resolution belongs after a cheap screen or when the user explicitly supplies the site. Accidentally adding `parcel_id`, `parcel_zoning`, `parcel_area_m2`, or parcel geometry to every regional candidate is materially more expensive than an ordinary screen.

**Previously proven:** Raw cached Mireye responses exist for two coordinates with nine fields each and no partial failures:

- San Leon, Texas: FEMA Zone AE, wetland intersection, low elevation, coastal proximity, surface-water permanence, terrain and soil fields ([cache](harness/cache/mireye/san_leon.json)).
- 3605 Winfield Cove, Austin, Texas: FEMA Zone X, no wetland intersection, zero surface-water permanence and well-drained soil ([cache](harness/cache/mireye/3605_winfield_cove_austin_tx.json)).

The broader Ashburn and Quincy Mireye results in `build_site_probe.json` are summary-only, not complete raw API packets. They count as prior evidence that the calls ran, but not as reproducible proof of each field's provenance ([probe summary](ee-explore/build_site_probe.json)).

**Maintenance finding:** The bundled `mireye-earth` skill still says `site_selection` has 54 fields and `data_center_siting` 90. The live counts are now 72 and 106. This validates the proposed split: concise operational skills plus a development-time schema check, not live catalog exploration inside every Mission ([skill](skills/mireye/mireye-earth/SKILL.md)).

### Earth Engine

**Previously proven:** The repository ran hundreds of Earth Engine probes. The consolidated time-series run records 147 successes out of 152 probes; the “deep weird” run records 68 successes out of 80. These prove access and numerous dataset operations, not automatically the correctness of a site-selection score ([best-of summary](ee-explore/BEST_OF.md), [time-series results](ee-explore/deep_timeseries/results.json), [radar report](ee-explore/deep_radar/REPORT.md)).

Decision-relevant results with the strongest receipts are:

| Recipe | Evidence | Status | Proper use |
|---|---|---|---|
| JRC monthly water history at San Leon | Baseline 1985–1999 water frequency 0.03%; 2021 10.84%; breakpoint around 2001 | **Previously proven** | A historical witness after a Mireye flood/wetland screen |
| Same recipe at Austin control | No water observations from 1985–2021 in the tested buffer | **Previously proven** | Negative control for false positives |
| 3DEP vs NASADEM/FABDEM at San Leon | Mireye/3DEP 2.37 m, NASADEM about 2.68 m, FABDEM about 0.75 m | **Previously proven** | Trigger a survey/elevation verification gap; do not pick one model as truth |
| 3DEP vs NASADEM/FABDEM at Austin | Models cluster near 206–208 m | **Previously proven** | Negative control showing disagreement is not automatic |
| CHIRPS drought/wet-year summaries | 30/30 runs succeeded across six regions and multiple periods | **Previously proven** | Regional rainfall anomaly context, after calibration to Mission and season |
| Landsat NDVI/NDWI/NBR trends | 25/25 trend probes and five breakpoint probes succeeded | **Partially proven** | Long-run change candidate; lacks parcel-level labeled validation |
| Sentinel-1 / GPM around Harvey | GPM rain and cloud-independent radar access worked; urban flood extraction was unstable | **Partially proven** | Event witness only with orbit/angle controls and conservative claims |
| MODIS land-surface temperature | Site-versus-ring computations ran | **Partially proven** | Heat-surface context, not ambient design temperature or worker exposure |
| Dynamic World built/bare change | API calls ran | **Invalid as scored** | Rebuild before use; see audit correction below |
| Sentinel-2 harmonic phenology | Three of three harmonic fits failed due to heterogeneous band types | **Untested after repair** | Do not ship as a farm score until fixed and tested against crop labels |

The raw end-to-end San Leon and Austin evidence is in [the harness](harness/runs/) and [Parcel Rewind](rewind/san_leon_rewind.json).

**Newly verified cache replay:** Importing the existing deterministic `judge` function and feeding only the cached Mireye/Earth packets reproduced `KILL` with `TIME` and `HEIGHT` fights for San Leon and `KEEP` with no fights for the Austin control. No API call or file write was involved. This confirms replayability of the current two-case rule, while the threshold caveats below still prevent treating it as a generally calibrated model.

### Google Maps Platform and Aerial View

**Previously proven:** The repository contains a real 40-second University of Chicago Aerial View orbit, with an Aerial View `videoId` and a playback URL whose source is `aerial_view` ([artifact](uchicago-aerial-view.html)). This proves that address-to-orbit playback can work for a supported location.

**Live recheck:** Exact Aerial View lookup succeeds for some addresses/video IDs and returns honest 404s for others; the 3D Tiles root endpoint is enabled. The configured API key is currently blocked from Routes, so no valid route matrix was produced. The following remain unproven:

- geocode and parcel identity agreement between Google and Mireye;
- arbitrary candidate render latency for Aerial View;
- a runtime camera path over Photorealistic 3D Tiles;
- using a Google visual product as analytical evidence.

The products are complementary but must stay separate:

- [Routes API](https://developers.google.com/maps/documentation/routes) can add road-network time/distance where Mireye returns straight-line proximity.
- [Aerial View](https://developers.google.com/maps/documentation/aerial-view/overview) and [Photorealistic 3D Tiles](https://developers.google.com/maps/documentation/tile/3d-tiles-overview) add presentation and human inspection context.
- Neither proves listing status, zoning permission, utility headroom, building condition, or a hazard.
- Maps 3D policy forbids using the tiles for machine interpretation or geometry extraction, and Aerial View policy forbids downloading/storing/caching video bytes. Persist the permitted `videoId`, stream playback, and keep both products out of analytical scoring ([Map Tiles policies](https://developers.google.com/maps/documentation/tile/policies), [Aerial View policies](https://developers.google.com/maps/documentation/aerial-view/policies)).

### Direct official APIs

**Newly verified without keys or paid calls:**

- The [USGS Water Data OGC API](https://api.waterdata.usgs.gov/ogcapi/v0/) is live and advertises monitoring locations, continuous/daily values, field measurements, groundwater-related metadata, and peak flows.
- The [FEMA NFHL ArcGIS service](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer) is live and currently exposes 32 layers.
- [USDA NRCS Soil Data Access](https://sdmdataaccess.sc.egov.usda.gov/) accepted a public tabular SQL query and returned a current catalog row.

These checks prove availability, not that calling them is always useful. FEMA NFHL and common NRCS soil values are already represented by Mireye; direct calls should be made only for a missing detail, an authority check, or a source-freshness investigation.

Official sources that are useful but remain **untested in this app** include [EIA-861](https://www.eia.gov/electricity/data/eia861/) for utility-system reliability and sales, [BTS NTAD](https://geodata.bts.gov/pages/ntad) / [FHWA Freight Analysis Framework](https://ops.fhwa.dot.gov/freight/freight_analysis/faf/) for freight networks and flows, [EPA ECHO](https://echo.epa.gov/tools/web-services) for facility/permit detail, and state water-right systems such as [California CalWATRS](https://www.waterboards.ca.gov/upward/calwatrs/) and [Texas TCEQ](https://www.tceq.texas.gov/permitting/water_rights/wr-permitting).

Primary-source limitations define how those connectors may be used:

- NWI is imagery-derived reconnaissance information and explicitly not a regulatory or legal wetland boundary ([USFWS limitation](https://www.fws.gov/node/264582)).
- The current direct USDA CDL release is annual 10 m CONUS data, while Earth Engine's convenient historical CDL collection is 30 m and currently ends at 2024. Major-crop accuracy is generally reported around 85–95%, not 100% ([2025 CDL metadata](https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_CDL25_FGDC-STD-001-1998.htm), [EE CDL](https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL)).
- FHWA FAF is regional multimodal freight demand, not driveway, turning-radius, or local truck-route evidence.
- EIA-861 reliability is utility/system-level; EIA-860/923 plant generation and capacity do not establish deliverable parcel headroom.
- USGS observations describe measured water conditions, not a water right or guaranteed well/utility capacity.

## Corrections required before more combination testing

### 1. Dynamic World “built percent” is not yet valid

The existing build probe averages Dynamic World's `built`, `bare`, and other probability bands, then treats those means as land-cover fractions. The official dataset says the probability bands sum to one per pixel and recommends thresholding the top-1 prediction for confident class assignment ([Dynamic World catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)). A mean built probability of 0.62 is **not** proof that 62% of the area is built.

Therefore the prior `neighbors`, `dirt`, saturation, and land-competition scores must not be reused. The replacement test should compare at least:

1. area fraction of top-1 `label == built` after a confidence threshold;
2. probability-weighted built exposure, explicitly named as such;
3. a coarser independent reference such as NLCD imperviousness or known building/permit polygons;
4. parcel and neighborhood geometries separately.

### 2. JRC water metrics depend strongly on mask, time window, and geometry

The repository already found that `occurrence` must be unmasked before spatial averaging; otherwise a dry buffer touching a pond can appear water-heavy. San Leon values also differ across 60 m, 1 km, and 2 km buffers and across “latest year,” “late-period average,” and all-history occurrence.

Every `flood-rewind` output must therefore state:

- exact polygon/buffer and pixel scale;
- observation coverage;
- early and late date windows;
- whether masked values were converted to dry or excluded;
- whether the metric is point, parcel, immediate drainage area, or regional context.

JRC in Mireye and JRC through Earth Engine are the **same source family**. A temporal Earth Engine computation adds a new feature, but is not independent corroboration. Sentinel-1/OPERA water, GPM precipitation, or an observed USGS gauge can provide a more independent event witness.

### 3. Radar flood detection is not a generic site skill yet

The deep-radar work proved that clouds do not block Sentinel-1, but also proved that orbit geometry can move VV by roughly 2.5 dB, wind can move open-water return by roughly 11 dB, and urban flooded vegetation can brighten instead of darken. A simple “dark after storm = flooded” rule should not ship.

`event-flood-witness` should activate only when a dated event matters, lock relative orbit/pass and incidence-angle treatment, and return `INCONCLUSIVE` when urban morphology or scene coverage defeats the method.

### 4. DEM disagreement is a verification trigger, not a verdict

FABDEM, NASADEM, and 3DEP represent different models, resolutions, corrections, and vertical references. A large coastal disagreement is valuable because it can flip flood-depth reasoning, but the agent must escalate to authoritative elevation/survey evidence rather than declare the lowest DEM correct.

### 5. Existing score thresholds are demo heuristics

The old probe's water, heat, slope, built, and tree thresholds were not tied to regulation, a user requirement, or a labeled outcome corpus. The new tests should first evaluate **facts and decisions**, not optimize a composite score. A threshold may enter the product only when it is user-declared, source-cited, or calibrated against a named corpus.

## Recommended concise skill registry

These are capability skills, not API wrappers and not giant Mission prompts. Each skill should be a short instruction file backed by versioned field/dataset manifests and deterministic adapters.

| Skill | Activate when | Complementary source combination | Structured output / stop condition | Current status |
|---|---|---|---|---|
| `resolve-site` | New address/pin or identity conflict | Mireye geocode/lookup; Google geocode only for disagreement/visual routing; parcel fields only when needed | canonical point, parcel match quality, boundary, ambiguities; stop on unresolved identity | Mireye coordinate path proven; cross-provider agreement untested |
| `screen-site-core` | Every candidate, with Mission recipe | Small Mireye field set for hazards, terrain, current infrastructure and source provenance | `VETO/GATE/INFORM/UNKNOWN` facts; no Earth Engine by default | Mireye raw proof at two sites |
| `flood-rewind` | Static flood result is consequential, contradictory, coastal/riverine, or user prioritizes flood | Mireye FEMA/NWI/elevation/current water + EE JRC monthly history; optionally Sentinel-1/OPERA/GPM or USGS gauge for an independent event witness | dated trend, geometry, coverage, contradiction, verification action | Strongest proven combination; event extension partial |
| `land-change` | Recent development, disturbance, encroachment, or neighboring competition could alter the decision | EE Dynamic World top-1/thresholded labels + NLCD/NAIP/Sentinel/Landsat; Mireye present land/building context | change type, interval, area, confidence; stop if sources disagree without ground truth | Calls proven; old scoring invalid |
| `farm-history` | Farm Mission after site identity and basic soil/water screen | Mireye soil/crop/farmland fields + direct current USDA CDL / EE historical CDL, Sentinel phenology, GRIDMET plus tested CHIRPS/ERA5 history + state water-right system/USGS observations | crop history, climate anomaly, soil constraints, legal water `UNKNOWN/VERIFIED` | Live Mireye crop identity + EE CDL rotation/CHIRPS rain proven at two pins; phenology and rights untested |
| `route-reality` | User supplies maximum travel time or logistics/commute matters | Mireye straight-line road/rail/airport context + Google Routes matrix to user-selected anchors + NTAD/FAF regional context | actual route time/distance and failure/coverage; never infer parcel ingress | Current Google key blocked from Routes; not available in prototype |
| `labor-access` | Warehouse/Data Center Mission has staffing constraints | Mireye tract/county employment context + Census LODES workplace/residence flows + Google Routes from selected labor sheds | workplace/residence job context and route-time bands; never a claim that workers are available | Untested; exclude from Home ranking |
| `grid-readiness` | Warehouse or Data Center power/redundancy is material | Mireye transmission/substation/utility/price/queue fields + EIA-861 system reliability + utility/ISO verification target | proximity, likely provider, historical system reliability, explicit capacity unknown | Live Ashburn/Abilene proximity and climate screen proven; EIA reliability/capacity untested |
| `environmental-record` | Mireye reports nearby Superfund/brownfield/RCRA/UST or industrial Mission requires it | Mireye proximity screen + EPA ECHO/FRS record detail | facility identity, distance, regulatory record, Phase I verification gap | Mireye catalog capability verified; direct drill-down untested |
| `climate-trajectory` | Farm water, Home heat/fire, or Data Center cooling assumptions are decision-sensitive | Mireye present design climate + EE GRIDMET/ERA5/CHIRPS history + [NASA GDDP-CMIP6](https://developers.google.com/earth-engine/datasets/catalog/NASA_GDDP-CMIP6) scenarios | historical baseline plus scenario-conditioned range; never a single “prediction”; CMIP6 is regional (~28 km), not parcel-scale | Single-model scenario path proven; ensemble/range and decision calibration untested |
| `scene-context` | A selected candidate is shown to the user | Aerial View lookup; fallback interactive 3D Tiles; Earth Engine/Open imagery only for analytical layers | playable/interactive scene plus attribution; contributes zero score | Two active Aerial videos, 404 fallback cases, and 3D Tiles endpoint verified live |
| `skeptic-review` | Before finalist promotion | Evidence graph only—no new source unless a contradiction is identified | flags shared-source pseudo-corroboration, stale data, geometry mismatch, unknown hard gates | Logic specified; not yet benchmarked |

Thin Mission recipes should only select and parameterize these skills. For example, Home usually composes `resolve-site`, `screen-site-core`, `route-reality`, conditional `flood-rewind`, `scene-context`, and `skeptic-review`; Farm additionally activates `farm-history` and often `climate-trajectory`.

## Multi-source combinations by Mission

| Mission | First pass | Selective deepening | Truly nonredundant external authority | Avoid |
|---|---|---|---|---|
| **Home** | Mireye parcel/building/hazard facts and functional POIs | JRC/Sentinel flood history, heat/land-change only when it changes a user constraint; Google Routes for commute; Aerial/3D for inspection context | Current listing/broker, local permit/zoning, inspection/insurance artifacts remain outside the automated screen | Demographic desirability; direct FEMA/NWI duplicate calls; treating imagery as condition proof |
| **Farm** | Mireye parcel area, soils, farmland, flood/wetlands, dominant crop, drought | Direct current CDL + EE historical CDL rotation, fixed Sentinel phenology, GRIDMET/CHIRPS/ERA5 seasonal history; Routes to selected markets | State water-right registry and, where useful, USGS observations; crop-specific NRCS interpretation beyond the Mireye point screen | Inferring water rights from green pixels/rainfall; treating crop labels as exact parcel truth |
| **Warehouse / Light Industrial** | Mireye developability, hazards, roads/rail, utilities, EPA proximity, labor context | Routes matrix to ports/interstates/customers; FAF for regional freight, LODES for labor flows; EE flood/event and land-change witnesses; EIA-861 reliability | Serving utility and local planning; EPA ECHO detail after a hit | Nearest-line distance as available capacity; FAF as driveway access; regional SAR change as parcel condition |
| **Data Center** | A reviewed subset of the Mireye data-center fields: grid, climate, water, fiber, hazard, environmental and residential context | EIA-861 system reliability; EE heat/water/land trajectory; future climate scenarios; regional competition only after land-change method passes | Utility large-load study/will-serve, enterprise-fiber quote/diverse routes, water/wastewater commitments | Calling all 106 fields blindly; nearby plant/substation as MW headroom; FCC mass-market fiber as enterprise redundancy |

## Real-site test matrix

The matrix deliberately mixes positive controls, known adverse sites, and currently weak/failed recipes. A “pass” means the skill produces the right evidence contract and honest uncertainty—not that a site receives a high score.

### Home

| ID / real site | Skills and sources under test | Oracle and acceptance criteria | Status |
|---|---|---|---|
| H1 — **3605 Winfield Cove, Austin, TX** (`30.2363775,-97.7807633`) | `resolve-site` → Mireye core → `flood-rewind` → DEM reconciliation | Preserve Mireye Zone X/no wetland/zero water history; Earth Engine must remain negative; DEM difference must not create a false alarm; no protected/demographic feature may enter rank | **Previously proven** for Mireye + water/DEM; routing/visual untested |
| H2 — **San Leon, TX coastal pin** (`29.475732,-94.966533`) | Mireye FEMA/wetland/elevation + EE JRC history + optional dated radar/precipitation | Surface the AE/wetland facts, increased historical water signal and DEM disagreement; classify as adverse or conditional under a flood-intolerant user rule; never claim survey-grade height | **Previously proven** for core; event witness partial |
| H3 — **Round Rock suburban pin** (`30.5083,-97.6789`) | Mireye core + Google Routes commute anchors + Aerial/3D coverage + heat context | Route time must differ from straight-line distance and preserve departure-time assumptions; visuals must affect presentation only; heat output must say land-surface temperature | **EE-only partial**; Mireye/Routes/Aerial untested |

### Farm

| ID / real site | Skills and sources under test | Oracle and acceptance criteria | Status |
|---|---|---|---|
| F1 — **Iowa corn-belt pin** (`42.0,-93.5`) | Mireye soil/farmland/crop + direct 2025/EE historical CDL + repaired Sentinel phenology + GRIDMET/CHIRPS/ERA5 | CDL rotations and phenology must agree within declared resolution or return contradiction; harmonic fit must run on typed homogeneous bands; compare against annual CDL labels, not visual intuition | Monthly Sentinel and climate calls proven; **harmonic phenology failed**; current direct CDL untested |
| F2 — **Central Valley agricultural pin, CA** (`36.5,-121.2`) | Mireye soil/water screen + Landsat trend + GRIDMET/CHIRPS/ERA5 + CalWATRS lookup | Separate observed vegetation/rain history from legal water right; a green/irrigated history cannot clear the water-right gate; trend stability tested under alternate windows | Landsat trend proven; Mireye/GRIDMET/right lookup untested |
| F3 — **Texas Hill Country pin** (`30.0,-98.5`) | Mireye terrain/soil/water + Landsat/GRIDMET/CHIRPS/ERA5 + TCEQ/USGS water context | Correctly distinguish drought/rainfall history, nearby observations and legal rights; sparse monitoring becomes `UNKNOWN`, not absence of water | EE historical calls proven; combined decision untested |

### Warehouse / Light Industrial

| ID / real site | Skills and sources under test | Oracle and acceptance criteria | Status |
|---|---|---|---|
| W1 — **San Leon coastal pin** (`29.475732,-94.966533`) | Mireye core/utilities + `flood-rewind` + Routes to selected highway/port anchors | A hard flood rule must reject before expensive logistics deepening; the agent should spend no routing/grid follow-up after a decisive veto | Flood verdict proven; short-circuit ordering and logistics untested |
| W2 — **Port Houston region** (`[-95.25,29.60,-94.95,29.80]`, then select a parcel) | Mireye parcel/site screen + Routes matrix + NTAD/FAF + event-flood witness | Route time to user-defined port/interstate must add information beyond nearest-road distance; regional SAR cannot be assigned to a parcel until a parcel geometry is chosen | Regional SAR previously proven; site combination untested |
| W3 — **Dallas North growth pin** (`33.05,-96.80`) | Mireye core/utilities/labor + corrected `land-change` + Routes to Texas Triangle anchors | Thresholded-label/NLCD change should identify a stable or changing area consistently across window choices; old mean-probability score must not be reproduced | Dynamic World calls proven; **old score invalid** |

### Data Center

| ID / real site | Skills and sources under test | Oracle and acceptance criteria | Status |
|---|---|---|---|
| D1 — **Ashburn, VA data-center cluster** (`39.0438,-77.4874`) | Selected Mireye grid/water/fiber/climate fields + EIA-861 + corrected land-change + climate trajectory | Recognize strong infrastructure context without claiming spare MW; EIA reliability must be labeled system-level; land competition must survive corrected classification and known-site checks | Mireye summary + EE calls partial; reliability/land method untested |
| D2 — **Quincy, WA data-center cluster** (`47.2343,-119.8525`) | Same as D1, emphasizing water/cooling/agricultural context | Distinguish low ambient cooling burden from water availability/rights; no “available capacity” claim from substation count; compare against Ashburn to test Mission adaptation | Mireye summary + EE calls partial |
| D3 — **Mesa east-fringe pin, AZ** (`33.4152,-111.6310`) | Mireye data-center subset + corrected land change + water/climate trajectory + utility verification target | Heat/water facts should deepen; future scenario must show model/scenario range; nearby infrastructure cannot clear water or MW gates | EE land call partial; rest untested |

## Test protocol and pass criteria

### Geometry and truth controls

1. Resolve the input once, save point plus parcel polygon and match quality, and run every parcel-scale source on the same geometry.
2. Use separate named geometries for parcel, 500 m surroundings, travel network, watershed, and regional climate. Never compare numbers whose spatial supports differ without saying so.
3. Each skill must have at least one positive control, one negative control, and one ambiguity/failure case.
4. Ground truth must come from a source capable of answering the claim: known crop labels/field records for phenology, observed event footprints for flood, current utility or planning artifacts for capacity/permission. Visual agreement alone is not validation.

### Evidence contract

Every observation should carry:

- source owner and exact dataset/API identifier;
- observed/data vintage and fetch time;
- geometry, scale/resolution and transformation version;
- status (`ok`, `absent`, `failed`, `unknown`);
- whether it is authoritative, a proxy, a model, or presentation-only;
- marginal credits/cost and latency;
- independence group, so JRC-via-Mireye and JRC-via-EE are not counted twice;
- the decision or uncertainty it changed.

### Skill-combination acceptance

A combination graduates from experimental to product use only if:

1. It changes or resolves a real Mission decision that the first source alone could not.
2. Its result is stable to reasonable date-window, buffer, and scale perturbations—or its instability is surfaced.
3. It passes positive and negative controls across at least two US regions.
4. It handles source absence and disagreement without converting them to a pass.
5. Its added latency/credits are justified by information gain.
6. A deterministic replay produces the same evidence and rule result from the same versioned inputs.

The agentic work under test is **selecting, sequencing, and stopping skills**: vetoing early, commissioning a temporal witness only when material, widening geography after rejection, and asking Skeptic Review to challenge the finalist. The data transformation and hard-gate result should remain reproducible code/config rather than hidden model reasoning.

## Recommended execution order

1. Re-run H1/H2 from cache to formalize the evidence contract and `flood-rewind` controls without spending credits.
2. Repair Dynamic World interpretation, then test W3/D1/D3 against NLCD or known development polygons before any land-change score returns to the UI.
3. Repair farm phenology typing and validate F1 against CDL years; then add F2/F3 water-right authority boundaries.
4. With an approved Maps budget, test one Routes matrix for H3/W2 and one Aerial View lookup/fallback flow. Keep scene context out of evidence scoring.
5. Add EIA-861 parsing for D1/D2 and one Warehouse utility territory; measure whether it changes a decision beyond Mireye's current fields. Add one LODES labor-flow comparison only if staffing is a declared Mission constraint.
6. Run `skeptic-review` over every case and reject any “two sources agree” claim that traces to the same underlying dataset.

## Primary sources

### Mireye

- [Live field catalog](https://api.mireye.com/v1/meta/fields)
- [Live plan/credit catalog](https://api.mireye.com/v1/meta/plans)
- [Mireye API documentation](https://docs.mireye.ai/api-reference)
- [Mireye Earth MCP source](https://github.com/Mireye-Labs/mireye-earth-mcp)

### Earth Engine and datasets

- [Earth Engine data catalog](https://developers.google.com/earth-engine/datasets)
- [JRC Monthly Water History v1.4](https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory)
- [Dynamic World V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- [USDA NASS Cropland Data Layers](https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL)
- [CHIRPS Daily precipitation](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY)
- [GRIDMET daily surface meteorology](https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_GRIDMET)
- [ERA5-Land hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY)
- [Sentinel-1 GRD](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD)
- [MODIS daily land-surface temperature](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1)
- [NASA GDDP-CMIP6](https://developers.google.com/earth-engine/datasets/catalog/NASA_GDDP-CMIP6)

### Google Maps Platform

- [Routes API](https://developers.google.com/maps/documentation/routes)
- [Aerial View API](https://developers.google.com/maps/documentation/aerial-view/overview)
- [Aerial View policies](https://developers.google.com/maps/documentation/aerial-view/policies)
- [Photorealistic 3D Tiles](https://developers.google.com/maps/documentation/tile/3d-tiles-overview)
- [Map Tiles policies](https://developers.google.com/maps/documentation/tile/policies)
- [Geocoding API](https://developers.google.com/maps/documentation/geocoding/overview)

### US public authorities

- [FEMA National Flood Hazard Layer](https://www.fema.gov/flood-maps/national-flood-hazard-layer)
- [USGS Water Data APIs](https://api.waterdata.usgs.gov/)
- [USDA NRCS Soil Data Access](https://sdmdataaccess.sc.egov.usda.gov/)
- [USFWS NWI data limitations](https://www.fws.gov/node/264582)
- [USDA 2025 CDL metadata](https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/metadata_CDL25_FGDC-STD-001-1998.htm)
- [EIA-861](https://www.eia.gov/electricity/data/eia861/)
- [EIA-860](https://www.eia.gov/electricity/data/eia860/)
- [EIA-923](https://www.eia.gov/electricity/data/eia923/)
- [BTS National Transportation Atlas Database](https://geodata.bts.gov/pages/ntad)
- [FHWA Freight Analysis Framework](https://ops.fhwa.dot.gov/freight/freight_analysis/faf/)
- [Census LODES](https://lehd.ces.census.gov/data/)
- [EPA ECHO web services](https://echo.epa.gov/tools/web-services)
- [California CalWATRS](https://www.waterboards.ca.gov/upward/calwatrs/)
- [Texas TCEQ water-right permits](https://www.tceq.texas.gov/permitting/water_rights/wr-permitting)

## Bottom line

The repository supports the user's instinct: the agent should invoke concise, use-case-aware skills that already know the best Mireye, Earth Engine, Google, and public-data combinations. It also shows why those combinations must be tested before they become product truth. Today, `flood-rewind` remains the clearest production candidate. Core Mireye screening is usable across all four Missions. `farm-history` is the next strongest tested combination because annual crop rotation and rainfall history add information beyond Mireye's current mode. The Data Center grid/heat/water screen is strong for prioritization but must preserve utility-capacity unknowns. Aerial View plus 3D fallback is proven for presentation. Warehouse route reality is blocked by the current Google configuration; corrected land-change and single-model future climate remain experimental rather than locked scoring inputs.
