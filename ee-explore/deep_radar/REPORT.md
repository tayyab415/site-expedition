# Deep Radar / SAR Exploration Report

**Generated:** 2026-08-12  
**Experiments:** 111 (ok=92, fail=19)  
**Root:** `/home/tayyabkhan/Shared/mireye-challenge/ee-explore/deep_radar/`

| Artifact | Path |
|---|---|
| Experiment JSON log | `logs/experiments.json` |
| Run log | `logs/run.log` |
| Thumbnails (~96 PNGs) | `thumbs/` |
| Main script | `scripts/deep_radar_explore.py` |
| Index | `FINDINGS.md` |

## Sites probed
- Galveston Bay, Clear Lake, Port of Houston
- Houston / West Houston / Addicks–Barker (Harvey 2017)
- Gulf shipping lane south of Galveston
- Mississippi River near Greenville, MS (2019 flood year)
- Controls: Greenland GIMP RADARSAT mosaic; Denver coherence point

---

## Five “whoa” findings (with numbers)

### 1. Wind can swing Gulf VV by ~11 dB — and ship detectors fall apart
On descending IW scenes over the Gulf AOI in 2023, the calmest scene mean VV was **-22.25 dB** and the roughest **-11.28 dB** (**Δ +10.97 dB**). Monthly means ran from July **-18.48 dB** to February **-12.47 dB**. A naive “background + 8 dB” bright-pixel rule flagged **56,520** pixels on the calm scene vs only **416** on the rough scene. Wind/roughness is first-order for marine SAR.

### 2. Orbit geometry beats land-cover for Galveston brightness
2023 Galveston median VV: ascending **-15.42 dB**, descending **-12.91 dB**. Per relative orbit: **#34** asc @ mean incidence **43.9°** → VV **-17.24 dB**; **#136** asc @ **31.9°** → **-13.43 dB**; **#143** desc @ **31.5°** → **-12.91 dB**. Scene-level corr(VV, incidence angle) ≈ **-0.52**. Mixing orbits without angle control invents fake change.

### 3. Public seasonal coherence: city ~0.89, open water ~0.03
`Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/COHERENCE` winter VV 12-day coherence point samples: Houston **0.89**, Galveston land **0.70**, Clear Lake **0.56**, open Gulf **0.03**, Denver **0.42**. Decay-model tau (same family): Houston **7.6**, Galveston **9.6**, open Gulf **2.8**, Denver **12.2**. This is the closest thing to InSAR inside the public EE catalog. Raw S1 SLC / interferogram collections are **not** available (`COPERNICUS/S1_SLC` etc. all 404).

### 4. L-band PALSAR-2 ScanSAR brightened during Harvey (+1.64 dB)
Over west Houston, dual-pol ScanSAR HH means: pre-landfall **-5.64 dB** → peak Aug 27–29 **-4.01 dB** (**+1.64 dB**). Multiple ScanSAR dates exist in-window (Aug 17, 22, 27, 29, Sep 5). This matches the classic L-band flooded-vegetation double-bounce response — opposite intuition from “water = dark” at C-band over open water.

### 5. Inland river SAR flood mapping works at scale; urban Harvey is messy
Mississippi River AOI near Greenville: 2019 wet-vs-dry mask ≈ **331 km²** (mean dVV **-1.43 dB**); 2023 spring-vs-summer extra wet ≈ **201 km²**. Houston Harvey median-stack flood area is threshold-fragile: **2.1 → 32.1 km²** across five cutoff sets. Same-orbit IW pair (2017-08-05 → 08-29, orbit 34) over west Houston has **both** tails (dVV p10 **-3.87**, p90 **+4.13**, mean **+0.46 dB**) — not a clean “everything got darker” story. During the Harvey week, Sentinel-2 had **8** scenes at **~59%** mean cloud while Sentinel-1 had **3** usable passes.

---

## What worked well
- **VV/VH dual-pol IW** everywhere in Texas; 2023 Galveston: **114** scenes (84 asc / 30 desc), orbits 34, 136, 143.
- **Urban vs water:** downtown VV **-8.10 dB** vs Clear Lake **-12.17 dB** (Δ **4.07 dB**); double-bounce proxy (VV>-8 & VV−VH>7) ≈ **51.8 km²**.
- **Speckle:** 50 m `focalMedian` cut open-Gulf dB std **1.94 → 1.19**. Native `refinedLee` is **not** an `ee.Image` method.
- **Ship / platform thread:** absolute VV>-5 gave thousands of bright pixels; persistent fraction >0.35 found **35** platform-like objects; local-contrast CFAR (VV − 800 m median > 8 dB) found **138** objects / 1536 pixels.
- **OPERA RTC** (76 scenes mid-2023 Galveston) and **OPERA DSWx-S1** (90 scenes in 2024 over Houston) load cleanly.
- **ALOS yearly mosaic + FNF4 + ScanSAR** all usable; LHScat scatterometer loads; GIMP RADARSAT mosaic works over Greenland only.
- **Seasonal composites** for Galveston, Houston floodplain, Port Houston, MS River (DJF/MAM/JJA/SON). Port seasonal |dVV|>3 dB area ≈ **40.9 km²**.

## What failed (useful negatives)
| Attempt | Result |
|---|---|
| UAVSAR / ICEYE / Capella / NISAR | Not in public EE catalog |
| `COPERNICUS/S1_SLC` (any path) | Not found — no raw InSAR in EE |
| Japan `StripMap_202401` over Texas | 0 scenes |
| EW mode over Houston | 0 scenes |
| HH IW over Galveston (2015–2024) | 0 scenes |
| S1 before 2014 | Empty |
| Linear-domain ENL via `reduceRegion` on ocean | Often null (numerical); use dB std instead |
| GRD vs GRD_FLOAT same-index compare | Brittle when first scene lacks VV |
| `mode()` DSWx over full year then `.select` after empty | Band errors if pipeline order wrong |

## Interferometry note
EE does **not** host Sentinel-1 SLC or ready interferograms. The practical InSAR-adjacent public assets are the Earth Big Data **seasonal coherence / backscatter / decay-parameter** mosaics (2019/2020 epoch). For true interferometry you leave EE (ASF HyP3, COMET, etc.).

## Thumbnail highlights
- `thumbs/gulf_calm_sea_VV.png` / `gulf_rough_sea_VV.png` — wind contrast  
- `thumbs/harvey_*` / `alos_lband_harvey_*` / `alos_scansar_houston_*` — flood thread  
- `thumbs/coherence_winter_vv_coh12_texas.png` — coherence land/water  
- `thumbs/gulf_persistent_vs_transient_bright.png` / `gulf_cfar_ships.png` — ships/platforms  
- `thumbs/galveston_orbit{34,136,143}_VV.png` — geometry  
- `thumbs/ms_river_2019flood_*.png` — inland flood  
- `thumbs/seasonal_*` — four sites × four seasons  

## Method note
All probes used `ee.Initialize(project='gen-lang-client-0261050164')` with the workspace `.venv-ee` Python. Every experiment appends to `logs/experiments.json` with name, ok/fail, params, numeric results, thumbnail paths, and notes.
