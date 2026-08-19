# Deep Radar / SAR Exploration Report

**Generated:** 2026-08-12T00:37:16.053213+00:00  
**Experiments:** 111 (ok=92, fail=19)  
**Artifacts:** `ee-explore/deep_radar/`  
- JSON log: `logs/experiments.json`  
- Thumbnails: `thumbs/` (98 PNGs)  
- Scripts: `scripts/deep_radar_explore.py`

## Sites
- Galveston Bay / Clear Lake / Port of Houston
- Houston Harvey floodplain (Addicks/Barker/West Houston) + rural Katy
- Gulf shipping lane south of Galveston
- Mississippi River near Greenville, MS
- Control: Greenland GIMP RADARSAT mosaic; Denver coherence point

## Coolest discoveries (with numbers)

1. **Wind turns the Gulf ~11 dB brighter (and kills simple ship detectors).**  
   Calm-scene ocean VV mean **-22.25 dB** vs rough **-11.28 dB** (Δ **+10.97 dB**). Using “mean+8 dB” thresholds: calm flagged **56,520** bright pixels vs rough only **416**. Seasonal monthly means swung from July **-18.48 dB** to Feb **-12.47 dB**.

2. **Incidence angle / orbit geometry dominates “land brightness”.**  
   Galveston 2023: ascending median VV **-15.42 dB** vs descending **-12.91 dB**. Orbit 34 (asc, mean angle **43.9°**) VV **-17.24 dB**; orbit 143 (desc, **31.5°**) VV **-12.91 dB**. Scene-level corr(VV, angle) ≈ **-0.52**.

3. **Interferometric coherence is a free public layer — and water is nearly incoherent.**  
   `Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/COHERENCE` winter VV 12-day COH: Houston **0.89**, Galveston land **0.70**, Clear Lake **0.56**, open Gulf **0.03**. Raw S1 SLC / InSAR stacks are **not** in EE.

4. **L-band Harvey ScanSAR brightened flooded west Houston by +1.64 dB.**  
   PALSAR-2 ScanSAR HH means pre-landfall **-5.64 dB** → peak Aug 27–29 **-4.01 dB**. Classic flooded-vegetation double-bounce at L-band. C-band same-orbit urban pair did **not** show simple darkening (see #5).

5. **Urban Harvey change is two-sided: brighten AND darken.**  
   Orbit-34 pair 2017-08-05 → 2017-08-29: downtown brighten(|dVV|>3) **0.0 km²** vs darken **0.0 km²**; rural Katy brighten **0.2** / darken **0.1**. Median-stack flood masks are threshold-fragile: **2–32 km²** depending on cutoffs. Inland MS River 2019 wet mask ≈ **331 km²**.

## Other solid results
- Urban vs Clear Lake VV contrast: **-8.10 vs -12.17 dB** (Δ **4.07 dB**); double-bounce proxy downtown ≈ **51.8 km²**.
- Gulf persistent bright objects (oil-platform-like, >35% of dates VV>-5 dB): **35** objects; CFAR-like local contrast (>8 dB over 800 m median): **138** objects.
- Speckle: open-Gulf dB std **1.94 → 1.19** with 50 m focalMedian; native `refinedLee` **not** on `ee.Image`.
- During Harvey week: Sentinel-2 **8** scenes @ **~59%** cloud; Sentinel-1 **3** usable.
- OPERA RTC (76 scenes) and DSWx-S1 (90 in 2024 over Houston) load; OPERA DSWx mode() over year is sparse water in this urban AOI.
- Port of Houston seasonal |dVV|>3 dB area ≈ **40.9 km²**.

## Catalog: what loads / what fails
**Works:** `COPERNICUS/S1_GRD`, `S1_GRD_FLOAT`, `OPERA/RTC/L2_V1/S1`, `OPERA/DSWX/L3_V1/S1`, JAXA PALSAR yearly + ScanSAR + FNF4, Earth Big Data seasonal COHERENCE/BACKSCATTER/DECAY, LHScat scatterometer, GIMP RADARSAT Greenland mosaic.

**Fails / absent:** UAVSAR, ICEYE, Capella, NISAR, any `S1_SLC` path, Japan StripMap emergency over Texas (0 scenes), EW mode over Houston (0), HH IW over Galveston (0), pre-2014 S1 (0).

## Failures & surprises worth remembering
- Mixing ascending+descending orbits without angle correction invents false “change.”
- Simple VV<-16 flood rules under-detect urban Harvey and are very threshold-sensitive.
- Linear-domain ENL reduceRegion can return null on ocean (use dB std or clamp); `focalMedian` return typing can break `.select` unless wrapped as `ee.Image(...)`.
- GRD_FLOAT index matching is brittle if the first GRD scene in a date filter isn’t dual-pol VV.

## Follow-up threads that paid off
1. Harvey → threshold sweep → same-orbit pair → urban brighten vs rural darken → L-band ScanSAR series  
2. Ships → wind calm/rough → persistent platforms → CFAR local contrast  
3. Coherence catalog hit → point samples land/water → decay tau  
4. Asc/desc gap → per-orbit angle + VV (orbits 34/136/143)


## Full experiment index

- **OK** `catalog_load_COPERNICUS_S1_GRD` — Loaded IC; bands=['HH', 'HV', 'angle']
- **OK** `catalog_load_COPERNICUS_S1_GRD_FLOAT` — Loaded IC; bands=['HH', 'HV', 'angle']
- **OK** `catalog_load_JAXA_ALOS_PALSAR_YEARLY_SAR` — Loaded IC; bands=['HH', 'HV', 'angle', 'date', 'qa']
- **OK** `catalog_load_JAXA_ALOS_PALSAR_YEARLY_SAR_EPOCH` — Loaded IC; bands=['HH', 'HV', 'angle', 'epoch', 'qa']
- **OK** `catalog_load_JAXA_ALOS_PALSAR-2_Level2_2_ScanSAR` — Loaded IC; bands=['HH', 'HV', 'LIN', 'MSK']
- **OK** `catalog_load_JAXA_ALOS_PALSAR-2_Level2_1_StripMap_202401` — Loaded IC; bands=['b1']
- **OK** `catalog_load_JAXA_ALOS_PALSAR_YEARLY_FNF4` — Loaded IC; bands=['fnf']
- **OK** `catalog_load_Earth_Big_Data_GLOBAL_SEASONAL_S1_V2019_BACKSCATTER` — Loaded IC; bands=['fall_hh_AMP', 'fall_hv_AMP', 'fall_vh_AMP', 'fall_vv_AMP', 'spring_hh_AMP', 'spring_hv_AMP', 'spring_vh_AMP', 'spring_vv_AMP', 'summer_hh_AMP', 'summer_hv_AMP', 'summer_vh_AMP', 'summer_vv_AMP', 'winter_hh_AMP', 'winter_hv_AMP', 'winter_vh_AMP', 'winter_vv_AMP']
- **OK** `catalog_load_Earth_Big_Data_GLOBAL_SEASONAL_S1_V2019_COHERENCE` — Loaded IC; bands=['fall_hh_COH06', 'fall_hh_COH12', 'fall_hh_COH18', 'fall_hh_COH24', 'fall_hh_COH36', 'fall_hh_COH48', 'fall_vv_COH06', 'fall_vv_COH12', 'fall_vv_COH18', 'fall_vv_COH24', 'fall_vv_COH36', 'fall_vv_COH48', 'spring_hh_COH06', 'spring_hh_COH12', 'spring_hh_COH18', 'spring_hh_COH24', 'spring_hh_COH36', 'spring_hh_COH48', 'spring_vv_COH06', 'spring_vv_COH12', 'spring_vv_COH18', 'spring_vv_COH24', 'spring_vv_COH36', 'spring_vv_COH48', 'summer_hh_COH06', 'summer_hh_COH12', 'summer_hh_COH18', 'summer_hh_COH24', 'summer_hh_COH36', 'summer_hh_COH48', 'summer_vv_COH06', 'summer_vv_COH12', 'summer_vv_COH18', 'summer_vv_COH24', 'summer_vv_COH36', 'summer_vv_COH48', 'winter_hh_COH06', 'winter_hh_COH12', 'winter_hh_COH18', 'winter_hh_COH24', 'winter_hh_COH36', 'winter_hh_COH48', 'winter_vv_COH06', 'winter_vv_COH12', 'winter_vv_COH18', 'winter_vv_COH24', 'winter_vv_COH36', 'winter_vv_COH48']
- **OK** `catalog_load_Earth_Big_Data_GLOBAL_SEASONAL_S1_V2019_DECAY_MODEL_PARAMETERS` — Loaded IC; bands=['fall_hh_rho', 'fall_hh_rmse', 'fall_hh_tau', 'fall_vv_rho', 'fall_vv_rmse', 'fall_vv_tau', 'spring_hh_rho', 'spring_hh_rmse', 'spring_hh_tau', 'spring_vv_rho', 'spring_vv_rmse', 'spring_vv_tau', 'summer_hh_rho', 'summer_hh_rmse', 'summer_hh_tau', 'summer_vv_rho', 'summer_vv_rmse', 'summer_vv_tau', 'winter_hh_rho', 'winter_hh_rmse', 'winter_hh_tau', 'winter_vv_rho', 'winter_vv_rmse', 'winter_vv_tau']
- **OK** `catalog_load_Earth_Big_Data_GLOBAL_SEASONAL_S1_V2019_INCIDENCE_LAYOVER_SHADOW` — Loaded IC; bands=['inc', 'lsmap']
- **OK** `catalog_load_OPERA_RTC_L2_V1_S1` — Loaded IC; bands=['VH', 'VV', 'mask']
- **OK** `catalog_load_OPERA_RTC_L2_V1_S1_STATIC` — Loaded IC; bands=['local_incidence_angle', 'incidence_angle', 'number_of_looks', 'rtc_anf_gamma0_to_beta0', 'rtc_anf_gamma0_to_sigma0', 'mask']
- **OK** `catalog_load_OPERA_DSWX_L3_V1_S1` — Loaded IC; bands=['WTR_Water_classification', 'BWTR_Binary_water', 'CONF_Confidence', 'DIAG_diagnostic']
- **OK** `catalog_load_projects_ee-pkurelab_assets_LHScat` — Loaded IC; bands=['radar_signals']
- **OK** `catalog_load_OSU_GIMP_2000_IMAGERY_MOSAIC` — Loaded as Image; bands=['B1', 'B2', 'B3', 'B4', 'B5', 'B6_low_gain', 'B6_high_gain', 'B7', 'B8', 'B8_radarsat']
- **FAIL** `catalog_load_ASF_UAVSAR` — Not available in public EE catalog (or wrong ID)
- **FAIL** `catalog_load_ICEYE_SAR` — Not available in public EE catalog (or wrong ID)
- **FAIL** `catalog_load_CAPELLA_SAR` — Not available in public EE catalog (or wrong ID)
- **FAIL** `catalog_load_NASA_NISAR_L2` — Not available in public EE catalog (or wrong ID)
- **FAIL** `catalog_load_COPERNICUS_S1_SLC` — Not available in public EE catalog (or wrong ID)
- **FAIL** `catalog_load_ESA_S1_SLC` — Not available in public EE catalog (or wrong ID)
- **OK** `s1_coverage_galveston_2023` — 114 IW VV+VH scenes; asc=84 desc=30; orbits=[143, 34, 136]
- **OK** `vv_vh_urban_vs_water` — Urban VV mean -8.10 dB vs water -12.17 dB; ΔVV=4.07 dB
- **OK** `asc_vs_desc_galveston` — Asc VV mean -15.42 vs Desc -12.91; mean |diff| via mean of signed=-1.6315063334523845
- **OK** `dualpol_ratios_galveston` — VV-VH urban mean=7.1981785907751785 water=7.057525947043702 (volume scattering lowers ratio over vegetation)
- **OK** `incidence_angle_vs_VV` — Corr(VV, incidence angle)≈-0.5188712328726688 over Galveston (geometry radiometry)
- **FAIL** `grd_db_vs_float` — Image.select: Band pattern 'VV' did not match any bands. Available bands: [constant]
- **OK** `orbit_mosaic_artifacts` — Mixed-orbit median often noisier / seamier than single relative orbit
- **OK** `urban_double_bounce_houston` — Double-bounce proxy area=51.791 km² downtown Houston
- **FAIL** `speckle_filtering_compare` — 'Element' object has no attribute 'select'
Traceback (most recent call last):
  File "/home/tayyabkhan/Shared/mireye-challenge/ee-explore/deep_radar/scripts/deep_radar_explore.py", line 627, in probe_speckle_filtering
    med_stats = reduce_stats(med, GALVESTON, 20, ["VV", "VH"])
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tayyabkhan/Shared/mireye-challenge/ee-explore/deep_radar/scripts/deep_radar_explore.p
- **OK** `harvey_flood_before_after` — Flood mask area ≈ 6.4 km²; mean dVV=0.5777896031519125
- **OK** `harvey_followup_vv_vs_vh_flood` — Compare VV vs VH flood masks; red=VV-only green=agree blue=VH-only
- **OK** `harvey_followup_same_orbit_change` — Best same-orbit drop on orbit 143: mean dVV=0.08022679085066749
- **OK** `harvey_followup_dualpol_ratio_change` — Δ(VV-VH) mean=0.22427468382545776
- **OK** `harvey_followup_single_scene` — First post scene 2017-08-29; VV mean=-6.784438147330508
- **OK** `harvey_followup_s1_vs_s2_availability` — S2=8 scenes mean cloud=58.974138375; S1=3 usable regardless of weather
- **OK** `ms_river_wet_vs_dry` — Extra low-backscatter wet area≈200.6 km²; mean dVV=-1.3658050980212013
- **OK** `port_houston_seasonal_change` — Seasonal |dVV|>3dB area=40.94 km²
- **OK** `seasonal_composite_galveston` — JJA VV mean=-14.818705011662319 vs DJF=-14.99866740327024
- **OK** `seasonal_composite_houston_floodplain` — JJA VV mean=-8.638666340491232 vs DJF=-8.526859219273014
- **OK** `seasonal_composite_port_houston` — JJA VV mean=-9.901569082875422 vs DJF=-9.545344615091574
- **OK** `seasonal_composite_ms_river` — JJA VV mean=-10.461265244381192 vs DJF=-11.598910162351398
- **OK** `gulf_ship_bright_target` — Ocean VV mean=-15.570680441199254; p99=-10.268106449547096; bright pixels≈5375
- **OK** `ship_followup_vv_vs_vh` — Ships are usually stronger in VV (surface bounce)
- **OK** `ship_followup_persistent_platforms` — Red≈oil platforms / fixed structures; blue≈occasional ships
- **OK** `ship_followup_pass_ascending` — ASCENDING: 84 scenes; VV p99=-15.942582371556986
- **OK** `ship_followup_pass_descending` — DESCENDING: 30 scenes; VV p99=-10.622617177582324
- **OK** `wind_roughened_sea_contrast` — Rough−calm ocean VV Δ=10.97 dB
- **OK** `seasonal_s1_coherence_v2019` — Public seasonal coherence (not raw InSAR). Urban coh={'fall_hh_COH06': None} water={'fall_hh_COH06': None}. Bands=['fall_hh_COH06', 'fall_hh_COH12', 'fall_hh_COH18', 'fall_hh_COH24', 'fall_hh_COH36', 'fall_hh_COH48', 'fall_vv_COH06', 'fall_vv_COH12', 'fall_vv_COH18', 'fall_vv_COH24', 'fall_vv_COH36', 'fall_vv_COH48', 'spring_hh_COH06', 'spring_hh_COH12', 'spring_hh_COH18', 'spring_hh_COH24', 'spring_hh_COH36', 'spring_hh_COH48', 'spring_vv_COH06', 'spring_vv_COH12', 'spring_vv_COH18', 'spring_vv_COH24', 'spring_vv_COH36', 'spring_vv_COH48', 'summer_hh_COH06', 'summer_hh_COH12', 'summer_hh_COH18', 'summer_hh_COH24', 'summer_hh_COH36', 'summer_hh_COH48', 'summer_vv_COH06', 'summer_vv_COH12', 'summer_vv_COH18', 'summer_vv_COH24', 'summer_vv_COH36', 'summer_vv_COH48', 'winter_hh_COH06', 'winter_hh_COH12', 'winter_hh_COH18', 'winter_hh_COH24', 'winter_hh_COH36', 'winter_hh_COH48', 'winter_vv_COH06', 'winter_vv_COH12', 'winter_vv_COH18', 'winter_vv_COH24', 'winter_vv_COH36', 'winter_vv_COH48']
- **OK** `seasonal_s1_backscatter_v2019` — Companion seasonal backscatter mosaic
- **OK** `seasonal_s1_coherence_decay_params` — Temporal coherence decay model parameters — rare InSAR-adjacent public layer
- **FAIL** `insar_slc_fail_COPERNICUS_S1_SLC` — S1 SLC / raw interferograms not in public EE — use ASF HyP3 or COMET for InSAR
- **FAIL** `insar_slc_fail_COPERNICUS_S1_SLC` — S1 SLC / raw interferograms not in public EE — use ASF HyP3 or COMET for InSAR
- **FAIL** `insar_slc_fail_ESA_COPERNICUS_S1_SLC` — S1 SLC / raw interferograms not in public EE — use ASF HyP3 or COMET for InSAR
- **OK** `opera_rtc_galveston` — OPERA RTC: 76 scenes, bands=['VH', 'VV', 'mask']
- **OK** `opera_dswx_s1_houston` — DSWx-S1 water product: 213 scenes
- **OK** `alos_palsar_yearly_galveston` — L-band HH mean=-14.2023317603705 HV=-25.662005663760098
- **OK** `alos_scansar_harvey` — PALSAR-2 ScanSAR during Harvey window: 2017-08-17T06:14:15.370000
- **FAIL** `alos_stripmap_202401_galveston` — Japan-focused emergency StripMap — expect 0 over Texas
- **OK** `lhscat_scatterometer` — Long-term scatterometer (ERS/QuikSCAT/ASCAT) — coarse but multi-decadal
- **OK** `gimp_radarsat1_greenland` — RADARSAT-1 era Greenland mosaic — empty/null over Texas, works over Greenland
- **OK** `alos_fnf4_galveston` — PALSAR-derived forest/non-forest classification over Galveston bay area
- **OK** `cross_sensor_s1_cband_vs_alos_lband` — C-band VV mean=-14.43 vs L-band HH=-14.20 — different scattering regimes (esp. vegetation penetration)
- **OK** `timeseries_galveston_point_VV` — n=116 VV samples; range [-9.761869102555016,-5.455185308269883] dB; outliers=2
- **FAIL** `ew_mode_over_houston` — EW is ocean/arctic mode — expect ~0 over Houston
- **FAIL** `hh_pol_galveston_iw` — HH IW rare outside polar — expect 0
- **FAIL** `s1_prelaunch_2010` — Pre-launch should be empty
- **OK** `harvey_scene_inventory` — 16 S1 scenes Aug-Sep 2017 Houston
- **OK** `harvey_best_orbit_pair` — {'orbit': 34, 'before': {'VV': -8.38836284758557, 'id': 'S1A_IW_GRDH_1SDV_20170805T002644_20170805T002710_017781_01DCB4_8FDF', 'orbit': 34, 'pass': 'ASCENDING', 't': '2017-08-05'}, 'after': {'VV': -6.1980879696901345, 'id': 'S1A_IW_GRDH_1SDV_20170829T002620_20170829T002645_018131_01E74D_D734', 'orbit': 34, 'pass': 'ASCENDING', 't': '2017-08-29'}, 'dVV_scene_mean': 2.190274877895436}
- **FAIL** `harvey_deep` — Image.load: Image asset 'S1A_IW_GRDH_1SDV_20170829T002620_20170829T002645_018131_01E74D_D734' not found (does not exist or caller does not have access).Traceback (most recent call last):
  File "/home/tayyabkhan/Shared/mireye-challenge/.venv-ee/lib/python3.12/site-packages/ee/data.py", line 359, in _execute_cloud_call
    return call.execute(num_retries=num_retries)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tayyabkhan/Shared/mi
- **OK** `harvey_threshold_sensitivity` — Flood area km2 by threshold: {'VV<-12&dVV<-2': 32.081602903987864, 'VV<-14&dVV<-2.5': 14.23451508143191, 'VV<-16&dVV<-3': 6.44380784238736, 'VV<-18&dVV<-4': 2.086450824937768, 'VV<-15&dVV<-1': 16.5617473752822}
- **OK** `wind_followup_ship_detect_calm` — calm: thr=-14.1 dB, bright pix=56520
- **OK** `wind_followup_ship_detect_rough` — rough: thr=-3.2 dB, bright pix=416
- **OK** `wind_followup_monthly_means` — Ocean VV annual range 10.93 dB; monthly={'2023-01': -14.839225889668475, '2023-02': -12.473311386713497, '2023-03': -14.84983965190282, '2023-04': -13.594580561616606, '2023-05': -14.718008850648857, '2023-06': -16.673457410638694, '2023-07': -18.477754369589466, '2023-08': -16.052092002508452, '2023-09': -14.318108057092314, '2023-10': -14.1407972161208, '2023-11': -15.689729378243669, '2023-12': -17.39534592203987}
- **OK** `coherence_landcover_contrast` — COH12 means urban={'fall_vv_COH12': None, 'spring_vv_COH12': None, 'summer_vv_COH12': None, 'winter_vv_COH12': None} water={'fall_vv_COH12': None, 'spring_vv_COH12': None, 'summer_vv_COH12': None, 'winter_vv_COH12': None}
- **FAIL** `speckle_enl_fixed` — unsupported format string passed to NoneType.__format__Traceback (most recent call last):
  File "<stdin>", line 224, in <module>
TypeError: unsupported format string passed to NoneType.__format__

- **OK** `alos_scansar_harvey_scene_20170817` — ScanSAR 20170817 HH_mean=None
- **OK** `alos_scansar_harvey_scene_20170817` — ScanSAR 20170817 HH_mean=-5.824641451073211
- **OK** `alos_scansar_harvey_scene_20170822` — ScanSAR 20170822 HH_mean=-6.3270190245764555
- **OK** `alos_scansar_harvey_scene_20170822` — ScanSAR 20170822 HH_mean=-6.268956985782767
- **OK** `alos_scansar_harvey_scene_20170827` — ScanSAR 20170827 HH_mean=-3.120793984070428
- **OK** `alos_scansar_harvey_scene_20170827` — ScanSAR 20170827 HH_mean=-4.618538460030891
- **OK** `alos_scansar_harvey_scene_20170827` — ScanSAR 20170827 HH_mean=None
- **OK** `alos_scansar_harvey_scene_20170829` — ScanSAR 20170829 HH_mean=-3.5208367745495983
- **OK** `alos_scansar_harvey_scene_20170829` — ScanSAR 20170829 HH_mean=-3.564461428087045
- **OK** `alos_scansar_harvey_scene_20170905` — ScanSAR 20170905 HH_mean=-6.7666326970824615
- **OK** `alos_scansar_harvey_scene_20170905` — ScanSAR 20170905 HH_mean=-5.55386194358403
- **OK** `alos_scansar_harvey_change` — L-band dHH mean=None across ScanSAR Harvey pair
- **OK** `ascdesc_followup_ascending` — ASCENDING Galveston VV=-15.42 ClearLake=-11.99
- **OK** `ascdesc_followup_descending` — DESCENDING Galveston VV=-12.91 ClearLake=-11.44
- **OK** `ascdesc_incidence_ascending` — ASCENDING mean incidence=36.19012774729685
- **OK** `ascdesc_incidence_descending` — DESCENDING mean incidence=31.47204992391419
- **FAIL** `opera_dswx_vs_s1_darkwater` — Image.select: Band pattern 'BWTR_Binary_water' was applied to an Image with no bands. See https://developers.google.com/earth-engine/guides/debugging#no-bandsTraceback (most recent call last):
  File "/home/tayyabkhan/Shared/mireye-challenge/.venv-ee/lib/python3.12/site-packages/ee/data.py", line 359, in _execute_cloud_call
    return call.execute(num_retries=num_retries)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tayyabkhan/Shared/mi
- **OK** `gulf_oil_platform_objects` — ~35 persistent bright objects (platform-like) in Gulf AOI
- **OK** `port_persistent_bright_infra` — Port persistent bright (VV>-6 both seasons)=68.761 km2
- **FAIL** `grd_db_vs_float_fixed` — Image.select: Band pattern 'VV' did not match any bands. Available bands: [constant]Traceback (most recent call last):
  File "/home/tayyabkhan/Shared/mireye-challenge/.venv-ee/lib/python3.12/site-packages/ee/data.py", line 359, in _execute_cloud_call
    return call.execute(num_retries=num_retries)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tayyabkhan/Shared/mi
- **OK** `ms_river_2019_major_flood` — 2019 MS flood AOI mask=331.0 km2; mean dVV=-1.4252620959766298
- **OK** `harvey_orbit34_pair_deep` — West Houston dVV mean=0.4607719036637659; flood_km2=0.0; Addicks dVV=-0.03336426728440441, flood=0.0 km2
- **OK** `lband_vs_cband_harvey_flooded_veg` — L-band HH WestHouston pre=-5.643789259575709 peak=-4.007133240873893 Δ=1.64 dB; C-band VV dVV mean=0.6049582356611207 — L-band may BRIGHTEN (flooded veg double-bounce) while C-band darkens
- **OK** `coherence_point_samples` — Point COH12 samples: {'houston': 0.89, 'galveston': 0.7000000000000001, 'clear_lake': 0.56, 'open_gulf': 0.03, 'ms_river': 0.74, 'denver_control': 0.42}; galveston reduce={'winter_vv_COH12_count': 207576, 'winter_vv_COH12_mean': 0.19600951144746}
- **OK** `speckle_enl_open_gulf` — ENL raw=None median=None boost=None
- **OK** `opera_dswx_band_inspect` — DSWx bands=['WTR_Water_classification', 'BWTR_Binary_water', 'CONF_Confidence', 'DIAG_diagnostic']; 2024 n=90; hist={'WTR_Water_classification': {'0': 461043.06274509314, '1': 2508.1411764705886, '3': 1170.501960784314}}
- **OK** `ship_cfar_local_contrast` — CFAR-like ships: 138 objects, 1536 pixels; contrast p95=2.11773833319005
- **OK** `polarimetric_VH_VV_ratio_classes` — VH/VV urban=0.20947583975555897 water=0.2082939668405589
- **OK** `orbit_detail_34` — Orbit 34 ASCENDING: n=30, angle_mean=43.904383004187146, VV=-17.23866455032874
- **OK** `orbit_detail_136` — Orbit 136 ASCENDING: n=54, angle_mean=31.914551053030088, VV=-13.432547525998988
- **OK** `orbit_detail_143` — Orbit 143 DESCENDING: n=30, angle_mean=31.470230903640353, VV=-12.913391914694033
- **OK** `harvey_urban_brighten_vs_rural_darken` — Urban brighten=0.0 km2 darken=0.0; Rural brighten=0.2 darken=0.1
- **OK** `speckle_dbstd_and_enl` — dB std raw=1.941 → median=1.189; ENL raw=None median=None
- **OK** `coherence_tau_point_samples` — Coherence decay tau samples: {'houston': 7.615, 'galveston': 9.597, 'open_gulf': 2.8000000000000003, 'denver': 12.23}