# Due-diligence advisory — San Leon, TX (Galveston Bay shore)
**Verdict: KILL**  ·  2026-08-13  ·  pin 29.475732, -94.966533

Prepared for the buyer's agent of record. This advisory cross-examines the official cited record against independent public satellite evidence. It is not a survey, appraisal, or legal advice.

## The record (as cited)
| Fact | Value | Source | Vintage |
|---|---|---|---|
| Ground elevation | 2.37 meters | [USGS_3DEP_COG](https://www.usgs.gov/3d-elevation-program) | 3DEP 1/3 arc-second seamless DEM |
| FEMA flood zone | AE | [FEMA_NFHL](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28) | 48167C_STUDY1 |
| Intersects wetland | True | [USFWS_NWI](https://www.fws.gov/program/national-wetlands-inventory) | — |
| Surface-water permanence | 5.00 percent | [JRC_GSW](https://global-surface-water.appspot.com/) | — |
| Soil drainage | Somewhat poorly drained | [NRCS_gNATSGO](https://storage.googleapis.com/mireye-earth-data/soils/gnatsgo_mukey_conus_fy2025.tif) | — |

## Where the record and the Earth disagree

### Fight 1: TIME
- **The record claims:** record says water 5% of the time
- **The witness says:** JRC monthly history: dry 1985-2000 (baseline 0.03% of months), wetting since 2001, 10.8% of months by 2021
- **Numbers:** `{"recorded_permanence_pct": 5.0, "observed_2021_pct": 10.8, "baseline_pct": 0.03, "breakpoint_year": 2001}`

### Fight 2: HEIGHT
- **The record claims:** record says ground at 2.37 m (USGS_3DEP_COG)
- **The witness says:** FABDEM says 0.75 m — 1.62 m lower; NASADEM says 2.68 m. Flood-depth math flips on a 1.6 m disagreement this close to the shore (743 m).
- **Numbers:** `{"record_m": 2.3652405738830566, "fabdem_m": 0.75, "nasadem_m": 2.68, "gap_m": 1.62, "height_gated": true}`

**Aggravating context:** already zone AE (48167C_STUDY1) and intersects a mapped wetland

## Evidence
- `water_timeline.svg` — 37-year monthly-water history at the pin (JRC/GSW1_4/MonthlyHistory, red bars = post-breakpoint years)
- `evidence.json` — full year-by-year values and both elevation models (NASA/NASADEM_HGT/001, projects/sat-io/open-datasets/FABDEM)
- All record values above carry their federal source and retrieval timestamp via the Mireye API.

## Recommendation
Advise the client to withdraw. Two independent public witnesses contradict the record this parcel would be priced on. If the client proceeds regardless, price the contradiction, not the record.