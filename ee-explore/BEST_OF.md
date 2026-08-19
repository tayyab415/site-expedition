# Earth Engine exploration — one-page best of

**When:** 11–12 Aug 2026  
**Where:** `ee-explore/` (deep digs + older smoke tests)  
**Scale:** ~350 files · ~400+ probes across radar / time / ocean / weird / local  
**Status:** research done · no product built yet

---

## What we actually proved works

| Superpower | Plain English | Proof we ran |
|---|---|---|
| **AI land fingerprints** | Google turns each year of satellites into a 64-number “vibe” per pixel. Compare years → see change. | Ashburn changed more than Miami/Houston (2017→2024). Hot pixels ~0.75 change score. |
| **Air from space** | Pollution and methane columns from TROPOMI. | Summer 2023 NO₂: NYC ≈ LA ≫ Houston ≫ Bakken. Bakken CH₄ drifts by month. |
| **Radar through clouds** | Sentinel-1 sees land/water when cameras can’t. | Harvey week: S2 ~59% cloudy; S1 still had usable passes. Inland river flood masks worked (MS River ~331 km²). |
| **Storm rain maps** | GPM IMERG paints extreme rain. | Harvey window: ~**860 mm** (~34 in) after fixing half-hour units. |
| **Ocean color + heat** | Bay vs open water, heatwaves, currents. | Galveston Bay chlorophyll ~**138×** open Gulf. Aug 2023 Gulf often >1°C warm anomaly. Loop Current ~0.5 m/s. |
| **Height models disagree** | Different DEMs don’t match on the coast. | San Leon: FABDEM **0.7 m** vs NASADEM **3 m**. Flood math flips. |
| **Historic floods catalog** | MODIS flood events as ready layers. | **37** events near Houston in Global Flood DB. |
| **Hidden gems** | Stuff people skip in the catalog. | NASA EMIT methane plumes, TEMPO NO₂, seasonal S1 coherence, OPERA flood products, Allen Coral Atlas seagrass. |

---

## Top “whoa” moments

1. **Wind wrecks naive ship detection** — calm Gulf vs rough Gulf: ~11 dB VV swing; fake “ships” go from tens of thousands of pixels to hundreds.
2. **Mixing radar orbits invents fake change** — ascending vs descending Galveston VV differs by ~2.5 dB; incidence angle matters.
3. **Urban Harvey is messy in radar** — open-water “dark = flood” fails in cities; L-band PALSAR actually *brightened* (~+1.6 dB) over west Houston (flooded vegetation vibe).
4. **Lake Mead lost water; Louisiana delta gained** — JRC decade water-frequency deltas show real drying/wetting patterns beyond Galveston.
5. **AI change ≠ always new buildings** — Ashburn’s hottest embedding pixel looked like farmland in NAIP early/late; change can be crops/edges too.
6. **MethaneSAT / fishing hours** — advertised or guessed IDs **blocked** without special access. EMIT plumes *do* load.

---

## Hard lessons (don’t ignore)

- JRC water `occurrence`: always `.unmask(0)` before averaging, or ponds poison dry land.
- IMERG `precipitation` is **mm/hour** on half-hourly grids → multiply by **0.5** when summing to get mm.
- `maxPixels` will explode on big/fine regions; use coarser scale or `bestEffort`.
- Open Buildings temporal is **not US-complete**.
- CGMD mangrove “2023 area drop” looks suspicious — re-check before trusting.

---

## Where the evidence lives

| Thread | Folder | Start here |
|---|---|---|
| Radar | `deep_radar/` | `REPORT.md`, `logs/experiments.json` |
| Time / change | `deep_timeseries/` | `results.json` |
| Ocean / coast | `deep_ocean/` | `deep_ocean_results.json` |
| Weird catalog / ML | `deep_weird/` | `PARENT_REPORT.md` |
| Air + embeddings | `deep_local/` | `mega_log.json`, `embeddings/` |
| Quick thumbs | `horizon_thumbs/`, `build_thumbs/` | PNGs |

---

## Strongest product-shaped threads (if we build next)

1. **Change agent (AI embeddings + Dynamic World)** — “this parcel flipped” for site-acq / loan desks; game skin still fits.  
2. **Cloud-proof flood witness (S1 + IMERG + Flood DB)** — act when cameras are blind.  
3. **Coast truth (DEM disagreement + water trend + bay greenness)** — don’t trust one height or one flood map.

---

*Not a submission. A map of what Earth Engine can do for us, with receipts.*
