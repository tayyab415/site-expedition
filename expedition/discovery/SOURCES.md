# Discovery sources

Research date: 19 August 2026. Primary docs and live probes on this VM.
This is the source map for `python3 -m expedition.discovery`. It is not a listing license.

## What discovery can honestly mean here

Mireye screens a pin. It does not invent inventory. Live probe of the catalog
(`mireye://catalog/presets`, `https://docs.mireye.ai/llms.txt`) shows lookup,
fetch, fetch/batch (max 25), geocode, proximity, ask, runs, field-requests.
There is no region search. Proximity answers "nearest substation to this
coordinate." It does not answer "every warehouse for lease in Harris County."

So the harness seeds pins from other sources, then Mireye can cheap-screen the
survivors. Earth Engine stays a witness on a known pin. Google tiles stay
pictures. LISTED requires a licensed listing id and a last-seen time.

## Live probes (19 Aug 2026)

GCP project `gen-lang-client-0261050164`. Maps key **Mireye challenge 3D UI**.
I also added Solar API (`solar.googleapis.com`) to that key. IP lock unchanged.
Street View metadata and Aerial lookup already worked. Weather and Geocoding stay
blocked on this key. Ask Google Earth has no programmatic API.

| Probe | Result |
|---|---|
| Places Text Search (New) | HTTP 200. 3PL query is the warehouse seed, not retailer DCs. |
| Google Solar `buildingInsights.findClosest` | HTTP 200 after key update. Macy DC roof: 14465 max panels, postal 77023. Pin witness, not a region search. |
| Street View metadata | HTTP 200. Pano at 29.7319,-95.3368, date 2026-03. |
| Aerial `lookupVideoMetadata` | HTTP 200. videoId present, capture 2023-03-31. Do not cache the video. |
| Weather / Geocoding on this key | 403 / REQUEST_DENIED. Not wired. |
| Earth Engine Dynamic World | Live via `.venv-ee`. DHL-area pin built 0.73, water 0.03, crops 0.04. Raster, not a parcel. |
| Ask Google Earth / Earth AI imagery search | Browser chat. No export API. Not wired. |
| Google Open Buildings v3 | Not US. |
| EPA ECHO NAICS 493 Houston 10 mi | 15 facilities with coords. Amazon dropped. Keepers: Dupuy Storage, DHL Supply Chain. Unfiltered radius search is still construction noise. |
| EIA ArcGIS `Power_Plants_in_the_US` | HTTP 200. Houston box ≥50 MW: W A Parish 3632, Cedar Bayou 1494, Deer Park 1192, T H Wharton 1002. |
| USGS USWTDB | Column is `t_state`. Houston box: Lane City Wind, Crawfish / Prairie Switch. |
| `RENTCAST_API_KEY` | unset |

## Router

| Mission | Quick seed | Standard/Deep hop | LISTED possible? |
|---|---|---|---|
| Warehouse | OSM | ECHO NAICS 493 + OSM power + EIA plants, then industrial around anchors | no |
| Data center | OSM | OSM power + USPVDB + USWTDB + EIA, then industrial hop | no |
| Farm | OSM | USPVDB + USWTDB | no |
| Home | OSM | none | RentCast sale listings, if a key exists |

Places joins the seed list when `--paid` is on. `--paid` also reverse-geocodes
nameless OSM pins, batches Elevation, attaches Street View / Solar / Aerial,
and drive time to the search origin via Routes (ADC, not the Maps key).
`--budget deep` samples Earth Engine Dynamic World (built/water/crops) on a
few pins. `--prefilter` is the only path that spends Mireye credits, and only
after `/v1/fetch/quote`. The Expedition board `/api/discover` still calls OSM only.

## Sources

| Source | Verdict | What it discovers | Label | Auth / ToS |
|---|---|---|---|---|
| OSM Overpass + Nominatim | BUILD_NOW | Tagged buildings, industrial land, farms, named data halls, substations | POTENTIAL | [OSM copyright](https://www.openstreetmap.org/copyright). Public Overpass. Rate-limit sensitive. |
| USGS USPVDB | BUILD_NOW | Operating ≥1 MW PV plants | anchor, never LISTED | [USPVDB data](https://energy.usgs.gov/uspvdb/data/), [API](https://energy.usgs.gov/uspvdb/api-doc/) |
| USGS USWTDB | BUILD_NOW as anchor | Operating wind projects | anchor, never LISTED | [USWTDB](https://energy.usgs.gov/uswtdb/). Filter `t_state`, not `p_state`. |
| EIA plants ArcGIS | BUILD_NOW as anchor | ≥50 MW plants near the look | anchor, never LISTED | EIA-860 via [Power_Plants_in_the_US](https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Power_Plants_in_the_US/FeatureServer/0) |
| EPA ECHO NAICS 493 | BUILD_NOW warehouse seed | Regulated warehousing. Amazon and tank terminals dropped. | POTENTIAL occupied facility | [ECHO web services](https://echo.epa.gov/tools/web-services). Unfiltered radius search is still noise. |
| Google Places Text Search (New) | BUILD_NOW with `--paid` | Named 3PL / DC / farm POIs | POTENTIAL | [Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search). Cache `place_id` only. |
| Google reverse Geocoding | WITNESS_ONLY with `--paid` | Street or plus-code for nameless OSM boxes | not a listing | [Geocoding](https://developers.google.com/maps/documentation/geocoding/overview). 30-day lat/lng cache. Added to the challenge key this session. Live unnamed Houston industrial pin: `MPWW+C2 Meadowbrook / Allendale, Houston, TX`. |
| Google Elevation | WITNESS_ONLY with `--paid` | Height in meters, one batch request | never score | Same unnamed pin: 8.27 m, 4.8 m resolution. Not USGS 3DEP. |
| Google Routes matrix | WITNESS_ONLY with `--paid` | Drive seconds / meters to the search origin | never score | Uses ADC like `adapters/routes.py`. Maps key still blocks Routes. Live: 6.7 km / 646 s toward Port Houston from that pin. |
| Street View metadata / Aerial / Static Maps | WITNESS_ONLY | Pano date, aerial videoId, PNG for display | never score | Static Maps HTTP 200 on this key. Do not OCR tiles. Aerial: no cache video. |
| Places Nearby / Autocomplete | SKIP | Farm nearby returned a garden center and a coffee shop. Autocomplete returned "Warehouse Center Drive". | n/a | Text Search stays the only Places seed. |
| Air Quality, Pollen, Weather, Address Validation, Roads, Time Zone | SKIP | Pin weather, not sites | n/a | APIs exist on the project. Blocked on this key. Not inventory. |
| Earth Engine Dynamic World | WITNESS_ONLY on `--budget deep` | built/water/crops probability in a 60 m buffer | not a parcel | [DYNAMICWORLD/V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1). Open Buildings v3 is not US. Other EE collections (JRC water, CDL, climate) already live in expedition screening, not this harness. |
| Ask Google Earth / Earth AI | BLOCKED | Browser spatial chat | n/a | [overview](https://developers.google.com/maps/documentation/earth/gemini/overview). No export API. Imagery search is Earth Professional UI only. |
| RentCast `/listings/sale` | NO_KEY | Active US residential / some vacant land | LISTED if `id` + `lastSeenDate` | [Listings](https://developers.rentcast.io/reference/property-listings). Explicitly **no** office, retail, industrial, manufacturing, agricultural. |
| Mireye fetch/batch | WITNESS_ONLY | Flood / wetland / slope on pins you already have | does not mint candidates | [batch](https://docs.mireye.ai/api-reference/fetch-batch.md), 25 locations, quote first |
| Regrid `/parcels/query` | PARTNER | Off-market parcel filter (acreage, flood, land use) | POTENTIAL land, not listed | [query endpoint](https://support.regrid.com/api/parcel-api-endpoints). Paid. Closest thing to real land discovery. |
| CREXi / CoStar / LoopNet / RESO / Zillow Bridge | PARTNER | Actual commercial or MLS listings | LISTED after a license | CREXi Sales API is credential-gated. RESO is a standard, not a feed. Do not scrape Realtor/Redfin ToS. |
| LightBox / ATTOM | PARTNER | Parcel + tax + some hazard | POTENTIAL | Vendor license |
| Overture buildings/places | DEFERRED | Building footprints / GERS places | POTENTIAL | Bulk download, not a tiny HTTP search |
| EIA Open Data API | DEFERRED | Time series. Plants come from the ArcGIS layer above. | n/a | [EIA API](https://www.eia.gov/opendata/documentation.php) |
| EPA ECHO unfiltered | WITNESS_ONLY | RMP drill-down after a Mireye hit | already in `adapters/epa.py` | Do not use raw radius search as warehouse inventory |
| Mapbox / CARTO / Google Maps MCP | OVERLAP | Geocode, POI, GIS agents | POI ≠ inventory | Useful later as another Places-class seed, not a listing feed |

## What is better than more OSM tags

1. Places is on. Still POTENTIAL POIs, still Google ToS (no durable cache of names/addresses).
2. Regrid-class parcel query for developable land (acreage + flood + zoning label).
3. A licensed CRE feed if the product is "sites you can actually lease."
4. RentCast for Home only. Do not pretend it covers warehouses.

`--paid` adds Places plus reverse geocode, elevation, Solar, Street View, Aerial, and Routes.
