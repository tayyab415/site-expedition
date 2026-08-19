#!/usr/bin/env python3
"""Deep weird EE exploration — obscure catalog, ML, exports, limits."""
from __future__ import annotations

import json
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

PROJECT = "gen-lang-client-0261050164"
OUT = Path(__file__).resolve().parent
THUMBS = OUT / "thumbs"
THUMBS.mkdir(parents=True, exist_ok=True)

print("Initializing EE...", flush=True)
ee.Initialize(project=PROJECT)
print("EE ready", flush=True)

TX_PERMIAN = ee.Geometry.Rectangle([-104.5, 31.0, -101.5, 33.5])
HOUSTON = ee.Geometry.Point([-95.3698, 29.7604]).buffer(20000).bounds()
IOWA = ee.Geometry.Rectangle([-94.0, 41.5, -93.0, 42.2])
NAIP_PT = ee.Geometry.Point([-95.4, 29.75])
AFRICA_LAGOS = ee.Geometry.Point([3.3792, 6.5244]).buffer(3000).bounds()
CA_CENTRAL = ee.Geometry.Rectangle([-120.5, 35.5, -119.5, 36.5])

results: list[dict] = []


def checkpoint():
    (OUT / "deep_weird_results.partial.json").write_text(
        json.dumps(
            {
                "n": len(results),
                "n_ok": sum(1 for r in results if r["ok"]),
                "results": results,
            },
            indent=2,
            default=str,
        )
    )


def log(name, category, ok, detail=None, thumb=None, note="", err=""):
    rec = {
        "name": name,
        "category": category,
        "ok": ok,
        "detail": detail,
        "thumb": str(thumb) if thumb else None,
        "note": note,
        "error": (err or "")[:900] or None,
    }
    results.append(rec)
    status = "OK" if ok else "FAIL"
    msg = f"[{status}] {category}/{name}"
    if err:
        msg += f" — {err[:140]}"
    elif note:
        msg += f" — {note[:80]}"
    print(msg, flush=True)
    checkpoint()


def save_thumb(img, path: Path, region, dims=384):
    try:
        url = img.getThumbURL({"region": region, "dimensions": dims, "format": "png"})
        urllib.request.urlretrieve(url, path)
        return path
    except Exception as e:
        print(f"  thumb fail {path.name}: {e}", flush=True)
        return None


# ---------------------------------------------------------------------------
# 1. Catalog loads (lightweight — no heavy composites)
# ---------------------------------------------------------------------------
CATALOG = [
    ("methane_s5p_ch4", "IC", "COPERNICUS/S5P/OFFL/L3_CH4"),
    ("no2_s5p_offl", "IC", "COPERNICUS/S5P/OFFL/L3_NO2"),
    ("no2_tempo", "IC", "NASA/TEMPO/NO2_L3"),
    ("viirs_ntl_monthly", "IC", "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"),
    ("viirs_ntl_annual", "IC", "NOAA/VIIRS/DNB/ANNUAL_V21"),
    ("dmsp_nightlights", "IC", "NOAA/DMSP-OLS/NIGHTTIME_LIGHTS"),
    ("gpw_pop_density", "IC", "CIESIN/GPWv411/GPW_Population_Density"),
    ("ghsl_pop", "IC", "JRC/GHSL/P2023A/GHS_POP"),
    ("landscan_global", "IC", "projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL"),
    ("open_buildings_v3", "FC", "GOOGLE/Research/open-buildings/v3/polygons"),
    ("open_buildings_temporal", "IC", "GOOGLE/Research/open-buildings-temporal/v1"),
    ("emit_ch4_plume", "IC", "NASA/EMIT/L2B/CH4PLM"),
    ("emit_ch4_enh", "IC", "NASA/EMIT/L2B/CH4ENH"),
    ("emit_reflectance", "IC", "NASA/EMIT/L2A/RFL"),
    ("soil_grtgroup", "IMG", "OpenLandMap/SOL/SOL_GRTGROUP_USDA-SOILTAX_C/v01"),
    ("soil_texture", "IMG", "OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02"),
    ("soil_ph", "IMG", "OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02"),
    ("gap_wildlife_habitat", "IMG", "USGS/GAP/CONUS/2011"),
    ("padus_protected", "FC", "USGS/GAP/PAD-US/v20/designation"),
    ("wdpa_protected", "FC", "WCMC/WDPA/current/polygons"),
    ("tiger_roads_2016", "FC", "TIGER/2016/Roads"),
    ("grace_land_v04", "IC", "NASA/GRACE/MASS_GRIDS_V04/LAND"),
    ("grace_mascon", "IC", "NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI"),
    ("lithology_ergo", "IMG", "CSP/ERGo/1_0/US/lithology"),
    ("topo_diversity", "IMG", "CSP/ERGo/1_0/Global/ALOS_topoDiversity"),
    ("human_modification", "IC", "CSP/HM/GlobalHumanModification"),
    ("gaia_impervious_change", "IMG", "Tsinghua/FROM-GLC/GAIA/v10"),
    ("ghsl_built_height", "IC", "JRC/GHSL/P2023A/GHS_BUILT_H"),
    ("hydroatlas_l6", "FC", "WWF/HydroATLAS/v1/Basins/level06"),
    ("freeflowing_rivers", "FC", "WWF/HydroSHEDS/v1/FreeFlowingRivers"),
    ("s5p_co", "IC", "COPERNICUS/S5P/OFFL/L3_CO"),
    ("s5p_so2", "IC", "COPERNICUS/S5P/OFFL/L3_SO2"),
    ("isda_soil_ph_africa", "IMG", "ISDASOIL/Africa/v1/ph"),
    ("uspvdb_guess", "FC", "USGS/USPVDB/v1"),
    ("covid_mobility_guess", "IC", "GOOGLE/COVID19/Mobility"),
    ("landslide_inventory_guess", "FC", "USGS/LANDSLIDES/v1"),
    ("earthquake_comcat_guess", "FC", "USGS/ANSS_ComCat"),
    ("methanesat_preview_guess", "IC", "projects/edf-methanesat-ee/assets/publicPreview/L3concentration"),
    ("traffic_guess", "IC", "GOOGLE/Traffic/v1"),
]


def probe_catalog_loads():
    print("=== catalog loads ===", flush=True)
    for name, kind, asset_id in CATALOG:
        t0 = time.time()
        try:
            detail = {"asset_id": asset_id, "kind": kind}
            if kind == "IC":
                col = ee.ImageCollection(asset_id)
                # first() can be slow on huge collections — use limit(1).first()
                img = col.limit(1).first()
                bands = img.bandNames().getInfo()
                detail["bands"] = bands[:20]
                detail["n_bands"] = len(bands)
            elif kind == "IMG":
                img = ee.Image(asset_id)
                bands = img.bandNames().getInfo()
                detail["bands"] = bands[:20]
            else:
                fc = ee.FeatureCollection(asset_id)
                # limit(1) propertyNames — proves asset exists
                props = fc.limit(1).first().propertyNames().getInfo()
                detail["props"] = props[:15]
            detail["elapsed_s"] = round(time.time() - t0, 2)
            log(name, "catalog", True, detail, note="load OK")
        except Exception as e:
            log(name, "catalog", False, {"asset_id": asset_id, "elapsed_s": round(time.time() - t0, 2)}, err=f"{type(e).__name__}: {e}")


def probe_catalog_thumbs_and_stats():
    """Heavier but selective: one image / short date window per theme."""
    print("=== catalog thumbs/stats ===", flush=True)
    probes = [
        (
            "thumb_s5p_ch4_permian",
            lambda: ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4")
            .filterBounds(TX_PERMIAN)
            .filterDate("2023-07-01", "2023-07-15")
            .select("CH4_column_volume_mixing_ratio_dry_air_bias_corrected")
            .mean(),
            TX_PERMIAN,
            {"min": 1750, "max": 1900, "palette": ["black", "blue", "cyan", "green", "yellow", "red"]},
            10000,
        ),
        (
            "thumb_s5p_no2_houston",
            lambda: ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
            .filterBounds(HOUSTON)
            .filterDate("2023-07-01", "2023-07-10")
            .select("tropospheric_NO2_column_number_density")
            .mean(),
            HOUSTON,
            {"min": 0, "max": 0.00015, "palette": ["black", "blue", "purple", "cyan", "yellow", "red"]},
            5000,
        ),
        (
            "thumb_viirs_ntl_houston",
            lambda: ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
            .filterDate("2023-01-01", "2023-12-31")
            .select("avg_rad")
            .mean(),
            HOUSTON,
            {"min": 0, "max": 60, "palette": ["000000", "FFFF00", "FFFFFF"]},
            500,
        ),
        (
            "thumb_viirs_ntl_change",
            lambda: (
                ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V21")
                .filterDate("2021-01-01", "2022-01-01")
                .first()
                .select("average")
                .subtract(
                    ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V21")
                    .filterDate("2014-01-01", "2015-01-01")
                    .first()
                    .select("average")
                )
            ),
            HOUSTON,
            {"min": -20, "max": 20, "palette": ["0000ff", "ffffff", "ff0000"]},
            500,
        ),
        (
            "thumb_gpw_pop",
            lambda: ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density")
            .sort("system:time_start", False)
            .first()
            .select("population_density"),
            HOUSTON,
            {"min": 0, "max": 2000, "palette": ["000004", "781c6d", "ed6925", "fcffa4"]},
            1000,
        ),
        (
            "thumb_emit_plume_permian",
            lambda: ee.ImageCollection("NASA/EMIT/L2B/CH4PLM")
            .filterBounds(TX_PERMIAN)
            .select("methane_plume_complex")
            .max(),
            TX_PERMIAN,
            {"min": 0, "max": 800, "palette": ["000000", "440154", "31688e", "35b779", "fde725"]},
            200,
        ),
        (
            "thumb_soil_ph_iowa",
            lambda: ee.Image("OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02").select("b0"),
            IOWA,
            {"min": 40, "max": 80, "palette": ["ff0000", "ffff00", "00ff00", "0000ff"]},
            500,
        ),
        (
            "thumb_gap_habitat",
            lambda: ee.Image("USGS/GAP/CONUS/2011").select("landcover"),
            HOUSTON,
            {"min": 1, "max": 500, "palette": ["aec3d4", "152106", "225129", "369b47", "30eb5b", "c3aa69"]},
            100,
        ),
        (
            "thumb_lithology",
            lambda: ee.Image("CSP/ERGo/1_0/US/lithology").select("b1"),
            HOUSTON,
            {"min": 1, "max": 15, "palette": ["000000", "a6cee3", "1f78b4", "b2df8a", "33a02c", "fb9a99", "e31a1c"]},
            200,
        ),
        (
            "thumb_open_buildings_temporal",
            lambda: ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1")
            .filterBounds(AFRICA_LAGOS)
            .filterDate("2023-01-01", "2024-01-01")
            .first()
            .select("building_height"),
            AFRICA_LAGOS,
            {"min": 0, "max": 20, "palette": ["000000", "ffffcc", "fd8d3c", "e31a1c"]},
            10,
        ),
        (
            "thumb_grace_mascon",
            lambda: ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI")
            .filterDate("2022-01-01", "2023-01-01")
            .select("lwe_thickness")
            .mean(),
            ee.Geometry.Rectangle([-106, 25, -93, 37]),
            {"min": -30, "max": 30, "palette": ["0000ff", "ffffff", "ff0000"]},
            25000,
        ),
    ]
    for name, builder, region, vis, scale in probes:
        try:
            img = builder().clip(region)
            stats = img.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), "", True), region, scale, maxPixels=5e6, bestEffort=True).getInfo()
            thumb = save_thumb(img.visualize(**vis), THUMBS / f"{name}.png", region)
            log(name, "catalog_viz", True, {"stats": stats, "scale": scale}, thumb)
        except Exception as e:
            log(name, "catalog_viz", False, err=str(e))


# ---------------------------------------------------------------------------
# 2. Platform APIs / ML / export
# ---------------------------------------------------------------------------
def probe_platform():
    print("=== platform APIs ===", flush=True)

    try:
        img = ee.Image("USGS/SRTMGL1_003").clip(HOUSTON)
        url = img.getDownloadURL({"scale": 90, "region": HOUSTON, "format": "GEO_TIFF"})
        log("getDownloadURL_srtm", "platform_api", True, {"url_prefix": url[:140], "url_len": len(url)})
    except Exception as e:
        log("getDownloadURL_srtm", "platform_api", False, err=str(e))

    try:
        img = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(HOUSTON)
            .filterDate("2023-06-01", "2023-07-01")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .median()
        )
        url = img.visualize(bands=["B4", "B3", "B2"], min=0, max=3000).getThumbURL({"region": HOUSTON, "dimensions": 256})
        path = THUMBS / "thumb_s2_houston.png"
        urllib.request.urlretrieve(url, path)
        log("getThumbURL_s2", "platform_api", True, {"url_prefix": url[:100]}, path)
    except Exception as e:
        log("getThumbURL_s2", "platform_api", False, err=str(e))

    try:
        roads = ee.FeatureCollection("TIGER/2016/Roads").filterBounds(HOUSTON).limit(30)
        elev = ee.Image("USGS/SRTMGL1_003")
        out = elev.reduceRegions(roads, ee.Reducer.mean(), 30)
        sample = out.limit(5).getInfo()
        vals = [f["properties"].get("mean") for f in sample["features"]]
        log("reduceRegions_roads_elev", "platform_api", True, {"means_sample": vals})
    except Exception as e:
        log("reduceRegions_roads_elev", "platform_api", False, err=str(e))

    try:
        water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").gt(50)
        dist = water.fastDistanceTransform(500).sqrt().multiply(ee.Image.pixelArea().sqrt()).rename("dist_m")
        stats = dist.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.max(), "", True), HOUSTON, 90, maxPixels=5e7, bestEffort=True).getInfo()
        thumb = save_thumb(
            dist.clip(HOUSTON).visualize(min=0, max=5000, palette=["0000ff", "00ffff", "ffff00", "ff0000"]),
            THUMBS / "distance_transform_houston.png",
            HOUSTON,
        )
        log("fastDistanceTransform", "platform_api", True, stats, thumb)
    except Exception as e:
        log("fastDistanceTransform", "platform_api", False, err=str(e))

    try:
        cost = ee.Image(1)
        sources = ee.Image().paint(ee.FeatureCollection([ee.Feature(ee.Geometry.Point([-95.37, 29.76]))]), 1)
        cum = cost.cumulativeCost(sources, 8000)
        stats = cum.reduceRegion(ee.Reducer.max(), HOUSTON, 120, maxPixels=5e7, bestEffort=True).getInfo()
        thumb = save_thumb(
            cum.clip(HOUSTON).visualize(min=0, max=8000, palette=["000000", "00ff00", "ffff00", "ff0000"]),
            THUMBS / "cumulative_cost_houston.png",
            HOUSTON,
        )
        log("cumulativeCost", "platform_api", True, stats, thumb)
    except Exception as e:
        log("cumulativeCost", "platform_api", False, err=str(e))

    # kriging
    has_k = hasattr(ee.Image, "kriging")
    log(
        "kriging",
        "platform_api",
        False if not has_k else True,
        {"hasattr_Image_kriging": has_k, "ee_attrs_with_rig": [a for a in dir(ee) if "rig" in a.lower()]},
        err=("ee.Image.kriging does not exist" if not has_k else ""),
    )

    # Classifiers
    print("  classifiers...", flush=True)
    try:
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(IOWA)
            .filterDate("2023-07-01", "2023-08-01")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .median()
            .select(["B2", "B3", "B4", "B8", "B11", "B12"])
            .clip(IOWA)
        )
        lc = ee.Image("ESA/WorldCover/v200").select("Map").clip(IOWA)
        class_values = [10, 20, 30, 40, 50, 60, 80, 90]
        lc_r = lc.remap(class_values, list(range(len(class_values)))).rename("lc").toByte()
        sample = s2.addBands(lc_r).stratifiedSample(numPoints=30, classBand="lc", region=IOWA, scale=40, seed=7)
        with_rand = sample.randomColumn("r", 7)
        training = with_rand.filter("r < 0.7")
        validation = with_rand.filter("r >= 0.7")
        bands = ["B2", "B3", "B4", "B8", "B11", "B12"]
        clf_results = {}
        for cname, clf in [
            ("smileRandomForest", ee.Classifier.smileRandomForest(12)),
            ("smileNaiveBayes", ee.Classifier.smileNaiveBayes()),
            ("libsvm", ee.Classifier.libsvm()),
        ]:
            print(f"    {cname}", flush=True)
            trained = clf.train(training, "lc", bands)
            cm = trained.confusionMatrix()
            matrix = cm.getInfo()
            validated = validation.classify(trained)
            em = validated.errorMatrix("lc", "classification")
            clf_results[cname] = {
                "train_accuracy": cm.accuracy().getInfo(),
                "val_accuracy": em.accuracy().getInfo(),
                "kappa": em.kappa().getInfo(),
                "matrix_shape": [len(matrix), len(matrix[0]) if matrix else 0],
            }
        rf = ee.Classifier.smileRandomForest(12).train(training, "lc", bands)
        thumb = save_thumb(
            s2.classify(rf).visualize(
                min=0, max=7, palette=["006400", "ffbb22", "ffff4c", "f096ff", "fa0000", "b4b4b4", "0064c8", "0096a0"]
            ),
            THUMBS / "rf_classified_iowa.png",
            IOWA,
        )
        log("classifiers_rf_nb_svm", "ml", True, clf_results, thumb)
    except Exception as e:
        log("classifiers_rf_nb_svm", "ml", False, err=f"{e}\n{traceback.format_exc()[-350:]}")

    # Clusterer
    print("  clusterer...", flush=True)
    try:
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(IOWA)
            .filterDate("2023-07-01", "2023-07-20")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
            .median()
            .select(["B2", "B3", "B4", "B8"])
            .clip(IOWA)
        )
        training = s2.sample(region=IOWA, scale=40, numPixels=1200, seed=1)
        clusterer = ee.Clusterer.wekaKMeans(5).train(training)
        result = s2.cluster(clusterer)
        hist = result.reduceRegion(ee.Reducer.frequencyHistogram(), IOWA, 80, maxPixels=2e7, bestEffort=True).getInfo()
        thumb = save_thumb(result.randomVisualizer(), THUMBS / "kmeans_s2_iowa.png", IOWA)
        log("clusterer_wekaKMeans_s2", "ml", True, {"histogram": hist, "clusterers": [a for a in dir(ee.Clusterer) if a.startswith("weka")]}, thumb)
    except Exception as e:
        log("clusterer_wekaKMeans_s2", "ml", False, err=str(e))

    # Export table GCS — expect fail
    try:
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([-95.37, 29.76]), {"x": 1})])
        task = ee.batch.Export.table.toCloudStorage(
            collection=fc,
            description="deep_weird_table_probe",
            bucket="mireye-ee-probe-nonexistent-bucket-xyz",
            fileNamePrefix="deep_weird/probe",
            fileFormat="CSV",
        )
        task.start()
        time.sleep(3)
        status = task.status()
        log(
            "export_table_gcs",
            "export",
            False,
            {"task_id": task.id, "status": status},
            err=f"expect fail: state={status.get('state')} error={status.get('error_message')}",
        )
    except Exception as e:
        log("export_table_gcs", "export", False, err=f"{type(e).__name__}: {e}")

    # Export image + task list
    try:
        region = ee.Geometry.Point([-95.37, 29.76]).buffer(400).bounds()
        task = ee.batch.Export.image.toDrive(
            image=ee.Image(1).clip(region),
            description="deep_weird_image_probe",
            folder="ee_deep_weird",
            fileNamePrefix="probe_constant",
            region=region,
            scale=30,
            maxPixels=1e6,
        )
        task.start()
        time.sleep(2)
        status = task.status()
        tasks = ee.data.getTaskList()[:10]
        slim = [
            {"id": t.get("id"), "state": t.get("state"), "description": t.get("description"), "error_message": t.get("error_message")}
            for t in tasks
        ]
        log("export_image_drive_tasklist", "export", True, {"started_task": status, "recent_tasks": slim})
    except Exception as e:
        log("export_image_drive_tasklist", "export", False, err=str(e))


# ---------------------------------------------------------------------------
# 3. Geometry
# ---------------------------------------------------------------------------
def probe_geometry():
    print("=== geometry ===", flush=True)
    try:
        grid = HOUSTON.coveringGrid("EPSG:4326", 0.05)
        log("coveringGrid_houston", "geometry", True, {"n_cells": grid.size().getInfo()})
    except Exception as e:
        log("coveringGrid_houston", "geometry", False, err=str(e))

    try:
        n_b = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(AFRICA_LAGOS).limit(200).size().getInfo()
        basins = ee.FeatureCollection("WWF/HydroATLAS/v1/Basins/level06").filterBounds(HOUSTON)
        pad = ee.FeatureCollection("USGS/GAP/PAD-US/v20/designation").filterBounds(HOUSTON).limit(40)
        pad_geom = pad.geometry()
        joined = basins.filterBounds(pad_geom).limit(8)

        def intersect_pad(f):
            g = f.geometry().intersection(pad_geom, 100)
            return f.set({"intersect_area": g.area(100), "basin_area": f.geometry().area(100)})

        info = joined.map(intersect_pad).getInfo()
        areas = [
            {"intersect_area": f["properties"].get("intersect_area"), "basin_area": f["properties"].get("basin_area")}
            for f in info["features"]
        ]
        log(
            "spatial_join_basins_padus",
            "geometry",
            True,
            {
                "open_buildings_lagos_limit200": n_b,
                "basins": basins.limit(50).size().getInfo(),
                "pad_limit40": pad.size().getInfo(),
                "sample_intersects": areas,
            },
        )
    except Exception as e:
        log("spatial_join_basins_padus", "geometry", False, err=str(e))

    try:
        big = ee.Geometry.Rectangle([-96.2, 29.3, -94.8, 30.2])
        n = ee.FeatureCollection("TIGER/2016/Roads").filterBounds(big).limit(5000).size().getInfo()
        log("intersect_large_fc_roads", "geometry", True, {"limit_5000_size": n})
    except Exception as e:
        log("intersect_large_fc_roads", "geometry", False, err=str(e))


# ---------------------------------------------------------------------------
# 4. Unmix / arrays
# ---------------------------------------------------------------------------
def probe_unmix():
    print("=== unmix/array ===", flush=True)
    try:
        l8 = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(CA_CENTRAL)
            .filterDate("2023-06-01", "2023-08-01")
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .median()
            .select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"])
            .multiply(0.0000275)
            .add(-0.2)
            .clip(CA_CENTRAL)
        )
        veg = [0.05, 0.09, 0.06, 0.45, 0.25, 0.12]
        soil = [0.15, 0.20, 0.25, 0.35, 0.40, 0.35]
        water = [0.04, 0.05, 0.03, 0.02, 0.01, 0.01]
        unmixed = l8.unmix([veg, soil, water], True, True).rename(["veg", "soil", "water"])
        stats = unmixed.reduceRegion(ee.Reducer.mean(), CA_CENTRAL, 120, maxPixels=5e7, bestEffort=True).getInfo()
        thumb = save_thumb(unmixed.visualize(bands=["veg", "soil", "water"], min=0, max=1), THUMBS / "unmix_ca_central.png", CA_CENTRAL)
        log("image_unmix_landsat", "array_unmix", True, {"mean_fractions": stats}, thumb)
    except Exception as e:
        log("image_unmix_landsat", "array_unmix", False, err=str(e))

    try:
        emit = ee.ImageCollection("NASA/EMIT/L2A/RFL").filterBounds(TX_PERMIAN).limit(1).first()
        bands = emit.bandNames().getInfo()
        subset = [b for i, b in enumerate(bands) if str(b).startswith("reflectance_") and i % 25 == 0][:24]
        arr = emit.select(subset).toArray()
        lengths = arr.arrayLength(0).reduceRegion(ee.Reducer.mean(), TX_PERMIAN, 400, maxPixels=5e6, bestEffort=True).getInfo()
        log(
            "emit_toArray_hyperspectral",
            "array_unmix",
            True,
            {"n_subset_bands": len(subset), "array_length_mean": lengths, "total_bands": len(bands)},
        )
    except Exception as e:
        log("emit_toArray_hyperspectral", "array_unmix", False, err=str(e))


# ---------------------------------------------------------------------------
# 5. listImages keyword themes
# ---------------------------------------------------------------------------
def probe_list_images():
    print("=== listImages ===", flush=True)
    mapping = {
        "methane": "COPERNICUS/S5P/OFFL/L3_CH4",
        "tropomi": "COPERNICUS/S5P/OFFL/L3_NO2",
        "landslide_proxy_emit": "NASA/EMIT/L2B/CH4PLM",
        "building": "GOOGLE/Research/open-buildings-temporal/v1",
        "solar_proxy_viirs": "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
        "traffic_proxy_ntl": "NOAA/VIIRS/DNB/ANNUAL_V21",
    }
    for kw, cid in mapping.items():
        try:
            resp = ee.data.listImages({"parent": cid, "pageSize": 4})
            images = resp.get("images") or []
            log(f"listImages_{kw}", "catalog_search", True, {"parent": cid, "n": len(images), "ids": [i.get("id") for i in images]})
        except Exception as e:
            log(f"listImages_{kw}", "catalog_search", False, {"parent": cid}, err=str(e))
    try:
        resp = ee.data.getList({"id": "NASA/EMIT/L2B/CH4PLM"})
        log("getList_emit_ch4plm", "catalog_search", True, {"n": len(resp) if resp else 0, "sample": (resp or [])[:3]})
    except Exception as e:
        log("getList_emit_ch4plm", "catalog_search", False, err=str(e))


# ---------------------------------------------------------------------------
# 6. Stress / limits
# ---------------------------------------------------------------------------
def probe_stress():
    print("=== stress ===", flush=True)
    dem = ee.Image("USGS/SRTMGL1_003")
    cases = [
        ("reduce_conus_scale1", ee.Geometry.Rectangle([-125, 24, -66, 50]), 1, None),
        ("reduce_texas_scale10", ee.Geometry.Rectangle([-106, 25, -93, 36]), 10, None),
        ("reduce_houston_scale1", HOUSTON, 1, None),
        ("reduce_houston_scale30_ok", HOUSTON, 30, None),
        ("reduce_houston_scale1_maxPixels1e9", HOUSTON, 1, 1e9),
        ("reduce_texas_bestEffort", ee.Geometry.Rectangle([-106, 25, -93, 36]), 10, "bestEffort"),
    ]
    for name, region, scale, mp in cases:
        try:
            kwargs = {}
            if mp == "bestEffort":
                kwargs["bestEffort"] = True
            elif mp is not None:
                kwargs["maxPixels"] = mp
            v = dem.reduceRegion(ee.Reducer.mean(), region, scale, **kwargs).getInfo()
            log(name, "stress", True, {"scale": scale, "mean": v, "kwargs": kwargs})
        except Exception as e:
            log(name, "stress", False, {"scale": scale, "kwargs": mp}, err=str(e))


# ---------------------------------------------------------------------------
# 7. Sharpness NAIP vs S2 vs Landsat
# ---------------------------------------------------------------------------
def probe_sharpness():
    print("=== sharpness ===", flush=True)
    try:
        region = NAIP_PT.buffer(600).bounds()
        naip = (
            ee.ImageCollection("USDA/NAIP/DOQQ")
            .filterBounds(region)
            .filterDate("2022-01-01", "2023-12-31")
            .mosaic()
            .select(["R", "G", "B"])
            .clip(region)
        )
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate("2022-06-01", "2022-09-01")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
            .median()
            .select(["B4", "B3", "B2"])
            .clip(region)
        )
        l8 = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(region)
            .filterDate("2022-06-01", "2022-09-01")
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .median()
            .select(["SR_B4", "SR_B3", "SR_B2"])
            .multiply(0.0000275)
            .add(-0.2)
            .clip(region)
        )

        def edge_energy(img, scale, bands):
            gray = img.select(bands).reduce(ee.Reducer.mean())
            grad = gray.gradient()
            mag = grad.select("x").pow(2).add(grad.select("y").pow(2)).sqrt().rename("edge")
            return mag.reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.stdDev(), "", True).combine(ee.Reducer.percentile([90, 99]), "", True),
                region,
                scale,
                maxPixels=5e7,
                bestEffort=True,
            ).getInfo()

        metrics = {
            "NAIP_1m": edge_energy(naip, 1, ["R", "G", "B"]),
            "S2_10m": edge_energy(s2, 10, ["B4", "B3", "B2"]),
            "Landsat_30m": edge_energy(l8, 30, ["SR_B4", "SR_B3", "SR_B2"]),
        }
        t1 = save_thumb(naip.visualize(bands=["R", "G", "B"], min=0, max=200), THUMBS / "sharp_naip.png", region)
        t2 = save_thumb(s2.visualize(bands=["B4", "B3", "B2"], min=0, max=3000), THUMBS / "sharp_s2.png", region)
        t3 = save_thumb(l8.visualize(bands=["SR_B4", "SR_B3", "SR_B2"], min=0, max=0.3), THUMBS / "sharp_landsat.png", region)
        log("sharpness_naip_s2_landsat", "sharpness", True, metrics, t1, f"thumbs={t1},{t2},{t3}")
    except Exception as e:
        log("sharpness_naip_s2_landsat", "sharpness", False, err=f"{e}\n{traceback.format_exc()[-350:]}")


# ---------------------------------------------------------------------------
# 8. Deep dive EMIT methane
# ---------------------------------------------------------------------------
def deep_dive_emit():
    print("=== deep dive EMIT ===", flush=True)
    col = ee.ImageCollection("NASA/EMIT/L2B/CH4PLM")
    followups = []

    def add(f, ok, **kw):
        followups.append({"f": f, "ok": ok, **kw})
        print(f"  followup {f}: {'OK' if ok else 'FAIL'}", flush=True)

    try:
        n = col.limit(5000).size().getInfo()
        d0 = ee.Date(col.aggregate_min("system:time_start")).format().getInfo()
        d1 = ee.Date(col.aggregate_max("system:time_start")).format().getInfo()
        add("count_and_span", True, n_images_limit5000=n, start=d0, end=d1)
    except Exception as e:
        add("count_and_span", False, err=str(e))

    try:
        perm = col.filterBounds(TX_PERMIAN)
        n = perm.limit(2000).size().getInfo()
        mx = perm.select("methane_plume_complex").max()
        stats = mx.reduceRegion(
            ee.Reducer.max().combine(ee.Reducer.mean(), "", True).combine(ee.Reducer.count(), "", True),
            TX_PERMIAN,
            200,
            maxPixels=5e7,
            bestEffort=True,
        ).getInfo()
        thumb = save_thumb(
            mx.clip(TX_PERMIAN).visualize(min=0, max=1000, palette=["000000", "440154", "31688e", "35b779", "fde725"]),
            THUMBS / "emit_permian_max.png",
            TX_PERMIAN,
        )
        add("permian_plume_max", True, n_scenes_limit2000=n, stats=stats, thumb=str(thumb))
    except Exception as e:
        add("permian_plume_max", False, err=str(e))

    try:
        enh = ee.ImageCollection("NASA/EMIT/L2B/CH4ENH").filterBounds(TX_PERMIAN)
        n = enh.limit(2000).size().getInfo()
        mean = enh.select("vertical_column_enhancement").mean()
        stats = mean.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.max(), "", True), TX_PERMIAN, 500, maxPixels=5e7, bestEffort=True).getInfo()
        thumb = save_thumb(
            mean.clip(TX_PERMIAN).visualize(min=0, max=200, palette=["0d0887", "7e03a8", "cc4778", "f89540", "f0f921"]),
            THUMBS / "emit_enh_permian.png",
            TX_PERMIAN,
        )
        add("ch4enh_colocated", True, n=n, stats=stats, thumb=str(thumb))
    except Exception as e:
        add("ch4enh_colocated", False, err=str(e))

    try:
        plume = col.filterBounds(TX_PERMIAN).select("methane_plume_complex").max().gt(100)
        pop = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density").sort("system:time_start", False).first()
        stats = pop.updateMask(plume).reduceRegion(
            ee.Reducer.mean().combine(ee.Reducer.sum(), "", True), TX_PERMIAN, 1000, maxPixels=5e7, bestEffort=True
        ).getInfo()
        add("plume_vs_population", True, stats=stats)
    except Exception as e:
        add("plume_vs_population", False, err=str(e))

    try:
        plume = col.filterBounds(TX_PERMIAN).select("methane_plume_complex").max().gt(100)
        ntl = (
            ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
            .filterDate("2023-01-01", "2023-12-31")
            .select("avg_rad")
            .mean()
        )
        s_under = ntl.updateMask(plume).reduceRegion(ee.Reducer.mean(), TX_PERMIAN, 500, maxPixels=5e7, bestEffort=True).getInfo()
        s_out = ntl.updateMask(plume.Not()).reduceRegion(ee.Reducer.mean(), TX_PERMIAN, 500, maxPixels=5e7, bestEffort=True).getInfo()
        add("plume_vs_viirs_ntl", True, ntl_under_plume=s_under, ntl_outside=s_out)
    except Exception as e:
        add("plume_vs_viirs_ntl", False, err=str(e))

    try:
        resp = ee.data.listImages({"parent": "NASA/EMIT/L2B/CH4PLM", "pageSize": 5})
        imgs = resp.get("images") or []
        sample_id = imgs[0]["id"] if imgs else None
        props = ee.Image(sample_id).toDictionary().getInfo() if sample_id else {}
        add("listImages_and_props", True, ids=[i.get("id") for i in imgs], sample_props={k: props[k] for k in list(props)[:20]})
    except Exception as e:
        add("listImages_and_props", False, err=str(e))

    # F7 bonus: S5P CH4 mean under EMIT plume mask
    try:
        plume = col.filterBounds(TX_PERMIAN).select("methane_plume_complex").max().gt(100)
        s5 = (
            ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4")
            .filterBounds(TX_PERMIAN)
            .filterDate("2023-06-01", "2023-08-01")
            .select("CH4_column_volume_mixing_ratio_dry_air_bias_corrected")
            .mean()
        )
        under = s5.updateMask(plume).reduceRegion(ee.Reducer.mean(), TX_PERMIAN, 5000, maxPixels=5e6, bestEffort=True).getInfo()
        outside = s5.updateMask(plume.Not()).reduceRegion(ee.Reducer.mean(), TX_PERMIAN, 5000, maxPixels=5e6, bestEffort=True).getInfo()
        add("plume_vs_s5p_ch4", True, s5p_under=under, s5p_outside=outside)
    except Exception as e:
        add("plume_vs_s5p_ch4", False, err=str(e))

    ok_n = sum(1 for f in followups if f.get("ok"))
    log("deep_dive_emit_methane", "deep_dive", ok_n >= 5, {"followups": followups, "n_ok": ok_n}, note="EMIT CH4PLM deep dive")


def main():
    probe_catalog_loads()
    probe_catalog_thumbs_and_stats()
    probe_platform()
    probe_geometry()
    probe_unmix()
    probe_list_images()
    probe_stress()
    probe_sharpness()
    deep_dive_emit()

    summary = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT,
        "n_tests": len(results),
        "n_ok": sum(1 for r in results if r["ok"]),
        "n_fail": sum(1 for r in results if not r["ok"]),
        "by_category": {},
        "results": results,
    }
    for r in results:
        c = r["category"]
        summary["by_category"].setdefault(c, {"ok": 0, "fail": 0})
        summary["by_category"][c]["ok" if r["ok"] else "fail"] += 1

    out_path = OUT / "deep_weird_results.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote {out_path}  ok={summary['n_ok']} fail={summary['n_fail']} total={summary['n_tests']}", flush=True)
    print("by_category:", json.dumps(summary["by_category"]), flush=True)


if __name__ == "__main__":
    main()
