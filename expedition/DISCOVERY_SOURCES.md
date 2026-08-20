# Lawful candidate-site discovery sources

**Research date:** 19 August 2026  
**Scope:** US-only Find-a-Site. Search Region + Mission → Candidate Sites with honest labels. Not screening.  
**Method:** First-party docs, OpenAPI, ToS, live `GET https://api.mireye.com/v1/meta/fields`. No scraping. No Zillow/LoopNet/Realtor extraction.

## Verdict

There is still no lawful, self-serve, nationwide **LISTED** feed for warehouse, farm, or data-center inventory. RentCast is the only documented LISTED API that a Python harness can call this week, and it covers residential / multifamily / some vacant land only.

Mireye does not search a region. Live OpenAPI 0.15.0 has no `/search` and no listing resource. `/v1/sites` registers a polygon for a dossier. `/v1/proximity` `nearest` ranks curated infra from a known origin. `/v1/fetch/batch` screens up to 25 supplied pins.

Google Places can *find* named businesses, but Maps ToS block storing Places content as a site inventory and forbid using Places lat/lng for point-in-polygon analysis. That kills Places as a seed into Mireye flood/parcel screens. Do not wire it.

This week: OSM Overpass + Overture/Microsoft footprints + federal facility/plant dumps as **POTENTIAL**, user pins as **USER SITE**, RentCast as **LISTED** for Home only. Then a cheap Mireye screen. Earth Engine stays a witness on finalists.

## Labels

| Label | When | Never |
|---|---|---|
| `LISTED` | Named authorized provider returns an active sale/lease assertion with listing id, source, `last_seen_at` | OSM tags, footprints, EIA plants, EE pixels, Places POIs, assessor land-use |
| `USER SITE` | Exact user address or pin | Anything the agent invented |
| `POTENTIAL` | Lawful public geometry or facility record with no market evidence | Implied "for sale" |

Stale listings drop to `POTENTIAL` plus confirm-with-broker. See [CONTEXT.md](../CONTEXT.md).

## Source scorecard

Columns: **D** = can it emit candidate pins in a region? **Label** = honest output. **VM** = callable from Python stdlib (`urllib`) on this GCP VM without a new paid license.

| Source | Discovers | Auth / price | ToS / limits | Label | VM | Verdict |
|---|---|---|---|---|---|---|
| **Mireye `/v1/fetch`, `/batch`, `/lookup`, `/geocode`, `/ask`** | Nothing. Enriches supplied locators. Live catalog: **310 fields, 15 presets**. Batch max **25**. | Bearer. Credits. Quote first. | US envelope. No region search. [docs.mireye.ai/llms.txt](https://docs.mireye.ai/llms.txt), [OpenAPI](https://api.mireye.com/v1/openapi.json) | n/a | Yes | **WITNESS_ONLY** |
| **Mireye `/v1/proximity` `nearest`** | Top-N from `@airports` `@substations` `@power_plants` `@rail` `@ports` `@urban_areas`. Needs an origin. `n` ≤ 25. Not a Texas-wide dump. | Bearer. Driving calcs billed. | Landmark names fail. Unrated substations excluded unless `min_kv`. [proximity](https://docs.mireye.ai/api-reference/proximity.md) | POTENTIAL infra, not sites | Yes | **WITNESS_ONLY** |
| **Mireye `/v1/sites`** | Register a polygon, build a dossier, `/v1/ask-site`. Not search. | Bearer | OpenAPI `register_site` | USER SITE if caller polygon | Yes | **WITNESS_ONLY** |
| **Mireye field-requests** | New *fields*, not inventory. [field-requests](https://docs.mireye.ai/api-reference/field-requests.md) | Bearer. Build allowance, not fetch credits. | Hours-scale builds | n/a | Yes | **NEVER** as discovery |
| **Mireye MCP** | Same seven tools: ask, fetch, geocode, lookup, proximity, request_field, status. No batch, no region. [mcp/tools](https://docs.mireye.ai/mcp/tools.md) | Bearer / OAuth | MCP fetch is single-location | n/a | MCP host, not stdlib | **WITNESS_ONLY** |
| **Places Nearby / Text Search (New)** | Named POIs in a ≤50 km circle, max **20** hits. Table A has `farm`, `ranch`, `manufacturer`, `storage`, `warehouse_store`. No `warehouse`, no `data_center`. Text Search can query those strings. Field mask required. `places.location` is Nearby Search Pro. [nearby](https://developers.google.com/maps/documentation/places/web-service/nearby-search), [types](https://developers.google.com/maps/documentation/places/web-service/place-types) | API key. Pro $32 / 1k after 5k free. [pricing](https://developers.google.com/maps/billing-and-pricing/pricing) | **Fatal:** no scrape/store of names/addresses; lat/lng cache **30 days**; place_id forever; **no Places lat/lng as PIP input**; Places content not on a non-Google map. [ToS 3.2.3](https://cloud.google.com/maps-platform/terms), [service terms §14](https://cloud.google.com/maps-platform/terms/maps-service-terms), [policies](https://developers.google.com/maps/documentation/places/web-service/policies). Maps key here still blocks Places. | would be POTENTIAL if legal | HTTP yes, key blocked | **NEVER** |
| **Geocoding API** | Address → coord. Not inventory. | $5 / 1k after 10k | Lat/lng cache 30 days; no non-Google map. [geocoding](https://developers.google.com/maps/documentation/geocoding/overview) | USER SITE resolve | Yes if key | Prefer Mireye |
| **Routes API** | Drive time. Not inventory. | Compute Routes Essentials $5 / 1k after 10k | 30-day cache of lat/lng/duration. Maps key here blocked for Routes. [routes](https://developers.google.com/maps/documentation/routes/overview) | n/a | Blocked | later commute screen |
| **Address Validation** | Corrects an address. Not inventory. CASS for US/PR. | Pro $17 / 1k after 5k | 30-day cache table. USPS fake-address reporting. [overview](https://developers.google.com/maps/documentation/address-validation/overview) | n/a | Yes if key | **NEVER** for Find-a-Site |
| **Maps Grounding Lite MCP** | `search_places`, weather, routes, `resolve_names`, `resolve_maps_urls`. Experimental. [MCP ref](https://developers.google.com/maps/ai/grounding-lite/reference/mcp) | API key. SKU Maps Grounding Lite $7 / 1k after 10k | Grounded output cache 30 days for eval only. Same Places ToS. [service terms §10](https://cloud.google.com/maps-platform/terms/maps-service-terms) | n/a | MCP | **NEVER** for stored candidates |
| **Maps Code Assist MCP** | Docs RAG, not places. [code assist](https://developers.google.com/maps/ai/mcp) | Experimental, no charge | Maps ToS + no model training on Maps content | n/a | MCP | **NEVER** |
| **Aerial View** | Pre-rendered US videos. [overview](https://developers.google.com/maps/documentation/aerial-view/overview) | $16 / 1k after 5k | **Cannot download/store/cache videos.** | n/a | Key-restricted | **WITNESS_ONLY** visual |
| **Photorealistic 3D / Map Tiles** | Display only | 1k free then $6 / 1k | No image analysis, no geodata extraction. [tile policies](https://developers.google.com/maps/documentation/tile/policies) | n/a | Tiles key | **NEVER** as inventory |
| **Earth Engine Dynamic World** | `GOOGLE/DYNAMICWORLD/V1` 10 m `built`/`crops` probabilities. [catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) | EE project. Limited plan from $0.40 / EECU-hr. [pricing](https://cloud.google.com/earth-engine/pricing) [access](https://developers.google.com/earth-engine/guides/access) | Dataset CC-BY-4.0. Raster class, not parcels. | inferred POTENTIAL only if you polygonize; dishonest as a site | Needs `ee` client | **WITNESS_ONLY** |
| **Earth Engine CDL** | `USDA/NASS/CDL` annual CONUS crop map. Public domain. [EE](https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL) [USDA](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php) | Same EE | Classification, not lease or water right | farm land-cover, not a farm listing | EE or GeoTIFF download | **WITNESS_ONLY** |
| **Google Open Buildings in EE** | `GOOGLE/Research/open-buildings/v3/polygons` | EE | **Africa, LatAm, S Asia, SE Asia. Not US.** [v3](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons) | n/a | n/a | **NEVER** |
| **Microsoft buildings in EE** | Not in official EE catalog. Community ingest only. | n/a | Unofficial path | n/a | n/a | skip EE; use the Microsoft download |
| **Ask Google Earth / Earth AI** | Earth *UI* spatial chat. Experimental. Data overlaps Places Table A. [get started](https://developers.google.com/maps/documentation/earth/gemini/get-started) [experimental](https://developers.google.com/maps/documentation/earth/experimental-overview). Earth AI is a Google program, not a stdlib API. [analytics page](https://mapsplatform.google.com/maps-products/geospatial-analytics/) | Earth account / Cloud preview | Pre-GA Earth terms. Not a harness endpoint. | n/a | No | **NEVER** this week |
| **BigQuery public data** | Hosted tables, 1 TB/month query free. [BQ public](https://cloud.google.com/bigquery/public-data) | GCP project | No SLA. Needs BQ client, not stdlib. Overture is easier from S3. | depends | No stdlib | skip; use Overture S3 |
| **Nominatim** | Address/place search | None. 1 req/s, valid UA | **No bulk, no grid reverse, no download-all-POIs, no autocomplete.** ODbL. [policy](https://operations.osmfoundation.org/policies/nominatim/) | address resolve only | Yes, already used | **NEVER** as region POI dump |
| **Overpass** | Tagged OSM features in a bbox. Current `discover.py` path. | None. ~10k req/day, ~1 GB/day, 429/504. [commons](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) [wiki](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances) | ODbL share-alike. Not a production backend. Cache. UA. | POTENTIAL | Yes | **BUILD_NOW** |
| **Overture Maps** | Buildings + places + GERS ids. Download bbox or DuckDB on `s3://overturemaps-us-west-2`. [getting data](https://docs.overturemaps.org/getting-data/) [overturemaps.org](https://overturemaps.org) | Free download | Buildings **ODbL**. Places mixed CDLA/Apache. US addresses include NAD license. [attribution](https://docs.overturemaps.org/attribution/) | POTENTIAL | Download yes; DuckDB not stdlib | **BUILD_NOW** if we ship a bbox extract |
| **Microsoft US Building Footprints** | 129,591,852 footprints, state GeoJSON zips. No use type. [README](https://raw.githubusercontent.com/microsoft/USBuildingFootprints/master/README.md) | Free | **ODbL**. Vintage mixed 2012–2020. | POTENTIAL large-footprint seeds | HTTP zip yes | **BUILD_NOW** warehouse/DC geometry |
| **Microsoft Global ML footprints** | Global, CDLA Permissive 2.0. [repo](https://github.com/microsoft/GlobalMLBuildingFootprints) | Free | CDLA. Overlaps US set. | POTENTIAL | Download | Prefer the US ODbL set |
| **OpenAddresses** | Address points, mixed source licenses. US includes NAD. [openaddresses.io](https://openaddresses.io) | Free | Per-source terms. Not a search API. Addresses are not sites. | n/a | Download | low value |
| **RentCast `/listings/sale` and rental** | City/state/ZIP or lat/lng + **radius miles**. Types: Single Family, Condo, Townhouse, Manufactured, Multi-Family, Apartment, Land. **Not** office/retail/industrial/manufacturing/agricultural. Daily listing refresh. 500/page. [listings](https://developers.rentcast.io/reference/property-listings) [types](https://developers.rentcast.io/reference/property-types) [search](https://developers.rentcast.io/reference/search-queries) | `X-Api-Key`. 50 free/mo, then $74 / 1k, $199 / 5k, $449 / 25k. 20 rps. [pricing](https://www.rentcast.io/api) [rate](https://developers.rentcast.io/reference/rate-limits) | API is the license. Site ToS bans scrapers of the *website*. [terms](https://www.rentcast.io/terms) | **LISTED** Home/land | Yes | **BUILD_NOW** Home only |
| **ATTOM Property API** | Radius search, max **20 miles**. `propertyIndicator` includes Industrial 50–54, Agricultural 70, Vacant 80. Assessor/sale history, not an MLS live feed. [docs](https://api.developer.attomdata.com/docs) | API key. Trial. Price not public. | Vendor license. | POTENTIAL parcels | Yes after key | **PARTNER** |
| **Regrid** | Nationwide parcels, zoning in metros, footprints, REST + MCP, 100k-point batch. [api](https://regrid.com/api) [plans](https://app.regrid.com/api/plans) | Token. Self-serve + enterprise >10k records/mo. 30-day sandbox. | API/Tiles ToS. | POTENTIAL parcels | Yes after token | **PARTNER** |
| **LightBox** | Parcels, structures, zoning, assessment APIs. [developer](https://developer.lightboxre.com/) | Portal login. No public self-serve price. | Commercial license. | POTENTIAL | After contract | **PARTNER** |
| **Crexi** | Help Center **Listing API is inbound push** for MLS/large brokers, not a pull feed. [listing API](https://learn.crexi.com/listing-api-overview-crexi-help-center). `api.crexi.com` swagger is credential-gated. | Partner agreement | Do not scrape crexi.com. | LISTED only after contract | No | **PARTNER** |
| **CoStar / LoopNet** | No public developer API page found (CoStar developer URL 404). | Sales | Do not scrape. | — | No | **NEVER** scrape; **PARTNER** if a feed is sold |
| **CommercialSearch / PropertyShark** | No first-party public API docs retrieved. | — | Do not scrape. | — | No | **NEVER** scrape |
| **EIA plants** | Form EIA-860 plant lat/lng, ≥1 MW. [FAQ](https://www.eia.gov/tools/faqs/faq.php?id=567&t=1) [API](https://www.eia.gov/opendata/) [Atlas plants](https://atlas.eia.gov/datasets/eia::power-plants/explore) | API key for series. **Bulk files need no key.** | Attribute EIA. API ToS on register page. **EIA does not publish substations.** Transmission shapefiles were HIFLD. | POTENTIAL infra pins, not warehouses | Yes, CSV | **BUILD_NOW** DC/warehouse *context seeds* |
| **HIFLD** | Was the public infra dump. **Open ended 26 Aug 2025.** Remaining access is HIFLD Secure on DHS GII: Login.gov, federal sponsor, DUA. [DHS](https://www.dhs.gov/gmo/hifld) [FGDC](https://www.fgdc.gov/organization/working-groups-subcommittees/hifld/index_html) [NAPSG](https://www.napsgfoundation.org/hifld_open/) | GII | Not for this agent | — | No | **NEVER** |
| **EPA ECHO / Envirofacts** | Public facility search REST, no auth. [ECHO](https://echo.epa.gov/tools/web-services) [Envirofacts](https://www.epa.gov/enviro/envirofacts-data-service-api) | None | 15 min query cap. FRS *intergovernmental* API needs NAAS. [FRS API](https://www.epa.gov/frs/intergovernmental-frs-api) | POTENTIAL industrial facilities | Yes | **BUILD_NOW** warehouse/DC neighbor seeds |
| **USPVDB** | ≥1 MW solar array polygons, CSV/shp/GeoJSON + REST. Public. [data](https://energy.usgs.gov/uspvdb/data/) | None | Cite USGS/LBNL. Not field-verified. | POTENTIAL energy sites / veto | Yes | **BUILD_NOW** energy context |
| **USWTDB** | Turbine points, public domain, cite USGS/ACP/LBNL. [uswtdb](https://energy.usgs.gov/uswtdb/) | None | Quarterly lag | POTENTIAL / veto | Yes | **BUILD_NOW** |
| **FAA OE-AAA** | Part 77 *filing* portal, not a site catalog. [portal](https://oeaaa.faa.gov/oeaaa/external/portal.jsp) | Login | Not inventory | n/a | n/a | **NEVER** as discovery |
| **FAA Digital Obstacle File** | Known aviation obstacles, 56-day cycle. [DOF](https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/dof/) | None | Aviation obstacles, not parcels | veto for tall DC | Yes | **WITNESS_ONLY** |
| **USDA CDL / CropScape** | National crop rasters, 10 m for 2024–25. [releases](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php) | None | Public domain. Not parcels. | farm cover | Download huge | **WITNESS_ONLY** |
| **Census TIGER** | Roads, places, blocks, rails. **Not parcels.** MAF addresses are not in the public files. [TIGER gdb](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-geodatabase-file.html) | None | Public | region geometry | Yes | **BUILD_NOW** as Search Region, not candidates |
| **PAD-US 4.1** | Protected areas. [overview](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview) [download](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download) DOI [10.5066/P96WBCHS](https://doi.org/10.5066/P96WBCHS) | None | Veto / easement screen. Not candidates. Energy-siting use is documented. | veto | GDB needs GIS lib | **BUILD_NOW** as filter |
| **Mapbox MCP** | POI category search, geocode, isochrone, directions. Token required. [README](https://github.com/mapbox/mcp-server) [Search Box](https://docs.mapbox.com/api/search/search-box/#category-search) | Mapbox token | Mapbox ToS; POIs are not listings | POTENTIAL POI | MCP + token | **PARTNER** |
| **CARTO MCP** | Queries *your* warehouse and Builder maps. [docs](https://docs.carto.com/carto-for-agents/mcp-server) | CARTO account | No public US inventory | n/a | No | **NEVER** unless we load data there |

## What Mireye will not do

Live `GET /v1/meta/fields` on 19 Aug 2026: 310 fields, 15 presets (`site_selection` 72, `data_center_siting` 120). OpenAPI paths include fetch, batch, quote, runs, geocode, lookup, ask, proximity, field-requests, **sites**, ask-site. Zero search/listing/region endpoints. [llms.txt](https://docs.mireye.ai/llms.txt)

`nearest` is the only "find things" op, and it is "closest N infra to this pin", not "candidate parcels in this county". EIA's own FAQ says **EIA does not publish substations**; Mireye's `@substations` is a curated internal set, not a dump you can replicate from EIA after HIFLD Open died.

Do not file a field-request for "warehouses for sale in Texas". That endpoint builds *fields at a point*.

## Places is a trap for this product

Nearby Search Pro is priced for 20-result circles, not county inventory. There is no industrial-warehouse type. Text Search "data center" returns branded operators, which is the opposite of off-market siting.

Worse: [Maps ToS 3.2.3(c)](https://cloud.google.com/maps-platform/terms) lists "use latitude/longitude values from the Places API as an input for point-in-polygon analysis" as forbidden content-creation. Mireye flood/wetland/parcel screens *are* PIP. Storing names/addresses is also banned. Cache of coords is 30 days. Put Places results on a Google Map or do not use them. Our board is not a Google Map.

Leave Places off. The GCP project having the API enabled does not change the ToS.

## Mission stacks this week

Cheap seed → dedupe → Mireye cheap screen → EE only on finalists.

| Mission | Seed | Dedupe | Cheap Mireye screen | EE / deepen |
|---|---|---|---|---|
| **warehouse** | Overpass `building=warehouse` / `industrial=warehouse`. Overture/MS large footprints. EPA ECHO industrial facilities as *neighbors*, not listings. User CSV. | ~100 m + name | flood, wetlands, slope, PAD-US, nearest interstate/rail via proximity if origin known. 8–12 non-parcel fields. Batch 25. | height/land-cover on finalists only |
| **farm** | Overpass named `landuse=farmland` / `farmyard`. User pins. CDL as *cover witness*, not a parcel list. | bbox centroid | soils/flood/wetland if in catalog, PAD-US veto | CDL / Dynamic World crops on finalists |
| **home** | **RentCast LISTED** radius search. User address. OSM houses only if RentCast is empty, labeled POTENTIAL. | listing id + address | flood/wildfire/commute fields, no labor | skip EE unless contradiction |
| **data_center** | User list first. OSM `telecom=data_center` as *existing operators*, not empty land. EIA-860 plants + USPVDB/USWTDB as **power context**, not sites. Large MS footprints near those plants as POTENTIAL land. | 250 m | `grid_interconnect` subset, flood, PAD-US, FAA DOF height veto | heat/drought on finalists |

Do not call a plant, a substation, or a solar array a warehouse or a home. Seed *from* infra, then require a parcel-like pin.

## Harness to build this week

**Router is deterministic.** Mission × Search Region picks adapters. The LLM does not choose vendors. MCP is a convenience wrapper around the same router, not a second brain.

**Adapters**

1. `user` → `USER SITE`
2. `overpass` → OSM tags, cached, UA, timeout budget → `POTENTIAL`
3. `rentcast` → Home LISTED only, if key present; else skip
4. `eia860` / `uspvdb` / `uswtdb` / `echo` → infra/facility POTENTIAL, mission-gated
5. `padus` → veto, never a candidate
6. `footprints` → optional pre-cut Overture or MS extract for the demo regions
7. `mireye_screen` → `/v1/fetch/quote` then `/v1/fetch/batch` pages of 25

Do not add Nominatim as a POI crawler. Keep it for user-typed addresses if Mireye geocode is not used.

**Candidate record**

```
id, mission, label, lat, lng, name,
source, source_url, source_id, last_seen_at,
license, attribution,
query_bbox, reason_seeded,
listing_id, listing_status   # LISTED only
```

No Places place_id pipeline. No scraped LoopNet URL.

**Spend gates**

- Mireye: quote every batch. Soft 20k / hard 25k already in [DECISIONS.md](DECISIONS.md). Cheap screen ≤15 ordinary fields, no parcel group until finalists.
- RentCast: 50 free calls. One radius query per Home search, paginate only if the user asks for more.
- Overpass: cache by query hash. Stop at 429. No grid of tiny bboxes across Texas.
- EE: finalists only, after Mireye survivors.

**This week we will not** license Regrid, ATTOM, LightBox, Crexi, CoStar, or Mapbox. We will not turn on Places. We will not scrape. We will not label OSM or EIA as LISTED.

## Partner backlog

| Priority | Vendor | Why | Blocker |
|---|---|---|---|
| 1 | Regrid | Region parcel query is the real off-market discovery for warehouse/farm/DC | Paid API + ToS |
| 2 | ATTOM | Industrial/ag/vacant `propertyIndicator` radius search | Trial key, 20 mi cap, not LISTED |
| 3 | Crexi pull feed | Commercial LISTED | Listing API is push-only; Sales API gated |
| 4 | LightBox | Parcels + structures + zoning | Sales |
| 5 | RentCast paid | Home LISTED volume | $74+ |
| 6 | CoStar | Industrial listings | No public API |
| — | Places | Named POIs | ToS PIP + storage ban |
| — | HIFLD | Subs/transmission | Open is gone |

If someone asks for "national warehouse listings" before a contract, the honest answer is still no.
