# GEE + GCP + AWS × Mireye — Build Challenge Research Note

**Verdict:** The winning seam is **time-series / change detection**, not “satellite on a map.” Mireye already ships cited **point-in-time** parcel facts (terrain, FEMA flood, wildfire exposure, wetlands, utilities, canopy/NDVI snapshots, land cover). GEE’s non-obvious value is **what changed, when, and how fast** — then an agent that **holds, notifies, or files**, not a basemap.

**Deadline:** 15 August 2026 · Agent required · Weird second source required · Real buyer required  
**Sources checked:** [mireye.com](https://www.mireye.com), [mireye.com/templates](https://www.mireye.com/templates), Earth Engine catalog + access/ToS docs, GCP Earth Engine/BigQuery docs, AWS Open Data Registry.

---

## 1. What Mireye already covers (do not reinvent)

From the product site and starter templates:

| Mireye strength | Examples | Implication for GEE |
|---|---|---|
| Cited point facts | Elevation, slope, aspect, land cover, soils | Don’t lead with NASADEM/SRTM as the “innovation” |
| Static / inventory hazards | FEMA flood zone, wetland intersection, coastal distance, wildfire exposure presets | Don’t rebuild “is this Zone AE?” — **change vs that baseline** is the gap |
| Utilities / grid | Transmission, plants, pipelines, sewer, interconnect-oriented presets | Pair with **nearby land-use change** or **AWS power-market data**, not another nearest-line query |
| Parcel / market | Parcel record, jurisdiction, HPI/valuation signals (lending template) | Use as identity + underwriting context around GEE metrics |
| Snapshot vegetation | Hazards template shows tree canopy % and NDVI | A **single NDVI number is not enough** — sell **trend, phenology, scar recovery, disturbance date** |
| Listed sources include | USGS, FEMA, NOAA, USDA, USFWS, JRC, **SENTINEL-2**, etc. | GEE using Sentinel is expected; differentiation is **computation over time + agent action** |

Templates that already own “site diligence / insurance book / solar-wind siting” patterns: Land Read, Hazards Read, Power Read, Insurance Book Monitoring, Property Diligence, ICP Finder, solar/wind/storage/data-center presets on the homepage.

**Challenge hard rule reminder:** reason → decide → act. Map UIs fail the brief even if the data is cool ([MIREYE_BUILD_CHALLENGE.md](./MIREYE_BUILD_CHALLENGE.md)).

**Do-not-build inspiration (adjacent only):** eagle-strike, foundation forensics, smell/wind+rentals, wet-bulb heat+canopy+outages, endangered-species habitat, carbon-aware compute, fishable river.

---

## 2. Google Earth Engine — capabilities that complement Mireye

### 2.1 Access, auth, commercial terms (challenge-relevant)

- Earth Engine now **requires a Google Cloud project** with the Earth Engine API enabled and registered for **commercial or noncommercial** use ([Access](https://developers.google.com/earth-engine/guides/access)).
- Python: `ee.Authenticate()` then `ee.Initialize(project='my-project')` ([Auth](https://developers.google.com/earth-engine/guides/auth)).
- Unattended agents (Cloud Run / Functions): prefer **Application Default Credentials** + project ID; service-account private keys are supported but discouraged for prod ([Service accounts](https://developers.google.com/earth-engine/guides/service_account)).
- **Commercial vs noncommercial:** Private-company / operational use needs a **paid commercial** registration; unpaid commercial use violates ToS ([Transition to commercial](https://developers.google.com/earth-engine/guides/transition_to_commercial), [Terms](https://earthengine.google.com/terms/), [Commercial](https://earthengine.google.com/commercial/)).
  - **Hackathon opinion:** A portfolio/demo that is **not sold** can often register as noncommercial if you qualify (individual / academic / nonprofit research). If you pitch a product you intend to sell, register commercial (or use Cloud free trial / startup credits carefully). Miscategorization can pause access.
- Exports: images/tables/video → **Google Drive, Cloud Storage, or EE assets** ([Exporting](https://developers.google.com/earth-engine/guides/exporting)). GCS needs a billed project + writable bucket.
- Quotas (defaults): ~40 concurrent interactive requests/project, **100 req/s**, ~2 concurrent batch tasks average, 250 GB assets; daily EECU optional cap ([Usage / quotas](https://developers.google.com/earth-engine/guides/usage)). Fine for a demo book of dozens–hundreds of parcels if you keep reducers local and cache.

### 2.2 Key public datasets (US parcels / addresses)

| Dataset | EE ID / entry | Why it matters vs Mireye |
|---|---|---|
| Sentinel-2 SR (harmonized) | [`COPERNICUS/S2_SR_HARMONIZED`](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | 5-day revisit; NDVI/NDWI/NBR **time series**, before/after composites |
| Dynamic World | [`GOOGLE/DYNAMICWORLD/V1`](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) | Near-real-time 10 m LULC **probabilities** (built/bare/trees/water/crops…) — class **change** |
| Hansen forest loss | [`UMD/hansen/global_forest_change_*`](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2024_v1_12) | Tree cover 2000 + **loss year** (stand-replacement) |
| NASA FIRMS | [`FIRMS`](https://developers.google.com/earth-engine/datasets/catalog/FIRMS) | Near-real-time active fire centroids (MODIS); plus VIIRS variants in catalog |
| MODIS LST | [`MODIS/061/MOD11A1`](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1) | Daily land surface temperature — **UHI / heat anomaly** (not wet-bulb air temp) |
| JRC Global Surface Water | [`JRC/GSW1_4/MonthlyHistory`](https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory) | Monthly water/non-water **1984–2021** — encroachment & permanence |
| CHIRPS precip | [`UCSB-CHG/CHIRPS/DAILY`](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY) | Daily precip for drought / anomaly indices |
| ERA5-Land | [`ECMWF/ERA5_LAND/HOURLY`](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY) | Hourly reanalysis (soil moisture, temp, etc.) for climate context |
| USDA CDL | [`USDA/NASS/CDL`](https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL) | Annual **crop type** CONUS — year-over-year crop switches |
| NLCD | [USGS NLCD releases](https://developers.google.com/earth-engine/datasets/catalog/USGS_NLCD_RELEASES_2021_REL_NLCD) | Multi-year impervious / land-cover epochs (slower than Dynamic World) |
| NASADEM / SRTM | [`NASA/NASADEM_HGT/001`](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) | DEM — **overlap with Mireye terrain**; use only as auxiliary |
| Ocean colour / CHL | e.g. [Copernicus plankton OLCI 300 m](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_MARINE_OC_GLO_BGC_PLANKTON_OLCI_300M) | Chlorophyll proxy for **blooms** (coastal/estuarine) |
| Landsat / MODIS / NAIP | Catalog hubs for [Landsat](https://developers.google.com/earth-engine/datasets), [MODIS](https://developers.google.com/earth-engine/datasets), NAIP | Long archive, phenology, high-res US aerial epochs |

Catalog overview: [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets).

### 2.3 Computations Mireye likely does **not** return as cited parcel facts

Lean on these as the “weird satellite” layer:

1. **NDVI / NDWI / NBR trajectories** (seasonal curves, slope, break points)  
2. **Recent burn scar + recovery** (NBR delta vs FIRMS coincidence; months of green-up)  
3. **Dynamic World / NLCD change** (trees→bare, bare→built, water expansion)  
4. **Hansen `lossyear`** on parcel / buffer  
5. **JRC water frequency & trend** (permanent vs seasonal vs new inundation)  
6. **Drought indices** from CHIRPS / ERA5 (SPI-like anomalies over growing season)  
7. **Urban heat island / LST anomaly** vs county rural baseline (MODIS) — *not* the forbidden wet-bulb+canopy+outage product  
8. **CDL crop type & phenology mismatch** (claimed soy vs observed corn curve)  
9. **Construction / mining disturbance** (sudden bare + spectral brightening)  
10. **Algal / turbidity proxies** (CHL, NDWI persistence near intakes / marinas)

---

## 3. GCP pieces that make an agent **act**

| Piece | Role in an agent |
|---|---|
| **Cloud Run / Cloud Functions** | Host the reason→decide→act loop; ADC → `ee.Initialize`; call Mireye API/MCP |
| **Cloud Storage** | Staging for EE exports, thumbnails, memo attachments ([Exporting](https://developers.google.com/earth-engine/guides/exporting)) |
| **BigQuery** | Screening books of parcels; `ST_REGIONSTATS` zonal stats from EE rasters; `Export.table.toBigQuery` ([BigQuery integrations](https://developers.google.com/earth-engine/guides/bigquery_integrations), [Export to BQ](https://developers.google.com/earth-engine/guides/exporting_to_bigquery), [Earth Engine on Cloud](https://cloud.google.com/earth-engine)) |
| **Pub/Sub** | Event bus: “new FIRMS cluster near book” → worker → underwriter alert ([BQ↔EE automation pattern](https://cloud.google.com/blog/products/data-analytics/automation-with-bigquery-earth-engine-and-cloud-functions)) |
| **Vertex AI / Gemini** | Reason over **Mireye citations + GEE derived metrics**; draft diligence memos with provenance |
| **Cloud Scheduler** | Nightly book re-screen (mirror Mireye’s Insurance Book Monitoring template, but add change metrics) |

**Agent-shaped GCP pattern (proven):** BigQuery parcel table → Pub/Sub → Cloud Function → EE zonal reduce / export → write metrics back to BQ → LLM decision → webhook/email/CRM.

---

## 4. AWS pieces that add a **third** non-obvious source

Prefer AWS when it is **not** “another copy of Sentinel.”

| AWS asset | URL | Non-trivial use with Mireye |
|---|---|---|
| **NEXRAD on AWS** | [registry.opendata.aws/noaa-nexrad](https://registry.opendata.aws/noaa-nexrad/) | Hail / severe-storm signatures for **claim verification**; SNS new-object notifications |
| **NOAA GOES** | [registry.opendata.aws/noaa-goes](https://registry.opendata.aws/noaa-goes/) | Rapid weather / smoke context for ops alerts |
| **PUDL (Catalyst)** | [registry.opendata.aws/catalyst-cooperative-pudl](https://registry.opendata.aws/catalyst-cooperative-pudl/) | EIA/FERC/EPA electricity system tables — **queue, generation, utility economics** beyond Mireye’s nearest-asset geometry |
| **NREL NSRDB** | [registry.opendata.aws/nrel-pds-nsrdb](https://registry.opendata.aws/nrel-pds-nsrdb/) | Hourly irradiance time series (Mireye solar presets ≠ full TMY/hourly validation) |
| **Sentinel / Landsat on AWS** | [Sentinel-2](https://registry.opendata.aws/sentinel-2/), [S2 COGs](https://registry.opendata.aws/sentinel-2-l2a-cogs/), [USGS Landsat](https://registry.opendata.aws/usgs-landsat/) | Escape hatch if EE access is blocked; usually **worse DX than GEE** for hackathons |
| **Amazon Location Service** | [aws.amazon.com/location](https://aws.amazon.com/location/) | Geofences + trackers + SNS when assets enter a risk polygon (action channel, not a map product) |
| **SNS / IoT** | AWS messaging | Push “act” to humans/systems |

**AIS note:** Challenge inspiration lists ship tracking, but **US AIS is not a clean first-class AWS Open Data drop-in** the way NEXRAD/PUDL are. Prefer MarineCadastre / NOAA AIS APIs as a custom fetch if you need vessels — or pick NEXRAD/PUDL for cleaner AWS complementarity.

Registry hub: [registry.opendata.aws](https://registry.opendata.aws/).

---

## 5. Product concepts (8)

### 1) Waterline Creep
- **Problem:** Flood maps lag reality. Insurers and title desks miss parcels where **surface water has been expanding for years** while FEMA still says Zone X — silent claims and bad closings.
- **Buyer:** Personal-lines flood underwriter / specialty inland-marine desk; secondary: title underwriting manager.
- **Weird combo:** Mireye flood/wetland/parcel citations + **JRC monthly water history + Sentinel NDWI trend** (+ optional BigQuery book screen).
- **Mireye vs GEE:** Mireye = geocode, FEMA zone, wetland flag, parcel ID. GEE = multi-decadal **water occurrence / recent wet months** and NDWI slope.
- **Agent loop:** Nightly book scan → score “Zone X + rising water frequency” → **place underwriting hold + Slack/email underwriter + attach citation memo** → CRM status `HOLD_WATERLINE`.
- **Why not a map:** The product is the **hold + memo**, not the blue pixels.
- **Feasibility:** **High** (JRC is precomputed; reducers are easy).
- **vs do-not-build list:** Not “fishable river”; flood *inventory* is Mireye’s job — **hydrographic creep** is the twist.

### 2) FieldAlibi
- **Problem:** Crop insurers and ag lenders lose money on **misreported crop / prevented-planting / phantom acres**.
- **Buyer:** Crop insurance SIU lead or regional ag-credit risk officer.
- **Weird combo:** Mireye soils/flood/parcel + **USDA CDL YoY + Sentinel NDVI phenology + CHIRPS drought anomaly**.
- **Mireye vs GEE:** Mireye = site constraints & identity. GEE = “what actually grew” and weather stress timing.
- **Agent loop:** Ingest policy/acreage schedule → compare claimed crop vs CDL/phenology → if mismatch + no drought alibi → **open SIU ticket + freeze indemnity draft**.
- **Why not a map:** Decision is **refer / don’t pay**, with an audit trail.
- **Feasibility:** **Med** (phenology thresholds need care; demo with CDL YoY + coarse NDVI is enough).
- **vs list:** Not eagle-strike / fishable river; agricultural fraud is a different buyer.

### 3) ScarLedger
- **Problem:** Post-fire, servicers and wildfire UW don’t know if vegetation/structure risk has **stabilized or is still a moonscape** — refis and renewals go through blind.
- **Buyer:** Mortgage servicer special-servicing / wildfire specialty underwriter.
- **Weird combo:** Mireye wildfire + terrain + parcel + **FIRMS coincidence + NBR burn scar + Dynamic World vegetation recovery curve**.
- **Mireye vs GEE:** Mireye = baseline wildfire exposure & structure context. GEE = **event timing + recovery trajectory**.
- **Agent loop:** On FIRMS near book OR monthly recovery job → classify `ACTIVE_SCAR / RECOVERING / STABLE` → **block refinance checklist item or force inspection order**.
- **Why not a map:** Acts on loan/policy workflow systems.
- **Feasibility:** **High–Med**.
- **vs list:** Adjacent to wildfire templates, but **recovery state machine** ≠ static hazard screen; not “heat that kills.”

### 4) DirtMoved
- **Problem:** Construction and CRE lenders miss **unauthorized grading / quarry creep / pad cuts** between diligence and funding.
- **Buyer:** CRE construction-loan officer / site-acquisition lead at a regional bank.
- **Weird combo:** Mireye parcel/land-use/utilities + **Dynamic World bare/built Δ + Sentinel brightness/NDVI collapse** (+ optional county permit scrape as third source).
- **Mireye vs GEE:** Mireye = legal parcel & static land cover. GEE = **weeks-scale disturbance**.
- **Agent loop:** Watchlist of loan addresses → detect disturbance → **generate diligence memo + pause draw request in tracker**.
- **Why not a map:** Money motion is the draw pause.
- **Feasibility:** **High**.
- **vs list:** Not foundation forensics (soils/bedrock); this is **surface disturbance ops**.

### 5) HailTruth
- **Problem:** Auto/roof carriers overpay hail claims without independent storm corroboration at the rooftop.
- **Buyer:** P&C claims manager (CAT / SIU).
- **Weird combo:** Mireye building/parcel + **AWS NEXRAD (hail/VIL proxies)** + **GEE pre/post roof-ish reflectance or vegetation scar in yard** (supporting, not sole evidence).
- **Mireye vs AWS/GEE:** Mireye pins the asset; NEXRAD answers “did severe hail likely hit?”; GEE supports before/after.
- **Agent loop:** FNOL webhook → pull radar + site facts → score corroboration → **auto-assign field adjuster vs fast-pay path**.
- **Why not a map:** Routing decision on the claim file.
- **Feasibility:** **Med** (NEXRAD parsing is the hard part; constrain demo to Level-III products / a library).
- **vs list:** Not wet-bulb health product; money problem for carriers.

### 6) BloomDock
- **Problem:** Marinas, water utilities, and coastal resorts lose bookings / face health liability when **HABs** hit without operational alerts tied to *their* docks and intakes.
- **Buyer:** Municipal drinking-water ops manager or marina portfolio operator.
- **Weird combo:** Mireye coastal/water/parcel proximity + **GEE chlorophyll / NDWI persistence** + optional **GOES** smoke/cloud context on AWS.
- **Mireye vs GEE:** Mireye = which assets sit on which waterbody edge. GEE = **bloom intensity time series**.
- **Agent loop:** Daily estuary scan → threshold breach → **SNS/SMS to ops + close recreational booking flag**.
- **Why not a map:** Closes operations, not “pretty green water.”
- **Feasibility:** **Med** (coastal CHL products are coarse; pick one estuary and fake-friendly thresholds).
- **vs list:** Health angle like “heat that kills,” but **HAB ops** ≠ wet-bulb housing; not “is the river fishable.”

### 7) QueueDirt
- **Problem:** Data-center / solar developers waste months on sites that look grid-adjacent on paper while **land next to the POI is already being paved by a competitor** — or utility economics don’t support the story.
- **Buyer:** Head of site acquisition at a renewables or data-center developer.
- **Weird combo:** Mireye `grid_interconnect` / Power Read + **Dynamic World built expansion in interconnect buffer** + **PUDL on AWS** (plant/utility tables).
- **Mireye vs GEE/AWS:** Mireye = distance/voltage/plant geometry. GEE = **land competition signal**. PUDL = non-spatial utility truth.
- **Agent loop:** Rank candidate sites → demote where built% surges or PUDL flags weak utility → **update CRM stage + kill email to broker**.
- **Why not a map:** CRM stage changes and kill decisions.
- **Feasibility:** **Med**.
- **vs list:** Not carbon-aware GPU routing; land+queue diligence.

### 8) HeatIsland Lease
- **Problem:** Industrial landlords and logistics tenants underprice **extreme rooftop/yard heat** that drives HVAC failure, worker safety incidents, and cold-chain spoilage — separate from FEMA/wildfire screens.
- **Buyer:** Risk manager at a logistics REIT or cold-storage operator.
- **Weird combo:** Mireye parcel/building/utilities + **MODIS LST anomaly vs rural baseline** + Dynamic World impervious/built fraction (+ optional ERA5).
- **Mireye vs GEE:** Mireye = site identity & power context. GEE = **summer LST z-score / nights above threshold**.
- **Agent loop:** Portfolio screen before lease renewal → high LST + high impervious → **escalate EHS ticket + recommend cool-roof CapEx memo**.
- **Why not a map:** Renewal / CapEx workflow action.
- **Feasibility:** **High**.
- **vs list:** Explicitly **not** wet-bulb+canopy+outages; uses **satellite LST + impervious change**, buyer is logistics REIT not city heat program.

---

## 6. Ranked top 3 (opinionated)

Scores: weirdness / buyer clarity / agent-ness / buildability before **15 Aug 2026** (each 1–5).

| Rank | Concept | Weird | Buyer | Agent | Build | Total | Why |
|---|---|---|---|---|---|---|---|
| **1** | **Waterline Creep** | 4 | 5 | 5 | 5 | **19** | Cleanest complementarity (FEMA static vs JRC/NDWI dynamic), obvious cheque-writer, hold action is demo-perfect |
| **2** | **FieldAlibi** | 5 | 5 | 5 | 3 | **18** | Weirdest honest combo; SIU buyer crystal clear; phenology polish is the only risk |
| **3** | **ScarLedger** | 4 | 5 | 5 | 4 | **18** | Strong money path; keep recovery-state framing so it doesn’t look like Hazards Read 2.0 |

**Honorable build-fast alternate:** DirtMoved (if the team is stronger on Dynamic World than ag phenology).  
**Skip for deadline pressure:** HailTruth (NEXRAD depth), BloomDock (validation fuss).

---

## 7. Architecture sketch — #1 Waterline Creep

```text
+----------------+   address / policy book    +---------------------+
| Underwriter    | -------------------------> | Cloud Scheduler /   |
| CRM / email    | <---- hold + memo + cites -| Pub/Sub trigger     |
+----------------+                            +----------+----------+
                                                         |
                                                         v
                                              +----------+----------+
                                              | Cloud Run agent     |
                                              | (Python)            |
                                              +----------+----------+
                         +-------------------------------+-------------------------------+
                         |                               |                               |
                         v                               v                               v
              +------------------+            +------------------+            +------------------+
              | Mireye API/MCP   |            | Earth Engine     |            | Vertex / Gemini  |
              | geocode + lookup |            | JRC GSW zonal    |            | reasoner         |
              | flood_risk /     |            | + S2 NDWI trend  |            |                  |
              | natural_hazard   |            | reduceRegion /   |            |                  |
              | parcel facts     |            | Export->GCS/BQ   |            |                  |
              +--------+---------+            +--------+---------+            +--------+---------+
                       | citations                     | metrics                       | decision
                       +---------------+---------------+---------------+---------------+
                                       |
                                       v
                            Decision: PASS | HOLD | REFER
                                       |
                 +---------------------+---------------------+
                 |                     |                     |
                 v                     v                     v
          BigQuery audit         Pub/Sub alert          Ticket / CRM
          (book metrics)         (Slack/Email/SNS)      status update
```

**Minimal happy path for a 4-day build:**

1. Seed 50–200 addresses (insured book CSV) in BigQuery or JSON.
2. Cloud Run: Mireye `flood_risk` / wetland fields + citations.
3. EE: for each parcel polygon/buffer, compute JRC water frequency (last N years vs prior) + recent Sentinel NDWI median.
4. Rules + Gemini: if FEMA low-risk **and** water frequency rising → HOLD.
5. Act: write row + send email/Slack with **Mireye citations + EE metric provenance**.
6. Demo video: one Zone X parcel that is visibly wetting over time → agent places hold.

Auth sketch:

```python
import ee, google.auth
credentials, _ = google.auth.default()
ee.Initialize(credentials, project="YOUR_GCP_PROJECT")
# Mireye: HTTPS API or MCP tools with GROWTH/BUILD promo codes from challenge brief
```

---

## 8. Feasibility & risk notes for the team

| Risk | Mitigation |
|---|---|
| EE commercial ToS | Register project honestly; don’t sell from a noncommercial project ([Terms](https://earthengine.google.com/terms/)) |
| Overlap with Mireye Sentinel/NDVI | Never demo “here is NDVI”; demo **Δt, break date, recovery class, water frequency** |
| Looking like a map app | UI = queue of decisions + actions log; map optional appendix |
| EE latency | Precompute nightly; interactive demo uses cached BQ metrics |
| Deadline | Prefer Waterline Creep or DirtMoved; instrument FieldAlibi only if someone knows CDL |

---

## 9. Primary sources (citation list)

### Mireye
- https://www.mireye.com  
- https://www.mireye.com/templates  
- Challenge brief in-repo: `MIREYE_BUILD_CHALLENGE.md`

### Earth Engine — platform
- Catalog: https://developers.google.com/earth-engine/datasets  
- Access: https://developers.google.com/earth-engine/guides/access  
- Auth: https://developers.google.com/earth-engine/guides/auth  
- Service accounts / ADC: https://developers.google.com/earth-engine/guides/service_account  
- Exporting: https://developers.google.com/earth-engine/guides/exporting  
- Quotas: https://developers.google.com/earth-engine/guides/usage  
- Cost controls: https://developers.google.com/earth-engine/guides/cost_controls  
- BigQuery integrations: https://developers.google.com/earth-engine/guides/bigquery_integrations  
- Export to BigQuery: https://developers.google.com/earth-engine/guides/exporting_to_bigquery  
- Commercial transition: https://developers.google.com/earth-engine/guides/transition_to_commercial  
- Terms: https://earthengine.google.com/terms/  
- Commercial landing: https://earthengine.google.com/commercial/  
- Earth Engine on Google Cloud: https://cloud.google.com/earth-engine  

### Earth Engine — datasets cited above
- Dynamic World: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1  
- Sentinel-2 SR Harmonized: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED  
- FIRMS: https://developers.google.com/earth-engine/datasets/catalog/FIRMS  
- Hansen GFC: https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2024_v1_12  
- MODIS LST: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1  
- JRC Monthly Water History: https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory  
- CHIRPS Daily: https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY  
- ERA5-Land Hourly: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY  
- USDA CDL: https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL  
- NASADEM: https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001  
- Copernicus plankton / CHL (example): https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_MARINE_OC_GLO_BGC_PLANKTON_OLCI_300M  

### GCP patterns
- BQ ↔ EE automation (Cloud Functions): https://cloud.google.com/blog/products/data-analytics/automation-with-bigquery-earth-engine-and-cloud-functions  

### AWS
- Open Data Registry: https://registry.opendata.aws/  
- NEXRAD: https://registry.opendata.aws/noaa-nexrad/  
- GOES: https://registry.opendata.aws/noaa-goes/  
- PUDL: https://registry.opendata.aws/catalyst-cooperative-pudl/  
- NSRDB: https://registry.opendata.aws/nrel-pds-nsrdb/  
- Sentinel-2 / COGs / Landsat: https://registry.opendata.aws/sentinel-2/ · https://registry.opendata.aws/sentinel-2-l2a-cogs/ · https://registry.opendata.aws/usgs-landsat/  
- Amazon Location Service: https://aws.amazon.com/location/  

---

## 10. Bottom-line recommendation

**Build Waterline Creep** unless the team has strong ag remote-sensing chops — then **FieldAlibi**.  

In one sentence for the one-pager: *“Mireye tells the agent what FEMA and the parcel say; Earth Engine tells it whether the ground has been getting wetter; the agent places the underwriting hold.”*
