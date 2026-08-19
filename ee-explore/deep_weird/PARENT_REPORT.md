# EE deep_weird — parent report

**80 probes · 68 OK · 12 FAIL** · project `gen-lang-client-0261050164`  
Artifacts: `deep_weird_results.json`, `run_probes.log`, `thumbs/` (22 PNGs), `run_probes.py`

---

## What most people miss (and actually loads)

These are real, loadable catalog assets that sit outside the usual Landsat/S2/DEM diet:

| Theme | Asset | Notes |
|---|---|---|
| **Methane plumes (ISS hyperspectral)** | `NASA/EMIT/L2B/CH4PLM`, `…/CH4ENH` | Plume complexes in ppm·m; only where plumes detected. ~1590 scenes Aug 2022–Oct 2024. **Deep-dive winner.** |
| **Hyperspectral reflectance** | `NASA/EMIT/L2A/RFL` | Hundreds of `reflectance_*` bands → `toArray()` works |
| **TROPOMI atmosphere** | `COPERNICUS/S5P/OFFL/L3_CH4`, `…/L3_NO2`, also CO/SO2/HCHO/AER_AI | Daily columns; CH4 is OFFL-only |
| **TEMPO NO2 (N. America)** | `NASA/TEMPO/NO2_L3` (deprecated → `…_V4`) | Hourly-ish geostationary NO2 |
| **Night lights change** | `NOAA/VIIRS/DNB/ANNUAL_V21`, monthly `…/VCMSLCFG`, legacy `NOAA/DMSP-OLS/NIGHTTIME_LIGHTS` | Annual difference thumbs worked |
| **Population** | `CIESIN/GPWv411/…`, `JRC/GHSL/P2023A/GHS_POP`, community `projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL` | LandScan is community, not “core” catalog branding |
| **Open Buildings temporal** | `GOOGLE/Research/open-buildings-temporal/v1` | Height / presence / fractional count (Africa+S Asia+LatAm — **not US**) |
| **Open Buildings polygons** | `GOOGLE/Research/open-buildings/v3/polygons` | FC; same geography limits |
| **Soil** | OpenLandMap soil taxonomy / texture / pH; `ISDASOIL/Africa/v1/ph` | Global + Africa-specific |
| **Wildlife / habitat** | `USGS/GAP/CONUS/2011` landcover; `USGS/GAP/PAD-US/v20/*`; `WCMC/WDPA/current/polygons` | GAP is CONUS habitat classes |
| **Geology-ish** | `CSP/ERGo/1_0/US/lithology`, topo diversity | Not full geology maps, but lithology exists |
| **Gravity / mass** | `NASA/GRACE/MASS_GRIDS_V04/LAND`, `…/MASCON_CRI` | Terrestrial water / mass anomalies |
| **Roads** | `TIGER/2016/Roads` | `TIGER/2021/Roads` **not found** |
| **Built height / human mod** | `JRC/GHSL/P2023A/GHS_BUILT_H`, `CSP/HM/GlobalHumanModification`, `Tsinghua/FROM-GLC/GAIA/v10` | GAIA = impervious change year |

Catalog docs advertise **MethaneAIR / MethaneSAT / OGIM** under EDF project paths — **this project could not load them** (`projects/edf-methanesat-ee/...` not found). Likely gated / renamed / preview-only.

---

## Hard failures (confirmed absent or broken)

- **USPVDB** — not in EE; USGS download + own asset upload only  
- **COVID mobility / traffic** — no public EE assets under guessed IDs  
- **USGS landslide inventory / ANSS ComCat** — not in EE catalog  
- **`ee.Image.kriging`** — does not exist  
- **GCS table export** to a nonexistent bucket: task starts (`READY`) then fails on credentials/bucket (logged as expected fail)  
- **Drive image export** — task starts; `getTaskList()` works  
- **`reduceRegion` pixel ceiling**: default `maxPixels=1e7`. Houston @ 1 m ≈ 1.8e9 pixels → fail even with `maxPixels=1e9`. Texas @ 10 m and CONUS @ 1 m explode. Escape hatches that worked: coarser scale (Houston @ 30 m OK) or `bestEffort=True` (Texas @ 10 m OK)

---

## Platform APIs that worked

- `getDownloadURL` (SRTM GeoTIFF URL)  
- `getThumbURL` + HTTP fetch  
- `reduceRegions` on TIGER roads × SRTM  
- `fastDistanceTransform` (distance to GSW water)  
- `cumulativeCost` from a point  
- `Geometry.coveringGrid`  
- Spatial filter/intersect: HydroATLAS basins × PAD-US  
- `ee.Image.unmix` (Landsat 3-endmember veg/soil/water)  
- `ee.data.listImages` / legacy `getList` on S5P / EMIT / VIIRS / open-buildings-temporal  

### ML

| Classifier | Train acc | Val acc | Kappa |
|---|---:|---:|---:|
| smileRandomForest(12) | 0.97 | 0.59 | 0.52 |
| smileNaiveBayes | 0.57 | 0.59 | 0.53 |
| libsvm | 0.83 | 0.67 | 0.61 |

- Clusterers present: `wekaKMeans`, `wekaXMeans`, `wekaCascadeKMeans`, `wekaCobweb`, `wekaLVQ` — KMeans on S2 succeeded  
- Gotcha: `ESA/WorldCover/v200` is an **ImageCollection**, not `ee.Image(...)`

---

## Sharpness (Houston suburb, unit-variance edge energy)

After normalizing each gray composite to unit variance (raw DN/reflectance edge energy is not comparable):

| Sensor | scale | mean edge |
|---|---:|---:|
| NAIP | 1 m | **0.304** |
| Sentinel-2 | 10 m | 0.047 |
| Landsat-8 | 30 m | 0.021 |

NAIP ≫ S2 ≫ Landsat, as expected. Thumbs: `sharp_naip.png`, `sharp_s2.png`, `sharp_landsat.png`.

---

## Deep dive: EMIT methane plumes (7/7 follow-ups OK)

Why surprising: most people stop at S5P CH4 columns. EMIT gives **spatially resolved plume footprints** (~60 m product, sparse scenes) from ISS.

1. **1590** images, 2022-08-10 → 2024-10-26  
2. **Permian**: 122 scenes intersecting AOI; plume max **7506 ppm·m**, mean where present ~175  
3. **CH4ENH** colocated (75 scenes); enhancement max ~593  
4. Plume mask ∩ GPW population → very low density (oilfield, not urban)  
5. VIIRS night lights under vs outside plume: ~7.9 vs ~8.2 (not a clean flaring signal at this aggregation)  
6. `listImages` + sample properties OK  
7. S5P CH4 under vs outside EMIT mask: **1885.3 vs 1884.5** (tiny column difference — EMIT catches local plumes S5P barely resolves)

Thumbs: `emit_permian_max.png`, `emit_enh_permian.png`, `thumb_emit_plume_permian.png`.

---

## Practical paths

1. **Atmosphere / methane stack**: EMIT plumes (local) + S5P CH4/NO2 (synoptic) + TEMPO NO2 (N. America diurnal) + VIIRS NTL (activity/flaring proxy).  
2. **People / built**: GHSL + GPW + LandScan (community) + Open Buildings temporal **outside US**; TIGER roads + PAD-US inside US.  
3. **Ground**: OpenLandMap soils + ERGo lithology + GRACE mass.  
4. **Do not expect in EE**: USPVDB, landslide inventories, earthquake catalogs, COVID mobility, traffic — upload yourself.  
5. **Compute hygiene**: never `aggregate_array` / full `.size()` on S5P-scale collections; prefer short date windows, `limit()`, `bestEffort`, or coarser scale. Default `maxPixels=1e7` is the hard wall.  
6. **Exports**: Drive tasks start fine; GCS needs a real bucket + IAM. Kriging is not a native op.
