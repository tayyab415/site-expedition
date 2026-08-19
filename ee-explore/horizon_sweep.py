#!/usr/bin/env python3
"""Push Earth Engine across many capabilities. Save what works / fails."""

from __future__ import annotations

import json
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
OUT = Path(__file__).resolve().parent / "horizon_sweep.json"
THUMB = Path(__file__).resolve().parent / "horizon_thumbs"
THUMB.mkdir(exist_ok=True)

# Mix of places so different datasets light up
PLACES = {
    "galveston": (-94.8, 29.3),
    "ashburn": (-77.4874, 39.0438),
    "yosemite": (-119.55, 37.75),
    "iowa_corn": (-93.5, 42.0),
    "la": (-118.25, 34.05),
    "miami": (-80.19, 25.76),
    "seattle": (-122.33, 47.61),
}


def init():
    ee.Initialize(project=PROJECT)


def gi(obj, label=""):
    try:
        return True, obj.getInfo()
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:300]}"


def save_thumb(name: str, image: ee.Image, region, dims=512) -> str | None:
    try:
        url = image.getThumbURL(
            {"region": region, "dimensions": dims, "format": "png"}
        )
        path = THUMB / f"{name}.png"
        urllib.request.urlretrieve(url, path)
        return str(path)
    except Exception as e:  # noqa: BLE001
        return f"thumb_fail: {e}"


def mean(img, geom, scale, band=None):
    src = img.select(band) if band else img
    ok, info = gi(
        src.reduceRegion(
            ee.Reducer.mean(), geom, scale, maxPixels=1e8, bestEffort=True
        )
    )
    if not ok:
        return None, info
    key = band or list(info.keys())[0] if info else None
    return (info.get(key) if key else None), None


results = []


def record(name, category, ok, detail, thumb=None, note=""):
    results.append(
        {
            "name": name,
            "category": category,
            "ok": ok,
            "detail": detail,
            "thumb": thumb,
            "note": note,
        }
    )
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {category:16} {name}", flush=True)


def run():
    init()
    print("Horizon sweep starting…", flush=True)

    # ---------- 1) Catalog / metadata ----------
    ok, info = gi(ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").limit(1).size())
    ok2, ids = gi(
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate("2023-06-01", "2023-06-02")
        .limit(1)
        .aggregate_array("system:index")
    )
    record(
        "list_sentinel2_meta",
        "catalog",
        ok,
        {"limit1_size": info if ok else info, "sample_ids": ids if ok2 else ids},
        note="Can we read collection metadata?",
    )

    # ---------- 2) Optical: Cloud Score+ masked NDVI time series ----------
    pt = ee.Geometry.Point(PLACES["iowa_corn"])
    geom = pt.buffer(500)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(pt)
        .filterDate("2023-05-01", "2023-09-30")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
    )
    cs = (
        ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
        .filterBounds(pt)
        .filterDate("2023-05-01", "2023-09-30")
    )
    joined = ee.Join.saveFirst("cs").apply(
        s2,
        cs,
        ee.Filter.equals(leftField="system:index", rightField="system:index"),
    )

    def add_ndvi(img):
        img = ee.Image(img)
        cs_img = ee.Image(img.get("cs"))
        clear = ee.Image(cs_img).select("cs").gte(0.6)
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
        return ndvi.updateMask(clear).copyProperties(img, ["system:time_start"])

    ndvi_col = ee.ImageCollection(joined).map(add_ndvi)
    # Sample monthly means as a chart-like series
    months = ee.List.sequence(5, 9)

    def month_mean(m):
        m = ee.Number(m)
        start = ee.Date.fromYMD(2023, m, 1)
        end = start.advance(1, "month")
        img = ndvi_col.filterDate(start, end).mean()
        d = img.reduceRegion(ee.Reducer.mean(), geom, 20, maxPixels=1e7, bestEffort=True)
        return ee.Feature(
            None,
            {"month": m, "ndvi": d.get("ndvi")},
        )

    series = ee.FeatureCollection(months.map(month_mean))
    ok, info = gi(series)
    record(
        "s2_cloudscore_ndvi_monthly",
        "optical_timeseries",
        ok,
        info if ok else info,
        note="Crop greenness May–Sep with Google Cloud Score+ cloud mask",
    )
    if ok:
        med = ndvi_col.median()
        vis = med.visualize(min=0, max=0.8, palette=["#3b1f0b", "#eab308", "#16a34a"])
        thumb = save_thumb("iowa_ndvi_summer2023", vis, geom.bounds())
        results[-1]["thumb"] = thumb

    # ---------- 3) Radar: Sentinel-1 VV backscatter ----------
    pt = ee.Geometry.Point(PLACES["galveston"])
    geom = pt.buffer(8000).bounds()
    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(pt)
        .filterDate("2023-01-01", "2023-12-31")
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .select("VV")
    )
    ok_n, n = gi(s1.size())
    if ok_n and n:
        vv = s1.mean()
        ok, info = gi(
            vv.reduceRegion(ee.Reducer.mean(), pt.buffer(1000), 20, maxPixels=1e7)
        )
        vis = vv.visualize(min=-20, max=0, palette=["#000000", "#38bdf8", "#ffffff"])
        thumb = save_thumb("galveston_s1_vv", vis, geom)
        record(
            "sentinel1_vv_mean",
            "radar",
            ok,
            {"n_images": n, "vv_mean_db": info.get("VV") if ok else info},
            thumb,
            note="Radar sees through clouds — useful for floods / ships / wet ground",
        )
    else:
        record("sentinel1_vv_mean", "radar", False, n if not ok_n else "empty", note="")

    # ---------- 4) Night lights VIIRS ----------
    pt = ee.Geometry.Point(PLACES["la"])
    geom = pt.buffer(40000).bounds()
    viirs = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate("2023-01-01", "2023-12-31")
        .select("avg_rad")
        .mean()
    )
    ok, info = gi(
        viirs.reduceRegion(ee.Reducer.mean(), pt.buffer(5000), 500, maxPixels=1e7)
    )
    vis = viirs.visualize(min=0, max=60, palette=["#0b1020", "#7c3aed", "#fde047", "#fff"])
    thumb = save_thumb("la_nightlights_2023", vis, geom)
    record(
        "viirs_nightlights",
        "nightlights",
        ok,
        info if ok else info,
        thumb,
        note="City glow from space — activity / blackout proxy",
    )

    # ---------- 5) Fire: FIRMS + NBR burn scar near LA hills ----------
    # Woolsey-ish / general SoCal — use Sierra foothills fire-prone area
    pt = ee.Geometry.Point([-118.6, 34.2])  # Santa Monica mountains area
    geom = pt.buffer(25000).bounds()
    firms = (
        ee.ImageCollection("FIRMS")
        .filterBounds(pt.buffer(25000))
        .filterDate("2018-01-01", "2019-12-31")
    )
    ok_n, n = gi(firms.size())
    # Landsat NBR before/after Nov 2018 Woolsey
    def nbr(col):
        return (
            col.filterBounds(pt)
            .filter(ee.Filter.lt("CLOUD_COVER", 30))
            .map(
                lambda img: img.normalizedDifference(["SR_B5", "SR_B7"]).rename("nbr")
            )
            .median()
        )

    pre = nbr(
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterDate("2018-06-01", "2018-10-15")
    )
    post = nbr(
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterDate("2018-11-20", "2019-03-01")
    )
    dNBR = pre.subtract(post).rename("dnbr")
    ok, info = gi(
        dNBR.reduceRegion(ee.Reducer.percentile([50, 90]), pt.buffer(10000), 30, maxPixels=1e8)
    )
    vis = dNBR.visualize(min=-0.2, max=0.8, palette=["#16a34a", "#fef08a", "#ef4444", "#450a0a"])
    thumb = save_thumb("socal_dnbr_woolsey_window", vis, geom)
    record(
        "landsat_dnbr_burnscar",
        "fire",
        ok,
        {"firms_count_2018_19": n if ok_n else ok_n, "dnbr_stats": info if ok else info},
        thumb,
        note="Burn severity from Landsat before/after fire season",
    )

    # ---------- 6) Snow: MODIS snow cover days near Seattle Cascades ----------
    pt = ee.Geometry.Point([-121.5, 47.5])
    geom = pt.buffer(40000).bounds()
    snow = (
        ee.ImageCollection("MODIS/061/MOD10A1")
        .filterDate("2023-11-01", "2024-04-30")
        .select("NDSI_Snow_Cover")
    )
    # count days with NDSI snow cover > 40
    snow_days = snow.map(lambda img: img.gt(40).rename("snow")).sum()
    ok, info = gi(
        snow_days.reduceRegion(ee.Reducer.mean(), pt.buffer(5000), 500, maxPixels=1e7)
    )
    vis = snow_days.visualize(min=0, max=120, palette=["#0ea5e9", "#ffffff"])
    thumb = save_thumb("cascades_snow_days_2324", vis, geom)
    record(
        "modis_snow_days",
        "snow",
        ok,
        info if ok else info,
        thumb,
        note="How many snowy days in winter — ski / water-supply vibe",
    )

    # ---------- 7) Crops: USDA CDL corn vs soy flip ----------
    pt = ee.Geometry.Point(PLACES["iowa_corn"])
    geom = pt.buffer(15000).bounds()
    cdl19 = ee.Image("USDA/NASS/CDL/2019").select("cropland")
    cdl23 = ee.Image("USDA/NASS/CDL/2023").select("cropland")
    # 1=corn, 5=soybeans
    corn19 = cdl19.eq(1)
    soy23 = cdl23.eq(5)
    flip = corn19.And(soy23).rename("corn_to_soy")
    ok, info = gi(
        flip.reduceRegion(ee.Reducer.mean(), pt.buffer(10000), 30, maxPixels=1e8)
    )
    # visualize 2023 crops (random palette-ish)
    vis = cdl23.visualize(
        min=1,
        max=20,
        palette=["#ffff00", "#ff00ff", "#00ff00", "#0000ff", "#a0522d"],
    )
    thumb = save_thumb("iowa_cdl_2023", vis, geom)
    record(
        "cdl_corn_to_soy_fraction",
        "agriculture",
        ok,
        {"fraction_corn19_to_soy23": info.get("corn_to_soy") if ok else info},
        thumb,
        note="USDA crop map — which fields switched crops",
    )

    # ---------- 8) Population / built: GHSL ----------
    pt = ee.Geometry.Point(PLACES["ashburn"])
    geom = pt.buffer(20000).bounds()
    pop = ee.Image("JRC/GHSL/P2023A/GHS_POP_E2030/3857").rename("pop")
    # reproject-ish by reducing in native
    ok, info = gi(
        pop.reduceRegion(ee.Reducer.sum(), pt.buffer(5000), 100, maxPixels=1e8, crs="EPSG:3857")
    )
    built = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S_E2020/3857").select(0).rename("built")
    ok2, info2 = gi(
        built.reduceRegion(ee.Reducer.mean(), pt.buffer(5000), 100, maxPixels=1e8, crs="EPSG:3857")
    )
    vis = built.visualize(min=0, max=50, palette=["#0b1020", "#f97316", "#fef08a"])
    thumb = save_thumb("ashburn_ghsl_built2020", vis, geom)
    record(
        "ghsl_pop_built",
        "population",
        ok and ok2,
        {"pop_sum_5km_2030": info if ok else info, "built_mean": info2 if ok2 else info2},
        thumb,
        note="People + building density grids from EU JRC",
    )

    # ---------- 9) Canopy height ETH Global ----------
    pt = ee.Geometry.Point(PLACES["yosemite"])
    geom = pt.buffer(20000).bounds()
    ch = ee.Image("ETH_GlobalSegmap_IRAD/ETH_GlobalCanopyHeight_10m_2020").select(0).rename("h")
    # dataset id might differ — try alternate
    ok, info = gi(
        ch.reduceRegion(ee.Reducer.mean(), pt.buffer(2000), 30, maxPixels=1e7)
    )
    if not ok:
        # try well-known ID
        for asset in [
            "projects/meta-forest-monitoring-okw37/assets/CanopyHeight",
            "NASA/GEDI/GEDI02_A_002_MONTHLY",
            "LARSE/GEDI/GEDI02_A_002_MONTHLY",
        ]:
            try:
                if "MONTHLY" in asset:
                    img = (
                        ee.ImageCollection(asset)
                        .filterBounds(pt)
                        .filterDate("2020-01-01", "2020-12-31")
                        .select("rh98")
                        .mean()
                        .rename("h")
                    )
                else:
                    img = ee.Image(asset).select(0).rename("h")
                ok, info = gi(
                    img.reduceRegion(ee.Reducer.mean(), pt.buffer(2000), 30, maxPixels=1e7)
                )
                if ok:
                    ch = img
                    break
            except Exception:  # noqa: BLE001
                continue
    if ok:
        vis = ch.visualize(min=0, max=40, palette=["#fef3c7", "#16a34a", "#064e3b"])
        thumb = save_thumb("yosemite_canopy_height", vis, geom)
    else:
        thumb = None
    record(
        "canopy_height",
        "forest",
        ok,
        info if ok else info,
        thumb,
        note="Tree height from space (GEDI / canopy maps)",
    )

    # ---------- 10) Climate: ERA5-Land monthly temp + precip ----------
    pt = ee.Geometry.Point(PLACES["miami"])
    era = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate("2023-01-01", "2023-12-31")
        .select(["temperature_2m", "total_precipitation_sum"])
    )
    ok_n, n = gi(era.size())
    if ok_n and n:
        t = era.select("temperature_2m").mean().subtract(273.15).rename("t_c")
        p = era.select("total_precipitation_sum").sum().rename("p_m")
        ok_t, ti = gi(t.reduceRegion(ee.Reducer.mean(), pt, 10000))
        ok_p, pi = gi(p.reduceRegion(ee.Reducer.mean(), pt, 10000))
        record(
            "era5_land_miami_2023",
            "climate",
            ok_t and ok_p,
            {
                "months": n,
                "mean_temp_c": ti.get("t_c") if ok_t else ti,
                "total_precip_m": pi.get("p_m") if ok_p else pi,
            },
            note="Weather model grid — heat + rain for a year",
        )
    else:
        record("era5_land_miami_2023", "climate", False, n)

    # ---------- 11) Soil moisture (SMAP) ----------
    pt = ee.Geometry.Point(PLACES["iowa_corn"])
    smap = (
        ee.ImageCollection("NASA/SMAP/SPL4SMGP/007")
        .filterBounds(pt)
        .filterDate("2023-07-01", "2023-07-31")
        .select("sm_surface")
    )
    ok_n, n = gi(smap.size())
    if ok_n and n:
        img = smap.mean()
        ok, info = gi(img.reduceRegion(ee.Reducer.mean(), pt.buffer(20000), 10000))
        vis = img.visualize(min=0.05, max=0.4, palette=["#78350f", "#fde68a", "#2563eb"])
        thumb = save_thumb("iowa_smap_jul2023", vis, pt.buffer(150000).bounds())
        record(
            "smap_soil_moisture",
            "soil",
            ok,
            {"n": n, "sm_surface": info.get("sm_surface") if ok else info},
            thumb,
            note="How wet the topsoil is — drought / farm signal",
        )
    else:
        # try older version
        smap = (
            ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
            .filterDate("2023-07-01", "2023-07-31")
            .select("ssm")
        )
        ok_n, n = gi(smap.size())
        if ok_n and n:
            img = smap.mean()
            ok, info = gi(img.reduceRegion(ee.Reducer.mean(), pt.buffer(20000), 10000))
            record("smap_soil_moisture", "soil", ok, {"n": n, "ssm": info}, note="fallback USDA SMAP")
        else:
            record("smap_soil_moisture", "soil", False, n)

    # ---------- 12) Open Buildings + NAIP high-res ----------
    pt = ee.Geometry.Point(PLACES["ashburn"])
    # Google Open Buildings temporal
    ob = ee.FeatureCollection("GOOGLE/Research/open-buildings-temporal/v1")
    # Actually open buildings v3 is image / FC depending — try FOOTPRINT polygons
    tried = []
    for asset in [
        "GOOGLE/Research/open-buildings/v3/polygons",
        "GOOGLE/Research/open-buildings-temporal/v1",
    ]:
        try:
            fc = ee.FeatureCollection(asset).filterBounds(pt.buffer(500))
            ok, n = gi(fc.size())
            tried.append({"asset": asset, "ok": ok, "n": n})
            if ok:
                record(
                    "open_buildings_count_500m",
                    "buildings",
                    True,
                    {"asset": asset, "count": n},
                    note="Building footprints from Google Research",
                )
                break
        except Exception as e:  # noqa: BLE001
            tried.append({"asset": asset, "ok": False, "err": str(e)[:200]})
    else:
        record("open_buildings_count_500m", "buildings", False, tried)

    naip = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterBounds(pt)
        .filterDate("2021-01-01", "2023-12-31")
        .mosaic()
    )
    ok, bands = gi(naip.bandNames())
    if ok:
        rgb = naip.select(["R", "G", "B"]) if "R" in bands else naip.select([0, 1, 2])
        vis = rgb.visualize(min=0, max=255)
        thumb = save_thumb("ashburn_naip", vis, pt.buffer(400).bounds(), dims=768)
        record(
            "naip_hires_aerial",
            "highres",
            True,
            {"bands": bands},
            thumb,
            note="Airplane photos ~1m — sharp local view",
        )
    else:
        record("naip_hires_aerial", "highres", False, bands)

    # ---------- 13) Terrain toys: hillshade, aspect, slope texture ----------
    dem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    pt = ee.Geometry.Point(PLACES["yosemite"])
    geom = pt.buffer(15000).bounds()
    slope = ee.Terrain.slope(dem)
    aspect = ee.Terrain.aspect(dem)
    hill = ee.Terrain.hillshade(dem, 315, 45)
    # simple texture: slope stdDev in neighborhood
    tex = slope.reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.circle(3))
    ok, info = gi(
        ee.Image.cat([slope.rename("s"), aspect.rename("a"), tex.rename("tex")]).reduceRegion(
            ee.Reducer.mean(), pt.buffer(2000), 30, maxPixels=1e7
        )
    )
    vis = hill.visualize(min=100, max=255)
    thumb = save_thumb("yosemite_hillshade", vis, geom)
    record(
        "terrain_hillshade_texture",
        "terrain",
        ok,
        info if ok else info,
        thumb,
        note="3D-looking hillshade + roughness roughness from DEM",
    )

    # ---------- 14) Tiny ML: sample Dynamic World, train smileCart, classify ----------
    pt = ee.Geometry.Point(PLACES["iowa_corn"])
    region = pt.buffer(3000)
    dw = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(pt)
        .filterDate("2023-06-01", "2023-08-31")
        .select(["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice", "label"])
        .mode()
    )
    # training from label band itself (sanity — not real generalization)
    samples = dw.stratifiedSample(
        numPoints=200,
        classBand="label",
        region=region,
        scale=30,
        seed=42,
        geometries=False,
    )
    classifier = ee.Classifier.smileCart().train(
        samples, "label", ["water", "trees", "grass", "crops", "built", "bare"]
    )
    classified = dw.select(["water", "trees", "grass", "crops", "built", "bare"]).classify(classifier)
    ok, info = gi(
        classified.rename("c").reduceRegion(ee.Reducer.frequencyHistogram(), region, 30, maxPixels=1e7)
    )
    record(
        "smilecart_toy_classify",
        "ml",
        ok,
        info if ok else info,
        note="Train a tiny decision-tree classifier inside EE (toy demo)",
    )

    # ---------- 15) Array / temporal profile as list ----------
    pt = ee.Geometry.Point(PLACES["galveston"])
    lst = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(pt)
        .filterDate("2023-01-01", "2023-12-31")
        .select("LST_Day_1km")
    )
    # reduce to 12 monthly values client-side via FeatureCollection
    def mstat(m):
        m = ee.Number(m)
        start = ee.Date.fromYMD(2023, m, 1)
        img = lst.filterDate(start, start.advance(1, "month")).mean().multiply(0.02).subtract(273.15)
        d = img.reduceRegion(ee.Reducer.mean(), pt, 1000)
        return ee.Feature(None, {"month": m, "lst_c": d.get("LST_Day_1km")})

    ok, info = gi(ee.FeatureCollection(ee.List.sequence(1, 12).map(mstat)))
    record(
        "modis_lst_monthly_profile",
        "timeseries",
        ok,
        info if ok else info,
        note="12-number temperature curve for one point — chart fuel",
    )

    # ---------- 16) Ocean: HYCOM / chlorophyll already partly done — try wave or salinity ----------
    pt = ee.Geometry.Point([-94.5, 28.5])  # Gulf
    hycom = (
        ee.ImageCollection("HYCOM/sea_temp_salinity")
        .filterDate("2023-08-01", "2023-08-07")
        .select("salinity_0")
        .mean()
        .multiply(0.001)
        .add(20)
    )  # scale per dataset docs often needed — record raw too
    ok, info = gi(hycom.reduceRegion(ee.Reducer.mean(), pt.buffer(20000), 10000))
    # also try Copernicus marine chl
    try:
        chl = (
            ee.ImageCollection("COPERNICUS/MARINE/OC_GLO_BGC/CHLOROPHYLL_PLANKTON/V6")
            .filterDate("2023-08-01", "2023-08-31")
            .first()
        )
        okc, bandc = gi(chl.bandNames())
    except Exception as e:  # noqa: BLE001
        okc, bandc = False, str(e)[:200]
    record(
        "ocean_salinity_hycom",
        "ocean",
        ok,
        {"salinity_rawish": info, "chl_bands_ok": okc, "chl_bands": bandc},
        note="Ocean model salinity near Galveston",
    )

    # ---------- 17) Aqueduct / flood hazard image ----------
    for asset in [
        "WRI/Aqueduct_Flood_Hazard_Maps/inundation_30years_rp100/v2",
        "WRI/Aqueduct_Water_Risk/V4/baseline_annual",
        "JRC/CEMS_GLOFAS/FloodHazard/v1",
    ]:
        try:
            if "baseline" in asset or "Water_Risk" in asset:
                img = ee.ImageCollection(asset).first() if "Collection" else ee.Image(asset)
                # Water risk is often an ImageCollection of indicators
                try:
                    img = ee.Image(asset)
                except Exception:
                    img = ee.ImageCollection(asset).first()
            else:
                img = ee.Image(asset)
            ok, bands = gi(img.bandNames())
            if ok:
                pt = ee.Geometry.Point(PLACES["miami"])
                ok2, info = gi(
                    img.select(0).reduceRegion(ee.Reducer.first(), pt, 1000, bestEffort=True)
                )
                record(
                    f"hazard_{asset.split('/')[-1]}",
                    "hazard_maps",
                    ok2,
                    {"asset": asset, "bands": bands, "sample": info},
                    note="Global flood / water-risk layers",
                )
                break
        except Exception as e:  # noqa: BLE001
            record(f"hazard_try_{asset[-20:]}", "hazard_maps", False, str(e)[:200])

    # ---------- 18) Kernel / morphological: built edge density ----------
    pt = ee.Geometry.Point(PLACES["la"])
    dw = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(pt)
        .filterDate("2023-01-01", "2023-12-31")
        .select("built")
        .mean()
    )
    edges = dw.gt(0.4).convolve(ee.Kernel.laplacian8()).abs().rename("edge")
    ok, info = gi(edges.reduceRegion(ee.Reducer.mean(), pt.buffer(5000), 30, maxPixels=1e7))
    vis = edges.visualize(min=0, max=0.5, palette=["#000", "#22d3ee", "#f43f5e"])
    thumb = save_thumb("la_built_edges", vis, pt.buffer(15000).bounds())
    record(
        "built_edge_laplacian",
        "image_ops",
        ok,
        info if ok else info,
        thumb,
        note="Find sharp city edges with a convolution kernel",
    )

    # ---------- 19) Connected components / vectorize sample ----------
    pt = ee.Geometry.Point(PLACES["galveston"])
    water = (
        ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
        .select("occurrence")
        .unmask(0)
        .gt(50)
        .selfMask()
    )
    # reduceToVectors on a small box
    box = pt.buffer(3000).bounds()
    vectors = water.reduceToVectors(
        geometry=box,
        scale=30,
        geometryType="polygon",
        eightConnected=False,
        maxPixels=1e7,
        labelProperty="water",
    )
    ok, n = gi(vectors.size())
    record(
        "water_reduceToVectors",
        "vectorize",
        ok,
        {"polygon_count": n if ok else n},
        note="Turn water pixels into polygons you can click",
    )

    # ---------- 20) Download URL (small geotiff) ----------
    dem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    region = ee.Geometry.Point(PLACES["yosemite"]).buffer(2000).bounds()
    try:
        url = dem.getDownloadURL(
            {
                "region": region,
                "scale": 90,
                "format": "GEO_TIFF",
                "filePerBand": False,
            }
        )
        dest = THUMB / "yosemite_dem_download.tif"
        urllib.request.urlretrieve(url, dest)
        record(
            "getDownloadURL_geotiff",
            "export",
            True,
            {"bytes": dest.stat().st_size, "path": str(dest)},
            note="Pull a real GeoTIFF file out of EE to disk",
        )
    except Exception as e:  # noqa: BLE001
        record("getDownloadURL_geotiff", "export", False, str(e)[:300])

    # ---------- 21) ImageCollection → short thumb strip (multi-date) ----------
    pt = ee.Geometry.Point(PLACES["iowa_corn"])
    thumbs = []
    for month in (5, 7, 9):
        img = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(pt)
            .filterDate(f"2023-{month:02d}-01", f"2023-{month:02d}-28")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .median()
            .normalizedDifference(["B8", "B4"])
        )
        vis = img.visualize(min=0, max=0.8, palette=["#78350f", "#facc15", "#15803d"])
        t = save_thumb(f"iowa_ndvi_2023_{month:02d}", vis, pt.buffer(2500).bounds())
        thumbs.append(t)
    record(
        "ndvi_month_strip",
        "animation_proxy",
        all(isinstance(t, str) and t.endswith(".png") for t in thumbs),
        {"thumbs": thumbs},
        note="Same field in May/Jul/Sep — greening then browning",
    )

    # ---------- 22) ESA WorldCover + Dynamic World disagreement ----------
    pt = ee.Geometry.Point(PLACES["seattle"])
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    dwlab = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(pt)
        .filterDate("2021-01-01", "2021-12-31")
        .select("label")
        .mode()
    )
    ok1, wci = gi(wc.reduceRegion(ee.Reducer.mode(), pt.buffer(300), 10))
    ok2, dwi = gi(dwlab.reduceRegion(ee.Reducer.mode(), pt.buffer(300), 10))
    record(
        "worldcover_vs_dynamicworld",
        "compare_maps",
        ok1 and ok2,
        {"esa_worldcover": wci, "dynamic_world": dwi},
        note="Two land-cover maps at same point — do they agree?",
    )

    # ---------- 23) Precipitation CHIRPS anomaly ----------
    pt = ee.Geometry.Point([-100.0, 32.0])  # west TX
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    july23 = chirps.filterDate("2023-07-01", "2023-07-31").sum()
    # climatology Jul 2000-2020
    clim = (
        ee.ImageCollection(
            [
                chirps.filterDate(f"{y}-07-01", f"{y}-07-31").sum()
                for y in range(2000, 2021)
            ]
        ).mean()
    )
    # EE can't take python list of images easily that way — do properly
    def july_sum(y):
        y = ee.Number(y)
        return chirps.filterDate(
            ee.Date.fromYMD(y, 7, 1), ee.Date.fromYMD(y, 8, 1)
        ).sum().set("y", y)

    clim = ee.ImageCollection(ee.List.sequence(2000, 2020).map(july_sum)).mean()
    anom = july23.subtract(clim).rename("anom")
    ok, info = gi(anom.reduceRegion(ee.Reducer.mean(), pt.buffer(20000), 5000))
    vis = anom.visualize(min=-100, max=100, palette=["#7f1d1d", "#fef3c7", "#1d4ed8"])
    thumb = save_thumb("west_tx_chirps_jul2023_anom", vis, pt.buffer(200000).bounds())
    record(
        "chirps_precip_anomaly",
        "climate",
        ok,
        info if ok else info,
        thumb,
        note="Was July 2023 wetter/drier than normal?",
    )

    # ---------- 24) Mangrove / coastal habitat ----------
    try:
        mang = ee.ImageCollection("LANDSAT/MANGROVE_FORESTS").first()  # may fail
        ok, bands = gi(mang.bandNames())
        record("mangrove_collection", "habitat", ok, bands)
    except Exception:
        # GMW
        for asset in [
            "projects/sat-io/open-datasets/GMW/extent/gmw_v3_2020",
            "UQ/murray/GSW/monthly_intertidal",
        ]:
            try:
                img = ee.Image(asset) if "gmw" in asset.lower() or "murray" in asset else ee.ImageCollection(asset).mosaic()
                if "murray" in asset:
                    img = ee.ImageCollection("UQ/murray/Intertidal/v1_1/data_mask").mosaic()
                ok, info = gi(
                    img.reduceRegion(
                        ee.Reducer.mean(),
                        ee.Geometry.Point([-81.7, 25.9]).buffer(5000),
                        30,
                        maxPixels=1e7,
                        bestEffort=True,
                    )
                )
                record("coastal_habitat_layer", "habitat", ok, {"asset": asset, "info": info})
                if ok:
                    break
            except Exception as e:  # noqa: BLE001
                record("coastal_habitat_try", "habitat", False, str(e)[:200])

    # ---------- 25) Server-side ee.List / math playground ----------
    ok, info = gi(ee.Number(2).pow(10).add(ee.Number(5).sqrt()))
    record("server_math", "platform", ok, info, note="Math runs on Google servers, not your laptop")

    # ---------- write ----------
    payload = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT,
        "n_tests": len(results),
        "n_ok": sum(1 for r in results if r["ok"]),
        "n_fail": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nWrote {OUT}  ok={payload['n_ok']} fail={payload['n_fail']}")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        Path(OUT).write_text(json.dumps({"results": results, "crash": True}, indent=2, default=str))
