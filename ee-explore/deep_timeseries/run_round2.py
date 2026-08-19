#!/usr/bin/env python3
"""Round 2: fix S2 harmonics, smarter JRC rising search, outlier zooms, LandTrendr."""

from __future__ import annotations

import json
import math
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_round2.json"
LOG = ROOT / "failures_round2.log"
THUMB = ROOT / "thumbs"
THUMB.mkdir(parents=True, exist_ok=True)

results: list[dict] = []


def init():
    ee.Initialize(project=PROJECT)


def gi(obj, label=""):
    try:
        return True, obj.getInfo()
    except Exception as e:  # noqa: BLE001
        msg = f"{label} {type(e).__name__}: {str(e)[:500]}"
        with LOG.open("a") as f:
            f.write(msg + "\n" + traceback.format_exc() + "\n---\n")
        return False, msg


def save_thumb(name, image, region, dims=512):
    try:
        url = image.getThumbURL({"region": region, "dimensions": dims, "format": "png"})
        path = THUMB / f"{name}.png"
        urllib.request.urlretrieve(url, str(path))
        return str(path)
    except Exception as e:  # noqa: BLE001
        with LOG.open("a") as f:
            f.write(f"thumb {name}: {e}\n")
        return f"thumb_fail: {e}"


def record(name, category, ok, detail, thumb=None, note="", lat=None, lng=None):
    results.append(
        {
            "name": name,
            "category": category,
            "ok": ok,
            "detail": detail,
            "thumb": thumb,
            "note": note,
            "lat": lat,
            "lng": lng,
        }
    )
    print(f"[{'OK' if ok else 'FAIL'}] {category:18} {name}", flush=True)


def jrc_freq(y0, y1):
    col = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory").filterDate(
        f"{y0}-01-01", f"{y1}-12-31"
    )
    water = col.map(lambda img: img.eq(2).rename("w").unmask(0))
    valid = col.map(lambda img: img.gt(0).rename("v").unmask(0))
    return water.sum().divide(valid.sum().max(1)).rename("freq").unmask(0)


def probe_s2_harmonic_fixed():
    sites = {
        "iowa_corn": (-93.5, 42.0),
        "sonoran": (-112.1, 33.4),
        "atlanta": (-84.25, 33.95),
        "el_yunque": (-65.79, 18.29),
    }
    for name, (lng, lat) in sites.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(1200)
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(pt)
            .filterDate("2019-01-01", "2024-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))
        )
        cs = (
            ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
            .filterBounds(pt)
            .filterDate("2019-01-01", "2024-12-31")
        )
        joined = ee.Join.saveFirst("cs").apply(
            s2,
            cs,
            ee.Filter.equals(leftField="system:index", rightField="system:index"),
        )

        def add_ndvi(img):
            img = ee.Image(img)
            clear = ee.Image(img.get("cs")).select("cs").gte(0.55)
            ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi").float()
            t = ee.Date(img.get("system:time_start"))
            doy = ee.Number(t.getRelative("day", "year")).add(1)
            w = doy.multiply(2 * math.pi / 365.25)
            # CRITICAL: cast to float() so band types are homogeneous across collection
            cos = ee.Image.constant(w.cos()).float().rename("cos")
            sin = ee.Image.constant(w.sin()).float().rename("sin")
            ones = ee.Image.constant(1).float().rename("constant")
            return (
                ndvi.updateMask(clear)
                .addBands([ones, cos, sin])
                .copyProperties(img, ["system:time_start"])
            )

        ndvi_col = ee.ImageCollection(joined).map(add_ndvi)
        independents = ee.List(["constant", "cos", "sin"])
        regressors = ndvi_col.select(independents.add("ndvi"))
        fit = regressors.reduce(ee.Reducer.linearRegression(3, 1))
        coef = fit.select("coefficients").arrayProject([0]).arrayFlatten([independents])
        amp = coef.select("cos").hypot(coef.select("sin")).rename("amp")
        phase = coef.select("sin").atan2(coef.select("cos"))
        doy_peak = phase.multiply(365.25 / (2 * math.pi))
        doy_peak = doy_peak.where(doy_peak.lt(0), doy_peak.add(365.25)).rename("doy_peak")

        ok, info = gi(
            ee.Image.cat([amp, doy_peak, coef]).reduceRegion(
                ee.Reducer.mean(), geom, 40, maxPixels=1e8, bestEffort=True
            ),
            f"s2fix_{name}",
        )
        # Also day-of-peak via max monthly NDVI proxy
        months = ee.List.sequence(1, 12)

        def month_ndvi(m):
            m = ee.Number(m)
            # all years 2019-2024 this month
            img = (
                ndvi_col.filter(ee.Filter.calendarRange(m, m, "month"))
                .select("ndvi")
                .mean()
            )
            d = img.reduceRegion(ee.Reducer.mean(), geom, 40, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"month": m, "ndvi": d.get("ndvi")})

        ok2, monthly = gi(ee.FeatureCollection(months.map(month_ndvi)), f"s2m_{name}")
        peak_month = None
        if ok2 and isinstance(monthly, dict):
            feats = monthly.get("features", [])
            vals = [
                (f["properties"]["month"], f["properties"].get("ndvi"))
                for f in feats
                if f["properties"].get("ndvi") is not None
            ]
            if vals:
                peak_month = max(vals, key=lambda x: x[1])

        vis = amp.visualize(min=0, max=0.45, palette=["#0c4a6e", "#fde047", "#16a34a"])
        thumb = save_thumb(f"s2_amp_fixed_{name}", vis, geom.bounds())
        record(
            f"s2_harmonic_fixed_{name}",
            "sentinel2",
            ok,
            {"fit": info if ok else info, "monthly": monthly if ok2 else monthly, "peak_month": peak_month},
            thumb,
            note="Cloud Score+ harmonic with .float() cast; peak month proxy",
            lat=lat,
            lng=lng,
        )


def probe_jrc_weird_rising_v2():
    """Find inland rising-water pixels; exclude ocean-saturated grid artifacts."""
    early = jrc_freq(1984, 1993)
    late = jrc_freq(2014, 2021)
    delta = late.subtract(early).rename("d_freq").unmask(0)
    # occurrence from GSW to mask permanent ocean / never-water
    occ = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0)
    # Interesting rising: big positive delta, but NOT already permanent water (occ < 80)
    # and not empty desert (late freq > 0.05 OR early > 0.02)
    interesting = (
        delta.gt(0.15)
        .And(occ.lt(80))
        .And(late.gt(0.05))
        .And(occ.gt(1))  # some water history
    )
    # Candidate inland / engineered water bodies known or suspected
    candidates = {
        # Reservoirs that filled / expanded
        "three_gorges_skip": None,  # not US
        "lake_powell_delta": (-111.0, 37.0),  # expect FALLING
        "elephant_butte_nm": (-107.19, 33.15),
        "lake_sakakawea_nd": (-101.4, 47.6),
        "fort_peck_mt": (-106.4, 48.0),
        "toledo_bend_tx": (-93.7, 31.5),
        "lake_ouachita_ar": (-93.1, 34.6),
        "clinton_lake_ks": (-95.35, 38.92),
        # Mining / pits
        "florida_phosphate_belt": (-82.0, 27.7),
        "minnesota_iron_range": (-92.5, 47.5),
        "wyoming_coal_pit": (-109.0, 44.0),
        # Coastal marsh / land-loss / canal
        "plaquemines_la": (-89.7, 29.4),
        "terrebonne_la": (-90.8, 29.3),
        "cameron_la": (-93.3, 29.8),
        "san_leon_tx": (-94.97, 29.48),
        # Irrigation / rice
        "arkansas_rice": (-91.5, 34.5),
        "california_rice_sac": (-121.7, 39.3),
        # Urban ponds / quarry
        "dallas_lakes": (-96.9, 32.9),
        "phoenix_lakes": (-111.9, 33.4),
        # Strange: Bonneville salt flats edge / GSL arms
        "gsl_farmington_bay": (-112.1, 41.0),
        # Cape Canaveral / Space Coast canals
        "merritt_island": (-80.7, 28.5),
        # Willapa / oyster
        "willapa_bay": (-123.95, 46.5),
        # Columbia River reservoirs
        "john_day_pool": (-120.0, 45.8),
        # Imperial valley canals vs salton
        "imperial_valley": (-115.5, 33.0),
        # Puerto Rico reservoir
        "lago_dos_bocas_pr": (-66.67, 18.33),
        # Bakken produced-water / stock ponds cluster
        "williston_nd": (-103.6, 48.15),
        # Appalachia mine ponds
        "wv_mine_ponds": (-81.5, 37.8),
        # Mississippi oxbow cutoffs
        "yazoo_ms": (-90.9, 32.8),
        # Everglades restoration STA
        "everglades_sta": (-80.6, 26.5),
    }

    scored = []
    for name, coords in candidates.items():
        if coords is None:
            continue
        lng, lat = coords
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(6000)
        ok, info = gi(
            ee.Image.cat(
                [
                    early.rename("early"),
                    late.rename("late"),
                    delta.rename("d_freq"),
                    occ.rename("occ"),
                ]
            ).reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.percentile([90, 99]), None, True),
                geom,
                60,
                maxPixels=1e8,
                bestEffort=True,
            ),
            f"jrc2_{name}",
        )
        d_mean = info.get("d_freq_mean") if ok and isinstance(info, dict) else None
        scored.append({"name": name, "lng": lng, "lat": lat, "stats": info if ok else info, "d_mean": d_mean})
        vis = delta.visualize(min=-0.4, max=0.4, palette=["#7f1d1d", "#fafaf9", "#0284c8"])
        thumb = save_thumb(f"jrc2_{name}", vis, geom.bounds())
        record(
            f"jrc2_candidate_{name}",
            "jrc_v2",
            ok,
            scored[-1],
            thumb,
            note="targeted rising/falling water candidates",
            lat=lat,
            lng=lng,
        )

    # Regional reduceToVectors-ish: sample interesting mask in LA coast + FL phosphate + AR rice
    hotspots = {
        "la_coast_box": ee.Geometry.Rectangle([-92.5, 29.0, -89.0, 30.2]),
        "fl_phosphate_box": ee.Geometry.Rectangle([-82.5, 27.3, -81.5, 28.2]),
        "ar_rice_box": ee.Geometry.Rectangle([-92.0, 34.0, -90.5, 35.5]),
        "nd_bakken_box": ee.Geometry.Rectangle([-104.5, 47.5, -102.0, 49.0]),
        "tx_coast_box": ee.Geometry.Rectangle([-95.5, 28.5, -94.0, 30.0]),
    }
    for hname, box in hotspots.items():
        # Mask to interesting rising, sample top pixels
        masked = delta.updateMask(interesting).clip(box)
        # Sample
        ok, samples = gi(
            masked.sample(region=box, scale=120, numPixels=400, seed=7, geometries=True),
            f"hsample_{hname}",
        )
        top = []
        if ok and isinstance(samples, dict):
            feats = samples.get("features", [])
            feats = sorted(
                feats,
                key=lambda f: (f.get("properties") or {}).get("d_freq") or -999,
                reverse=True,
            )
            top = feats[:8]
        record(
            f"jrc2_hotspot_sample_{hname}",
            "jrc_v2",
            ok,
            {"top_pixels": top},
            note="sample rising pixels (delta>0.15, occ 1-80) in box",
        )
        # Zoom #1 top pixel
        if top:
            coords = top[0]["geometry"]["coordinates"]
            lng, lat = coords[0], coords[1]
            pt = ee.Geometry.Point([lng, lat])
            geom = pt.buffer(1500)
            ok2, info2 = gi(
                ee.Image.cat([early.rename("early"), late.rename("late"), delta, occ.rename("occ")]).reduceRegion(
                    ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True
                ),
                f"jrc2_zoom_{hname}",
            )
            # before/after thumbs
            vis_d = delta.visualize(min=-0.3, max=0.6, palette=["#450a0a", "#fafaf9", "#0ea5e9"])
            vis_l = late.visualize(min=0, max=1, palette=["#1c1917", "#38bdf8", "#fff"])
            t1 = save_thumb(f"jrc2_zoom_delta_{hname}", vis_d, geom.bounds(), 768)
            t2 = save_thumb(f"jrc2_zoom_late_{hname}", vis_l, geom.bounds(), 768)
            record(
                f"jrc2_zoom_top_{hname}",
                "jrc_v2",
                ok2,
                {"pixel": top[0], "buffer_stats": info2 if ok2 else info2, "late_thumb": t2},
                t1,
                note="finest zoom on weirdest rising pixel in box",
                lat=lat,
                lng=lng,
            )


def probe_growth_better():
    """Better fringe points — true desert→suburb edges."""
    sites = {
        "phoenix_buckeye": (-112.55, 33.42),       # far west fringe
        "phoenix_queen_creek": (-111.65, 33.25),
        "austin_manor": (-97.55, 30.35),            # east growth
        "austin_bee_cave": (-97.95, 30.31),
        "atlanta_cumming": (-84.14, 34.21),
        "dallas_frisco": (-96.82, 33.15),
        "dallas_mckinney": (-96.70, 33.20),
        "houston_katy": (-95.82, 29.79),
    }
    ranking = []
    for name, (lng, lat) in sites.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(5000)
        b16 = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(pt)
            .filterDate("2016-01-01", "2017-01-01")
            .select("built")
            .mean()
        )
        b24 = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(pt)
            .filterDate("2024-01-01", "2025-01-01")
            .select("built")
            .mean()
        )
        d = b24.subtract(b16).rename("dbuilt")
        ok, info = gi(
            ee.Image.cat([b16.rename("b16"), b24.rename("b24"), d]).reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.percentile([90, 99]), None, True),
                geom,
                20,
                maxPixels=1e8,
                bestEffort=True,
            ),
            f"dw2_{name}",
        )
        mean_d = info.get("dbuilt_mean") if ok and isinstance(info, dict) else None
        ranking.append({"name": name, "lng": lng, "lat": lat, "mean_dbuilt": mean_d, "stats": info})
        vis = d.visualize(min=-0.15, max=0.45, palette=["#14532d", "#fafaf9", "#dc2626"])
        thumb = save_thumb(f"dw2_surge_{name}", vis, geom.bounds())
        record(
            f"dw2_surge_{name}",
            "dynamic_world",
            ok,
            ranking[-1],
            thumb,
            note="true fringe growth comparison",
            lat=lat,
            lng=lng,
        )

    ranking = [r for r in ranking if r["mean_dbuilt"] is not None]
    ranking.sort(key=lambda x: x["mean_dbuilt"], reverse=True)
    record("dw2_ranking", "dynamic_world", True, ranking, note="sorted by mean built surge")

    if ranking:
        top = ranking[0]
        lng, lat = top["lng"], top["lat"]
        pt = ee.Geometry.Point([lng, lat])
        for buf, tag in [(1200, "1p2km"), (400, "400m")]:
            geom = pt.buffer(buf)
            # class trajectory
            traj = []
            for y in [2016, 2018, 2020, 2022, 2024]:
                img = (
                    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                    .filterBounds(pt)
                    .filterDate(f"{y}-01-01", f"{y}-12-31")
                    .select(["built", "crops", "trees", "grass", "shrub_and_scrub", "bare"])
                    .mean()
                )
                ok, info = gi(
                    img.reduceRegion(ee.Reducer.mean(), geom, 10, maxPixels=1e8, bestEffort=True),
                    f"dw2_traj_{top['name']}_{y}_{tag}",
                )
                traj.append({"year": y, "props": info if ok else info})
            vis = (
                ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                .filterBounds(pt)
                .filterDate("2024-01-01", "2025-01-01")
                .select("built")
                .mean()
                .visualize(min=0, max=0.8, palette=["#052e16", "#fbbf24", "#b91c1c"])
            )
            thumb = save_thumb(f"dw2_zoom_built24_{top['name']}_{tag}", vis, geom.bounds(), 768)
            record(
                f"dw2_zoom_traj_{top['name']}_{tag}",
                "dynamic_world",
                True,
                traj,
                thumb,
                note=f"class traj at biggest surge {top['name']}",
                lat=lat,
                lng=lng,
            )


def probe_landtrendr_fixed():
    lng, lat = -122.0, 44.5
    pt = ee.Geometry.Point([lng, lat])
    geom = pt.buffer(3000)

    def prep8(img):
        img = ee.Image(img)
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        nir = img.select("SR_B5").multiply(0.0000275).add(-0.2)
        swir2 = img.select("SR_B7").multiply(0.0000275).add(-0.2)
        nbr = nir.subtract(swir2).divide(nir.add(swir2)).rename("NBR").float()
        return nbr.updateMask(clear).copyProperties(img, ["system:time_start"])

    def prep5(img):
        img = ee.Image(img)
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        nir = img.select("SR_B4").multiply(0.0000275).add(-0.2)
        swir2 = img.select("SR_B7").multiply(0.0000275).add(-0.2)
        nbr = nir.subtract(swir2).divide(nir.add(swir2)).rename("NBR").float()
        return nbr.updateMask(clear).copyProperties(img, ["system:time_start"])

    l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterBounds(pt).filterDate("1990-01-01", "2012-01-01").map(prep5)
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(pt).filterDate("2013-01-01", "2023-12-31").map(prep8)
    col = l5.merge(l8)

    # Build annual collection the LandTrendr way
    years = ee.List.sequence(1990, 2023)

    def annual(y):
        y = ee.Number(y)
        start = ee.Date.fromYMD(y, 1, 1)
        end = start.advance(1, "year")
        return (
            col.filterDate(start, end)
            .median()
            .set("system:time_start", start.millis())
            .toFloat()
        )

    annual = ee.ImageCollection.fromImages(years.map(annual))
    # LandTrendr wants dict with timeSeries as ImageCollection
    try:
        lt_result = ee.Algorithms.TemporalSegmentation.LandTrendr(
            timeSeries=annual,
            maxSegments=6,
            spikeThreshold=0.9,
            vertexCountOvershoot=3,
            preventOneYearRecovery=True,
            recoveryThreshold=0.25,
            pvalThreshold=0.05,
            bestModelProportion=0.75,
            minObservationsNeeded=6,
        )
        ok, bands = gi(lt_result.bandNames(), "lt_bands")
        # LandTrendr returns 'LandTrendr' array band: [year, src, fitted, mag, dur, rate, ...]
        # Extract years and fitted via arraySlice
        lt = lt_result.select("LandTrendr")
        # rmse band sometimes separate
        ok2, rmse = gi(
            lt_result.select("rmse").reduceRegion(
                ee.Reducer.mean(), geom, 90, maxPixels=1e7, bestEffort=True
            ),
            "lt_rmse",
        )
        # Get vertex count proxy: count of non-zero year rows is hard server-side;
        # sample one pixel series
        ok3, pix = gi(
            lt_result.sample(region=pt.buffer(90), scale=90, numPixels=3, geometries=True),
            "lt_sample",
        )
        vis = lt_result.select("rmse").visualize(min=0, max=0.15, palette=["#fff", "#f97316", "#7f1d1d"])
        thumb = save_thumb("landtrendr_rmse_cascades", vis, geom.bounds())
        record(
            "landtrendr_cascades_fixed",
            "landtrendr",
            ok,
            {"bands": bands if ok else bands, "rmse": rmse if ok2 else rmse, "sample_n": len(pix.get("features", [])) if ok3 and isinstance(pix, dict) else pix},
            thumb,
            note="LandTrendr kwargs args; annual NBR 1990-2023 Cascades",
            lat=lat,
            lng=lng,
        )
    except Exception as e:  # noqa: BLE001
        record("landtrendr_cascades_fixed", "landtrendr", False, str(e)[:500], note="still failing")


def probe_paradise_and_climate_zoom():
    # Paradise recovery yearly numbers already have — zoom NBR pre/post
    lng, lat = -121.62, 39.75
    pt = ee.Geometry.Point([lng, lat])
    geom = pt.buffer(8000)

    def nbr_col(start, end):
        col = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(pt)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUD_COVER", 40))
        )

        def nbr(img):
            qa = img.select("QA_PIXEL")
            clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
            optical = img.select(["SR_B5", "SR_B7"]).multiply(0.0000275).add(-0.2)
            n = optical.normalizedDifference(["SR_B5", "SR_B7"]).rename("nbr")
            return n.updateMask(clear)

        return col.map(nbr).median()

    pre = nbr_col("2017-06-01", "2018-10-01")
    post = nbr_col("2018-11-20", "2019-06-01")
    rec = nbr_col("2023-06-01", "2023-10-01")
    dnbr = pre.subtract(post).rename("dnbr")
    ok, info = gi(
        ee.Image.cat([pre.rename("pre"), post.rename("post"), rec.rename("rec"), dnbr]).reduceRegion(
            ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True
        )
    )
    vis = dnbr.visualize(min=-0.1, max=0.8, palette=["#16a34a", "#fef08a", "#ef4444", "#450a0a"])
    thumb = save_thumb("paradise_dnbr_camp_fire", vis, geom.bounds(), 768)
    record(
        "paradise_dnbr_camp_fire",
        "fire_zoom",
        ok,
        info if ok else info,
        thumb,
        note="Camp Fire dNBR + 2023 recovery NBR",
        lat=lat,
        lng=lng,
    )

    # CHIRPS deep drought contrast Texas vs Iowa 2011/2012
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")

    def annual(y):
        return chirps.filterDate(f"{y}-01-01", f"{y+1}-01-01").sum().rename("precip")

    ref = ee.ImageCollection([annual(y) for y in range(1991, 2021)]).mean()
    for y in [2011, 2012, 2019, 2023]:
        anom = annual(y).subtract(ref).rename("anom")
        for name, (lng, lat) in {
            "iowa": (-93.5, 42.0),
            "texas_hill": (-98.5, 30.0),
            "arizona": (-112.0, 33.5),
            "louisiana": (-91.0, 30.5),
        }.items():
            ok, info = gi(
                anom.reduceRegion(
                    ee.Reducer.mean(),
                    ee.Geometry.Point([lng, lat]).buffer(25000),
                    5000,
                    maxPixels=1e7,
                    bestEffort=True,
                )
            )
            record(
                f"chirps2_{y}_{name}",
                "chirps",
                ok,
                info if ok else info,
                note=f"annual precip anomaly {y}",
                lat=lat,
                lng=lng,
            )

    # Hansen SE Georgia lossyear histogram — plantation cycle
    hansen = ee.Image("UMD/hansen/global_forest_change_2024_v1_12")
    try:
        lossyear = hansen.select("lossyear")
        loss = hansen.select("loss")
    except Exception:
        hansen = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")
        lossyear = hansen.select("lossyear")
        loss = hansen.select("loss")

    lng, lat = -82.5, 31.5
    geom = ee.Geometry.Point([lng, lat]).buffer(40000)
    ok, hist = gi(
        lossyear.updateMask(loss).reduceRegion(
            ee.Reducer.frequencyHistogram(), geom, 60, maxPixels=1e8, bestEffort=True
        ),
        "hansen_ga_hist",
    )
    vis = lossyear.updateMask(loss).visualize(min=1, max=23, palette=["#fef3c7", "#ea580c", "#7f1d1d"])
    thumb = save_thumb("hansen_se_ga_zoom", vis, geom.bounds(), 768)
    record(
        "hansen_se_ga_lossyear_hist",
        "hansen",
        ok,
        hist if ok else hist,
        thumb,
        note="SE Georgia plantation harvest cadence via lossyear",
        lat=lat,
        lng=lng,
    )

    # Louisiana wetland NDVI decline zoom — coastal land loss
    lng, lat = -90.0, 29.5
    pt = ee.Geometry.Point([lng, lat])
    geom = pt.buffer(10000)
    # early vs late NDVI summer
    def ls_ndvi(start, end):
        def prep(img):
            qa = img.select("QA_PIXEL")
            clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
            # L5/L8 handle separately later — use L5 for early L8 for late
            return img

        return prep

    l5 = (
        ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        .filterBounds(pt)
        .filterDate("1985-06-01", "1990-09-30")
        .filter(ee.Filter.calendarRange(6, 9, "month"))
    )

    def ndvi5(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        o = img.select(["SR_B3", "SR_B4"]).multiply(0.0000275).add(-0.2)
        return o.normalizedDifference(["SR_B4", "SR_B3"]).rename("ndvi").updateMask(clear)

    def ndvi8(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        o = img.select(["SR_B4", "SR_B5"]).multiply(0.0000275).add(-0.2)
        return o.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi").updateMask(clear)

    early = l5.map(ndvi5).median()
    late = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(pt)
        .filterDate("2019-06-01", "2024-09-30")
        .filter(ee.Filter.calendarRange(6, 9, "month"))
        .map(ndvi8)
        .median()
    )
    d = late.subtract(early).rename("dndvi")
    ok, info = gi(
        ee.Image.cat([early.rename("early"), late.rename("late"), d]).reduceRegion(
            ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True
        )
    )
    vis = d.visualize(min=-0.3, max=0.3, palette=["#7f1d1d", "#fafaf9", "#166534"])
    thumb = save_thumb("la_wetland_ndvi_delta", vis, geom.bounds(), 768)
    record(
        "la_wetland_summer_ndvi_delta",
        "landsat_zoom",
        ok,
        info if ok else info,
        thumb,
        note="LA wetland summer NDVI late(2019-24) - early(1985-90)",
        lat=lat,
        lng=lng,
    )


def probe_modis_doy_peak():
    """MODIS phenology: day of peak NDVI for biomes."""
    for name, (lng, lat) in {
        "iowa_corn": (-93.5, 42.0),
        "sonoran": (-112.1, 33.4),
        "el_yunque": (-65.79, 18.29),
        "manhattan": (-73.985, 40.748),
        "olympic": (-123.8, 47.8),
    }.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(4000)
        col = (
            ee.ImageCollection("MODIS/061/MOD13Q1")
            .filterBounds(pt)
            .filterDate("2018-01-01", "2024-12-31")
            .select("NDVI")
        )
        # quality-ish: just use all; find DOY of max via qualityMosaic trick
        def add_doy(img):
            doy = ee.Date(img.get("system:time_start")).getRelative("day", "year").add(1)
            nd = img.multiply(0.0001).rename("ndvi")
            return nd.addBands(ee.Image.constant(doy).rename("doy").float()).copyProperties(
                img, ["system:time_start"]
            )

        with_doy = col.map(add_doy)
        # qualityMosaic on ndvi picks pixel with max ndvi; keep doy
        peak = with_doy.qualityMosaic("ndvi")
        ok, info = gi(
            peak.reduceRegion(ee.Reducer.mean(), geom, 250, maxPixels=1e7, bestEffort=True),
            f"modis_peak_{name}",
        )
        # Also per-year peak doy mean
        years = ee.List.sequence(2018, 2024)

        def year_peak(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            img = with_doy.filterDate(start, start.advance(1, "year")).qualityMosaic("ndvi")
            d = img.reduceRegion(ee.Reducer.mean(), geom, 250, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"year": y, "doy": d.get("doy"), "ndvi": d.get("ndvi")})

        ok2, series = gi(ee.FeatureCollection(years.map(year_peak)), f"modis_ypeak_{name}")
        vis = peak.select("doy").visualize(min=100, max=250, palette=["#1d4ed8", "#fde047", "#b91c1c"])
        thumb = save_thumb(f"modis_doy_peak_{name}", vis, geom.bounds())
        record(
            f"modis_doy_peak_{name}",
            "modis_phenology",
            ok,
            {"mean_peak": info if ok else info, "yearly": series if ok2 else series},
            thumb,
            note="MOD13Q1 qualityMosaic day-of-peak greenness",
            lat=lat,
            lng=lng,
        )


def main():
    LOG.write_text(f"start {datetime.now(timezone.utc).isoformat()}\n")
    init()
    for label, fn in [
        ("s2_fixed", probe_s2_harmonic_fixed),
        ("jrc_v2", probe_jrc_weird_rising_v2),
        ("growth", probe_growth_better),
        ("landtrendr", probe_landtrendr_fixed),
        ("zooms", probe_paradise_and_climate_zoom),
        ("modis_phen", probe_modis_doy_peak),
    ]:
        print(f"\n--- {label} ---", flush=True)
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            with LOG.open("a") as f:
                f.write(f"CRASH {label}: {e}\n{traceback.format_exc()}\n")
            record(f"CRASH_{label}", "crash", False, str(e)[:500])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_probes": len(results),
        "n_ok": sum(1 for r in results if r["ok"]),
        "n_fail": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote {OUT} ({summary['n_probes']} probes)", flush=True)


if __name__ == "__main__":
    main()
