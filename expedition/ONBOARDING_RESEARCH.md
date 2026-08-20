# Onboarding research: what the first page should ask

**Date:** 20 August 2026  
**Question:** The first onboarding page does not collect the specs a person actually uses to place a site (size, program, power, slope). What should it ask, and what can this product honestly enforce?

This is a research note, not a product freeze. Implementation is a separate change.

## What the first page actually asks today

Visible without opening **Adjust the plan**:

1. Mission tiles (warehouse, farm, home, data center, custom)
2. A free-text box ("Read this")
3. Examine vs Discover
4. City / metro, or a region dropdown
5. One flood checkbox
6. A plan summary card and **Find geographies**

Size, site form, budget, water/sewer/fiber, preference weights, investigations, and route anchors all live inside a collapsed `<details>` in `ui/index.html`. Warehouse is preselected. Size defaults to `flexible`. Power is never asked.

The previous rewrite hid those controls on purpose. The swipe-session stills show the older page dumping every envelope, constraint, preference, and investigation at once. That was unusable. Hiding everything was the overcorrection. The specs that change the search disappeared with the noise.

## The controls already exist. They do not screen.

`SIZE_BANDS` in `ui/app.js` already has warehouse sq-ft bands, farm acre bands, home living-area bands, and data-center acre bands. `compile_plan` in `plan.py` will stamp `size_band:…` onto `hard_constraints` when the band is not `flexible`.

`verdict.py` then does this: if the candidate record has no matching `size_band` field, it opens a Verification Gap. It does not reject. Curated pins in `data/candidates.json` have no size at all, so a user who picks "250k–500k sq ft" still sees San Leon, Alliance, and the rest. The declared size is a note, not a filter.

The intent parser in `intent.py` always writes `size_band: "flexible"`. "250,000 square foot warehouse near Dallas" never sets a band.

Electrical capacity is an always-on gap for warehouse and data center (`plan.py`). The product never asks how much load the operation needs, so every survivor is Conditional on a utility letter whether the user wanted a 200 kW last-mile shed or a 200 MW hall.

Default warehouse route anchors are Port of Houston and a San Antonio customer pin, even if the search is Chicago.

## What "warehouse" actually means in the industry

NAIOP splits industrial into manufacturing, warehouse/distribution, and flex. It does **not** classify by a single square-footage cutoff. The 2017 Industrial Building Types Matrix (still the published matrix; 2024 restates the same types) treats size as "any" for most types, then distinguishes them by use, clear height, docks, office share, and truck-turning radius:

| Type | Typical traits from the matrix |
|---|---|
| Manufacturing | Any size. Clear height 10 ft+. Docks vary. Office under 20%. |
| General warehouse | Any size. Clear height 16 ft+. Door ratio about 1:5k–15k sf. |
| Distribution / truck terminal | Denser doors. Turning radius 120–130 ft. |
| Fulfillment / high-cube | 100,000–1,000,000+ sf. Clear height 32 ft+. Very high truck parking. |
| Flex | Clear height 10–24 ft. Office 30–100%. Turning radius ~110 ft. |

Sources: [NAIOP 2017 Terms and Definitions](https://www.naiop.org/globalassets/research-and-publications/report/terms-and-definitions-/researchreportcre-terms-and-definitions-2017.pdf) (Industrial Building Types Matrix, pp. 22–25); [NAIOP 2024 Terms](https://www.naiop.org/globalassets/research-and-publications/report/terms-and-definitions-/naiop-2024-terms-and-definitions.pdf) (manufacturing, warehouse, flex, last-mile, truck terminal, cold storage, fulfillment).

CBRE's market reports treat **big-box** as a warehouse or DC of **at least 200,000 sq ft**. That is a market slice, not a building class. Source: [CBRE 2024 North America Industrial Big-Box](https://www.cbre.com/insights/reports/2024-north-america-industrial-big-box).

EIA CBECS 2018 "warehouse and storage" is a different animal. Mean building is **17,400 sq ft**. 69% are under 10,000 sf. Less than 1% exceed 500,000 sf. Site electricity intensity for warehouse buildings that use electricity is **7.9 kWh per square foot per year**. Source: [EIA CBECS warehouse PBA](https://www.eia.gov/consumption/commercial/pba/warehouse-and-storage.php); [Table C22](https://www.eia.gov/consumption/commercial/data/2018/ce/pdf/c22.pdf).

That 7.9 kWh/sf number is why a normal 250,000 sf warehouse is a small electrical load (on the order of a few hundred kW average, under 1 MW peak if it is lights and HVAC). Cold storage and manufacturing are not that building.

Our current warehouse bands (under 100k / 100–250k / 250–500k / 500k+) are closer to industrial CRE practice than to CBECS. They are the right *kind* of question. They are just not on the first page, and they do not drive screening.

## Factory power is not warehouse power

EIA MECS 2022 (manufacturing, not commercial warehouses):

- 12.3 billion sq ft of manufacturing floorspace
- Four industries (chemicals, petroleum and coal, paper, primary metals) dominate energy use
- Average enclosed floorspace is largest in primary metals (268,642 sf), paper (233,352 sf), and transportation equipment (200,798 sf)

Source: [2022 MECS results](https://www.eia.gov/consumption/manufacturing/data/2022/pdf/2022%20MECS%20Results.pdf).

A factory is a process load. Asking "warehouse or not" does not capture it. This product has no manufacturing Mission. The closest path is warehouse plus the `electrical_capacity` gap, which never asks for MW.

Data halls are worse. CRS R48646 (26 Aug 2025) cites industry definitions of hyperscale as exceeding **100 MW**, and notes that 100 MW continuous is on the order of **80,000 US households**. Direct cooling water for a 100 MW US data center is illustrated by IEA as roughly **2,600 households**. Source: [CRS R48646](https://crsreports.congress.gov/product/pdf/R/R48646).

Mireye will not clear that load. `grid-readiness` is written to prioritize and name proxies. It must not claim deliverable MW. The onboarding question is still worth asking, because a 200 kW warehouse and a 200 MW hall should not run the same field list or the same "we don't know about power" shrug.

## What Mireye can actually answer (catalog 0.15.0)

Live presets from `mireye://catalog/presets`: `terrain`, `flood_risk`, `wildfire_underwrite`, `land_cover`, `site_selection`, `building_lookup`, `utilities`, `boundaries`, `natural_hazard`, `grid_interconnect`, `data_center_siting`, `solar_siting`, `wind_siting`, `storage_siting`, `points_of_interest`.

Useful for a declared program:

| User asked | Can screen now | Honest limit |
|---|---|---|
| Flat land | `slope_degrees` (USGS 3DEP). Hint in catalog: >25° complicates conventional construction. | Point slope, not a pad grading plan. |
| Existing building size | `primary_building_footprint_sqm` (Overture). 1 credit. Not parcel-group. | Footprint, not rentable area, not clear height, not dock count. |
| Land area | `parcel_area_m2` (Regrid). | **Parcel-group.** `DECISIONS.md` forbids parcel-group spends unless the human opts in. Without that, land size stays a gap. |
| Flood | `within_floodplain_polygon`, `fema_flood_zone` | FEMA SFHA, not a flood-insurance quote. |
| Wetland | `intersects_wetland` | NWI presence, not a delineation. |
| Power nearby | `nearest_substation_distance_m`, `nearest_substation_max_voltage_kv` (EIA Atlas). Catalog hint: 69 kV may be too weak for 200 MW+. | Distance and published voltage. **Not** a will-serve letter. |
| Transmission | `nearest_transmission_line_voltage_kv`, `max_transmission_line_voltage_kv_within_radius` | Geometry proximity. |
| Queue pressure | `interconnection_queue_active_capacity_county_mw` | County aggregate, not this tap. |
| Industrial price | `avg_retail_electricity_price_industrial_usd_per_kwh` | State (sometimes utility territory). Areal. |
| Water / sewer mapped | `within_water_service_area`, `within_sewer_service_area` | Service-area polygon, not capacity. |
| Fiber observed | `fiber_broadband_available`, `fiber_provider_count` | Not carrier-diverse enterprise fiber. |
| Cultivated | `is_cultivated`, `dominant_crop_5y` | Cover, not a water right. |
| Building present | `primary_building_overture_class` | Helps site form. Does not prove the building is the right program. |

`data_center_siting` is the heavy preset (cooling, water, fiber, hazards, interconnect). Warehouse core fields in `plan.py` are a short logistics screen. They do not include substation voltage, transmission class, or industrial price unless we add them when the user declares a large load.

Mireye does not search a region. Discovery still needs OSM / footprints / user pins. Size and power declarations can prefilter those seeds (large Overture footprints, substations above a kV floor). They cannot invent LISTED inventory.

## Studio already has the programs. Onboarding ignores them.

`studio.py` ships warehouse programs NAIOP would recognize: cross-dock 80×40, bulk 120×60, last-mile 60×30, cold storage 80×50, light flex 70×40, high-cube fulfillment 100×60, truck terminal 90×45, office/warehouse hybrid 50×36. Farm has packing shed and shop. Data center has a 48×32 hall shell. Home has a 16×12 massing.

Those presets appear after the board opens, on FUTURE. They do not set the Mission Plan. A user placing a last-mile van facility and a user placing a high-cube box currently confirm the same warehouse plan.

The studio footprints are also tiny relative to the size bands. Cross-dock 80×40 m is about 34,000 sq ft. High-cube 100×60 m is about 64,500 sq ft. Both sit in "under 100k". The visual concept is a diagram, not the search size. Do not use the glTF as the size band.

## Proposed first page

One screen. Four questions that change the Expedition. Everything else stays under Adjust.

### 1. What are you placing

Keep the four Missions. Do **not** add a fifth "factory" Mission in this pass. Manufacturing is a warehouse/industrial program with a load band, until we have a reviewed field list and gates for process plants (air nonattainment, RCRA, water, gas, rail). Custom remains the escape hatch.

Under warehouse, show program chips that map to studio presets and to defaults:

| Chip | Size default | Power default | Site form hint | Extra hard asks |
|---|---|---|---|---|
| Last-mile / city distribution | under 100k sf | lighting/HVAC | existing or land | urban, docks, not rail |
| Cross-dock / truck terminal | 100–250k | lighting/HVAC | either | truck court, highway |
| Bulk / high-cube | 250–500k or 500k+ | lighting/HVAC | land or existing big box | rail useful, flood veto |
| Cold storage | 100–250k | process (few MW) | existing or land | water, power, flood |
| Light industrial / flex | under 100k | lighting or small process | existing | sewer/water optional |
| Light manufacturing | 100–250k | process | land or existing | power, air, rail optional |

Farm, home, and data hall keep their current Mission. Home "flat" means slope, not an apartment. If someone wants a residential apartment, this product is the wrong tool; Home is a lot from constraints.

### 2. How big

Visible. Required unless they pick Flexible.

- Warehouse: building sq-ft band (keep the four bands). Show a land hint, not a second required field: at ~35% coverage a 250k box wants on the order of 15–20 acres of truck court and parking. That hint is planning arithmetic, not a Mireye fact.
- Farm: acre band (already defined).
- Home: living-area band (already defined). Lot size stays a gap without parcel opt-in.
- Data hall: acre band **and** a load band (below).

When site form is **existing asset**, cheap-screen `primary_building_footprint_sqm` against the band. Convert sq m to sq ft. Unknown footprint is Conditional, not Strong Fit. When site form is **developable land**, do not fetch parcel area unless the human opts into parcel-group. Stamp `site_size` as a blocking gap, same as today, but say so on the card.

### 3. What the site has to take (mission-specific, three or fewer)

Warehouse / manufacturing / data hall:

- **Load band:** lighting/HVAC only · process (about 1–20 MW) · large load (20–100 MW) · hyperscale (100 MW+) · not sure
- Lighting/HVAC: keep current warehouse fields. Electrical capacity stays a gap but does not dominate the card.
- Process or above: add `nearest_substation_max_voltage_kv`, transmission voltage, industrial price. Prefer grid proximity. Still never claim MW.
- Hyperscale: switch the fetch toward `data_center_siting` even if the Mission tile was warehouse. Water service becomes a real question. Fiber redundancy stays a gap.

Also on this row, only the gates that are actually binary:

- Warehouse default: flood veto (already there)
- Optional chips: rail, major highway, mapped water, mapped sewer
- "Must be flat" as a slope gate, e.g. reject or Conditional above ~5° for a big box, ~15° as a warning. Pick a band, do not put a slider.

Farm: cultivated required, drought as preference, water right always a gap.

Home: flood, slope, wildfire. No labor. No "nice neighborhood".

Data hall: flood, heat, grid proximity, fiber observed. MW and redundant fiber remain gaps.

### 4. Where

Keep city/metro. Drop the Texas-shaped default once a city is typed. Do not attach Houston and San Antonio anchors unless the user names destinations. Warehouse should ask "where do trucks go?" as one optional line, not two baked-in Texas pins.

## What stays in Adjust the plan

Scan budget. Geography widening. Acquisition budget (always a gap without a licensed price feed). Optional investigations. Preference *weights*. Custom manifest. Route-anchor lat/lng editor.

If the first page is doing its job, most people never open that drawer.

## What not to do

- Do not restore the old all-controls dump.
- Do not add a MW number field that looks like a utility letter.
- Do not fetch `parcel_area_m2` on every Find-a-Site click.
- Do not treat studio glTF dimensions as the search size.
- Do not parse free text and skip the visible bands. The box can *propose* chips. The chips are the plan.
- Do not invent a factory Mission until there is a reviewed field list and at least one held-out gate.

## Implementation order if this is accepted

1. Promote size band and warehouse program chips onto the first page. Wire intent parsing for sq-ft and acre phrases. Keep verdict behavior (gap, not fake reject) until candidates carry size.
2. Add a load band on warehouse and data hall. Expand `FIELDS` when the band is process or above. Copy stays "nearby voltage is not capacity".
3. For Examine + existing asset, compare Overture footprint to the size band.
4. Stop injecting Texas route anchors when the Search Region is not Texas.
5. Only then consider a manufacturing Mission.

## Sources

- Current UI: `expedition/ui/index.html`, `expedition/ui/app.js` (`SIZE_BANDS`, `MISSION_COPY`)
- Plan / verdict: `expedition/plan.py`, `expedition/verdict.py`, `expedition/intent.py`
- Studio programs: `expedition/studio.py`
- Spend rule: `expedition/DECISIONS.md` (parcel-group opt-in)
- Catalog: Mireye `GET /v1/meta/fields` via MCP, version 0.15.0, 20 Aug 2026
- NAIOP 2017 Terms: https://www.naiop.org/globalassets/research-and-publications/report/terms-and-definitions-/researchreportcre-terms-and-definitions-2017.pdf
- NAIOP 2024 Terms: https://www.naiop.org/globalassets/research-and-publications/report/terms-and-definitions-/naiop-2024-terms-and-definitions.pdf
- CBRE 2024 Industrial Big-Box: https://www.cbre.com/insights/reports/2024-north-america-industrial-big-box
- EIA CBECS 2018 warehouse PBA: https://www.eia.gov/consumption/commercial/pba/warehouse-and-storage.php
- EIA CBECS Table C22: https://www.eia.gov/consumption/commercial/data/2018/ce/pdf/c22.pdf
- EIA MECS 2022 results: https://www.eia.gov/consumption/manufacturing/data/2022/pdf/2022%20MECS%20Results.pdf
- CRS R48646 (26 Aug 2025): https://crsreports.congress.gov/product/pdf/R/R48646
