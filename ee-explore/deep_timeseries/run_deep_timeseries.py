#!/usr/bin/env python3
"""Deep EE time-series + change probes. Failures logged; thumbs + JSON saved."""

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
OUT = ROOT / "results.json"
LOG = ROOT / "failures.log"
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


def save_thumb(name: str, image: ee.Image, region, dims=512) -> str | None:
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
    row = {
        "name": name,
        "category": category,
        "ok": ok,
        "detail": detail,
        "thumb": thumb,
        "note": note,
        "lat": lat,
        "lng": lng,
    }
    results.append(row)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {category:18} {name}", flush=True)


def reduce_mean(img, geom, scale, band=None):
    src = img.select(band) if band else img
    ok, info = gi(
        src.reduceRegion(
            ee.Reducer.mean(), geom, scale, maxPixels=1e8, bestEffort=True
        )
    )
    if not ok:
        return None, info
    if band:
        return info.get(band), None
    if not info:
        return None, "empty"
    return list(info.values())[0], None


# ---------------------------------------------------------------------------
# Places / biomes
# ---------------------------------------------------------------------------
BIOMES = {
    "sonoran_desert": (-112.1, 33.4),       # Phoenix fringe desert
    "iowa_corn": (-93.5, 42.0),
    "el_yunque_pr": (-65.79, 18.29),        # Puerto Rico rainforest
    "manhattan": (-73.985, 40.748),
    "olympic_rainforest": (-123.8, 47.8),   # WA temperate rainforest
}

GROWTH = {
    "phoenix_fringe": (-112.05, 33.55),
    "austin_nw": (-97.80, 30.40),
    "atlanta_suburbs": (-84.25, 33.95),
    "dallas_north": (-96.80, 33.05),
}

LANDSAT_SITES = {
    "central_valley_ag": (-121.2, 36.5),
    "colorado_pine": (-105.5, 39.2),
    "louisiana_wetland": (-90.0, 29.5),
    "texas_hill_country": (-98.5, 30.0),
    "cascades_clearcut": (-122.0, 44.5),
}


def landsat_sr_collection(geom, start, end):
    """Merge L5/L7/L8/L9 Collection 2 SR with harmonized band names."""

    def prep5(img):
        img = ee.Image(img)
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        optical = img.select(["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]).multiply(0.0000275).add(-0.2)
        optical = optical.rename(["blue", "green", "red", "nir", "swir1", "swir2"])
        return optical.updateMask(clear).copyProperties(img, ["system:time_start"])

    def prep8(img):
        img = ee.Image(img)
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        optical = img.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]).multiply(0.0000275).add(-0.2)
        optical = optical.rename(["blue", "green", "red", "nir", "swir1", "swir2"])
        return optical.updateMask(clear).copyProperties(img, ["system:time_start"])

    l5 = (
        ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        .filterBounds(geom)
        .filterDate(start, end)
        .map(prep5)
    )
    l7 = (
        ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        .filterBounds(geom)
        .filterDate(start, end)
        .map(prep5)
    )
    l8 = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(geom)
        .filterDate(start, end)
        .map(prep8)
    )
    l9 = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(geom)
        .filterDate(start, end)
        .map(prep8)
    )
    return l5.merge(l7).merge(l8).merge(l9)


def add_indices(img):
    img = ee.Image(img)
    ndvi = img.normalizedDifference(["nir", "red"]).rename("NDVI")
    ndwi = img.normalizedDifference(["green", "nir"]).rename("NDWI")
    nbr = img.normalizedDifference(["nir", "swir2"]).rename("NBR")
    t = img.metadata("system:time_start").divide(1000 * 60 * 60 * 24 * 365.25)
    # year since 1970 for linearFit
    year = ee.Image(t).rename("t")
    return img.addBands([ndvi, ndwi, nbr, year])


def probe_landsat_trends():
    for name, (lng, lat) in LANDSAT_SITES.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(3000)
        col = landsat_sr_collection(geom, "1985-01-01", "2024-12-31").map(add_indices)
        # Annual medians for stability
        years = ee.List.sequence(1985, 2024)

        def annual(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = start.advance(1, "year")
            med = col.filterDate(start, end).select(["NDVI", "NDWI", "NBR"]).median()
            # attach t = year for linearFit stack
            return med.addBands(ee.Image.constant(y).rename("t").float()).set("year", y)

        annual_col = ee.ImageCollection(years.map(annual))

        # linearFit: independent = t, dependent = index
        for band in ["NDVI", "NDWI", "NBR"]:
            stacked = annual_col.select(["t", band])
            fit = stacked.reduce(ee.Reducer.linearFit())
            ok, info = gi(
                fit.reduceRegion(
                    ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True
                ),
                f"landsat_linfit_{name}_{band}",
            )
            record(
                f"landsat_linfit_{name}_{band}",
                "landsat_trend",
                ok,
                info if ok else info,
                note="slope=change per year from annual medians 1985-2024",
                lat=lat,
                lng=lng,
            )

        # Thiel-Sen via sensSlope reducer if available
        try:
            for band in ["NDVI", "NBR"]:
                # need collection of single-band images with time
                def pack(img):
                    img = ee.Image(img)
                    return img.select(band).addBands(img.select("t")).rename(["y", "t"])

                packed = annual_col.map(pack)
                # sensSlope expects independent first? Docs: Reducer.sensSlope() on ImageCollection
                # with bands [independent, dependent] — check: actually sensSlope uses first band as
                # independent variable. So order t, y.
                packed2 = annual_col.select(["t", band])
                sen = packed2.reduce(ee.Reducer.sensSlope())
                ok, info = gi(
                    sen.reduceRegion(
                        ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True
                    ),
                    f"landsat_sens_{name}_{band}",
                )
                record(
                    f"landsat_sensSlope_{name}_{band}",
                    "landsat_trend",
                    ok,
                    info if ok else info,
                    note="Thiel-Sen slope if reducer available",
                    lat=lat,
                    lng=lng,
                )
        except Exception as e:  # noqa: BLE001
            record(
                f"landsat_sensSlope_{name}",
                "landsat_trend",
                False,
                str(e)[:300],
                note="sensSlope unavailable or failed",
                lat=lat,
                lng=lng,
            )

        # Breakpoint proxy: slope early (1985-2004) vs late (2005-2024)
        early = annual_col.filter(ee.Filter.lte("year", 2004)).select(["t", "NDVI"])
        late = annual_col.filter(ee.Filter.gte("year", 2005)).select(["t", "NDVI"])
        fit_e = early.reduce(ee.Reducer.linearFit())
        fit_l = late.reduce(ee.Reducer.linearFit())
        ok_e, e_info = gi(
            fit_e.reduceRegion(ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True)
        )
        ok_l, l_info = gi(
            fit_l.reduceRegion(ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True)
        )
        delta = None
        if ok_e and ok_l and e_info and l_info:
            try:
                delta = (l_info.get("scale") or 0) - (e_info.get("scale") or 0)
            except Exception:  # noqa: BLE001
                delta = None
        record(
            f"landsat_breakpoint_ndvi_{name}",
            "landsat_breakpoint",
            ok_e and ok_l,
            {"early_1985_2004": e_info, "late_2005_2024": l_info, "slope_delta": delta},
            note="year-window breakpoint proxy: late slope minus early slope",
            lat=lat,
            lng=lng,
        )

        # Thumb: NDVI slope viz
        fit_ndvi = annual_col.select(["t", "NDVI"]).reduce(ee.Reducer.linearFit())
        vis = fit_ndvi.select("scale").visualize(
            min=-0.01, max=0.01, palette=["#7f1d1d", "#fef3c7", "#14532d"]
        )
        thumb = save_thumb(f"landsat_ndvi_slope_{name}", vis, geom.bounds())
        results[-1]["thumb"] = thumb


def probe_sentinel2_phenology():
    sites = {
        "iowa_corn": BIOMES["iowa_corn"],
        "sonoran": BIOMES["sonoran_desert"],
        "atlanta": GROWTH["atlanta_suburbs"],
    }
    for name, (lng, lat) in sites.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(1500)
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(pt)
            .filterDate("2019-01-01", "2024-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
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
            cs_img = ee.Image(img.get("cs"))
            clear = ee.Image(cs_img).select("cs").gte(0.55)
            ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
            t = ee.Date(img.get("system:time_start"))
            doy = t.getRelative("day", "year").add(1)
            # harmonic terms
            w = doy.multiply(2 * math.pi / 365.25)
            cos = ee.Image.constant(w.cos()).rename("cos")
            sin = ee.Image.constant(w.sin()).rename("sin")
            ones = ee.Image.constant(1).rename("constant")
            return (
                ndvi.updateMask(clear)
                .addBands([ones, cos, sin])
                .copyProperties(img, ["system:time_start"])
                .set("doy", doy)
            )

        ndvi_col = ee.ImageCollection(joined).map(add_ndvi)

        # Harmonic regression: ndvi ~ constant + cos + sin
        # linearRegression with 3 independents
        independents = ee.List(["constant", "cos", "sin"])
        dependent = ee.String("ndvi")
        regressors = ndvi_col.select(independents.add(dependent))
        # flatten to array image for regression
        # Use reduce linearRegression
        fit = regressors.reduce(ee.Reducer.linearRegression(3, 1))
        coef = fit.select("coefficients").arrayProject([0]).arrayFlatten([independents])
        # amplitude = sqrt(cos^2 + sin^2)
        amp = coef.select("cos").pow(2).add(coef.select("sin").pow(2)).sqrt().rename("amp")
        # phase / day of peak: atan2(sin, cos) -> day
        # peak NDVI when cos*cos(w) + sin*sin(w) max => w = atan2(sin, cos)
        phase = coef.select("sin").atan2(coef.select("cos")).rename("phase")
        # convert phase (radians) to DOY: phase * 365.25 / (2pi)
        doy_peak = phase.multiply(365.25 / (2 * math.pi)).mod(365.25).rename("doy_peak")
        # handle negative
        doy_peak = doy_peak.where(doy_peak.lt(0), doy_peak.add(365.25))

        ok_a, a_info = gi(
            amp.reduceRegion(ee.Reducer.mean(), geom, 40, maxPixels=1e8, bestEffort=True),
            f"s2_amp_{name}",
        )
        ok_d, d_info = gi(
            doy_peak.reduceRegion(ee.Reducer.mean(), geom, 40, maxPixels=1e8, bestEffort=True),
            f"s2_doy_{name}",
        )
        ok_c, c_info = gi(
            coef.reduceRegion(ee.Reducer.mean(), geom, 40, maxPixels=1e8, bestEffort=True),
            f"s2_coef_{name}",
        )
        vis = amp.visualize(min=0, max=0.4, palette=["#0c4a6e", "#fde047", "#16a34a"])
        thumb = save_thumb(f"s2_seasonal_amp_{name}", vis, geom.bounds())
        record(
            f"s2_harmonic_phenology_{name}",
            "sentinel2_phenology",
            ok_a and ok_d,
            {
                "amplitude": a_info if ok_a else a_info,
                "doy_peak": d_info if ok_d else d_info,
                "coefs": c_info if ok_c else c_info,
            },
            thumb,
            note="Cloud Score+ masked harmonic fit 2019-2024; amp + day-of-peak greenness",
            lat=lat,
            lng=lng,
        )

        # Monthly mean array 2023 for sanity
        months = ee.List.sequence(1, 12)

        def month_mean(m):
            m = ee.Number(m)
            start = ee.Date.fromYMD(2023, m, 1)
            end = start.advance(1, "month")
            img = ndvi_col.filterDate(start, end).select("ndvi").mean()
            d = img.reduceRegion(ee.Reducer.mean(), geom, 40, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"month": m, "ndvi": d.get("ndvi")})

        ok, series = gi(ee.FeatureCollection(months.map(month_mean)), f"s2_monthly_{name}")
        record(
            f"s2_monthly_2023_{name}",
            "sentinel2_phenology",
            ok,
            series if ok else series,
            note="monthly NDVI 2023 with Cloud Score+",
            lat=lat,
            lng=lng,
        )


def probe_modis_biomes():
    for name, (lng, lat) in BIOMES.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(5000)

        # MOD13Q1 NDVI 16-day
        ndvi = (
            ee.ImageCollection("MODIS/061/MOD13Q1")
            .filterBounds(pt)
            .filterDate("2001-01-01", "2024-12-31")
            .select("NDVI")
        )
        # Monthly means across all years → climatology, and 2023 curve
        months = ee.List.sequence(1, 12)

        def month_clim(m):
            m = ee.Number(m)
            # all years this month
            filt = ndvi.filter(ee.Filter.calendarRange(m, m, "month"))
            img = filt.mean().multiply(0.0001)  # scale
            d = img.reduceRegion(ee.Reducer.mean(), geom, 250, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"month": m, "ndvi": d.get("NDVI")})

        def month_2023(m):
            m = ee.Number(m)
            start = ee.Date.fromYMD(2023, m, 1)
            end = start.advance(1, "month")
            img = ndvi.filterDate(start, end).mean().multiply(0.0001)
            d = img.reduceRegion(ee.Reducer.mean(), geom, 250, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"month": m, "ndvi": d.get("NDVI")})

        ok1, clim = gi(ee.FeatureCollection(months.map(month_clim)), f"modis_clim_{name}")
        ok2, y23 = gi(ee.FeatureCollection(months.map(month_2023)), f"modis_2023_{name}")

        # MOD11A2 LST day
        lst = (
            ee.ImageCollection("MODIS/061/MOD11A2")
            .filterBounds(pt)
            .filterDate("2001-01-01", "2024-12-31")
            .select("LST_Day_1km")
        )

        def month_lst(m):
            m = ee.Number(m)
            filt = lst.filter(ee.Filter.calendarRange(m, m, "month"))
            img = filt.mean().multiply(0.02).subtract(273.15)  # C
            d = img.reduceRegion(ee.Reducer.mean(), geom, 1000, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"month": m, "lst_c": d.get("LST_Day_1km")})

        ok3, lst_clim = gi(ee.FeatureCollection(months.map(month_lst)), f"modis_lst_{name}")

        # long-term NDVI linearFit on annual means
        years = ee.List.sequence(2001, 2024)

        def ann(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = start.advance(1, "year")
            med = ndvi.filterDate(start, end).mean().multiply(0.0001).rename("NDVI")
            return med.addBands(ee.Image.constant(y).rename("t").float()).set("year", y)

        fit = ee.ImageCollection(years.map(ann)).select(["t", "NDVI"]).reduce(ee.Reducer.linearFit())
        ok4, slope = gi(
            fit.reduceRegion(ee.Reducer.mean(), geom, 250, maxPixels=1e7, bestEffort=True),
            f"modis_slope_{name}",
        )

        vis = (
            ndvi.filterDate("2023-01-01", "2024-01-01")
            .mean()
            .multiply(0.0001)
            .visualize(min=0, max=0.8, palette=["#78350f", "#fde047", "#166534"])
        )
        thumb = save_thumb(f"modis_ndvi_2023_{name}", vis, geom.bounds())
        record(
            f"modis_biome_curves_{name}",
            "modis_biome",
            ok1 and ok3,
            {
                "ndvi_climatology": clim if ok1 else clim,
                "ndvi_2023": y23 if ok2 else y23,
                "lst_climatology_c": lst_clim if ok3 else lst_clim,
                "ndvi_annual_slope_2001_2024": slope if ok4 else slope,
            },
            thumb,
            note="MOD13Q1 + MOD11A2 monthly arrays for biome contrast",
            lat=lat,
            lng=lng,
        )


def jrc_water_freq(start_y, end_y):
    """Mean water detection frequency from JRC MonthlyHistory; unmask(0)."""
    col = (
        ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")
        .filterDate(f"{start_y}-01-01", f"{end_y}-12-31")
    )

    def water_bit(img):
        # 0=no data, 1=not water, 2=water
        return img.eq(2).unmask(0).rename("water")

    # frequency = mean of water detections among valid observations
    # Proper approach: water count / valid count; unmask(0) on water
    water = col.map(lambda img: img.eq(2).rename("w").unmask(0))
    valid = col.map(lambda img: img.gt(0).rename("v").unmask(0))
    freq = water.sum().divide(valid.sum().max(1)).rename("freq").unmask(0)
    return freq


def probe_jrc_weird_rising():
    # Decade freqs
    early = jrc_water_freq(1984, 1993)
    late = jrc_water_freq(2014, 2021)  # GSW1_4 MonthlyHistory ends ~2021
    delta = late.subtract(early).rename("d_freq").unmask(0)

    # Candidate regions across US (avoid only Galveston)
    candidates = {
        "salton_sea_south": (-115.8, 33.1),
        "lake_mead": (-114.4, 36.1),
        "louisiana_delta": (-89.5, 29.3),
        "florida_everglades": (-80.8, 25.6),
        "great_salt_lake": (-112.5, 41.1),
        "chesapeake": (-76.3, 38.8),
        "columbia_gorge": (-121.2, 45.7),
        "plains_playa_tx": (-102.0, 33.5),
        "minnesota_lakes": (-94.0, 47.0),
        "sacramento_delta": (-121.6, 38.1),
        "cape_hatteras": (-75.6, 35.2),
        "mobile_bay": (-88.0, 30.5),
        "puerto_rico_coast": (-66.1, 18.45),
        "nevada_reservoir": (-119.0, 39.3),  # Lahontan-ish
        "arizona_ag_canals": (-114.7, 32.7),  # Yuma
        "north_dakota_bakken": (-103.0, 48.0),
        "ohio_river_paducah": (-88.6, 37.1),
        "galveston_control": (-94.8, 29.3),
    }

    scores = []
    for name, (lng, lat) in candidates.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(8000)
        ok, info = gi(
            delta.reduceRegion(
                ee.Reducer.percentile([50, 90, 99]),
                geom,
                90,
                maxPixels=1e8,
                bestEffort=True,
            ),
            f"jrc_delta_{name}",
        )
        ok2, mean_d = gi(
            delta.reduceRegion(ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True),
            f"jrc_mean_{name}",
        )
        ok3, late_m = gi(
            late.reduceRegion(ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True)
        )
        ok4, early_m = gi(
            early.reduceRegion(ee.Reducer.mean(), geom, 90, maxPixels=1e8, bestEffort=True)
        )
        score = None
        if ok2 and mean_d:
            score = mean_d.get("d_freq")
        scores.append(
            {
                "name": name,
                "lng": lng,
                "lat": lat,
                "delta_mean": score,
                "delta_pct": info if ok else info,
                "early_freq": early_m if ok4 else early_m,
                "late_freq": late_m if ok3 else late_m,
            }
        )
        vis = delta.visualize(min=-0.3, max=0.3, palette=["#7f1d1d", "#f5f5f4", "#0369a1"])
        thumb = save_thumb(f"jrc_delta_{name}", vis, geom.bounds())
        record(
            f"jrc_decade_delta_{name}",
            "jrc_water",
            ok2,
            scores[-1],
            thumb,
            note="JRC MonthlyHistory water freq 2014-21 minus 1984-93; unmask(0)",
            lat=lat,
            lng=lng,
        )

    # Systematic CONUS grid sample of max rising (coarse)
    # Sample every ~3 deg, extract max delta in 25km buffer
    grid_pts = []
    for lat in range(26, 49, 3):
        for lng in range(-124, -67, 3):
            grid_pts.append((lng, lat))

    # Batch as FeatureCollection for efficiency — sample max in each cell
    feats = []
    for i, (lng, lat) in enumerate(grid_pts):
        feats.append(ee.Feature(ee.Geometry.Point([lng, lat]), {"i": i, "lng": lng, "lat": lat}))
    fc = ee.FeatureCollection(feats)

    def sample_max(f):
        f = ee.Feature(f)
        geom = f.geometry().buffer(20000)
        stats = delta.reduceRegion(
            ee.Reducer.max(), geom, 300, maxPixels=1e7, bestEffort=True
        )
        return f.set({"max_d": stats.get("d_freq")})

    sampled = fc.map(sample_max)
    # get top rising
    ok, info = gi(
        sampled.sort("max_d", False).limit(15),
        "jrc_grid_top",
    )
    record(
        "jrc_conus_grid_top15_rising",
        "jrc_water",
        ok,
        info if ok else info,
        note="CONUS ~3deg grid, max decade water-freq delta in 20km buffer",
    )

    # Zoom weirdest non-Galveston from candidates + grid
    rising_sorted = sorted(
        [s for s in scores if s["delta_mean"] is not None],
        key=lambda x: x["delta_mean"],
        reverse=True,
    )
    # also declining (Lake Mead etc.)
    falling_sorted = sorted(
        [s for s in scores if s["delta_mean"] is not None],
        key=lambda x: x["delta_mean"],
    )

    for label, subset in [("rising", rising_sorted[:3]), ("falling", falling_sorted[:2])]:
        for s in subset:
            if "galveston" in s["name"] and label == "rising":
                continue
            lng, lat = s["lng"], s["lat"]
            pt = ee.Geometry.Point([lng, lat])
            geom = pt.buffer(2500)
            ok, info = gi(
                ee.Image.cat([early.rename("early"), late.rename("late"), delta]).reduceRegion(
                    ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True
                ),
                f"jrc_zoom_{s['name']}",
            )
            vis = delta.clip(geom).visualize(
                min=-0.4, max=0.4, palette=["#7f1d1d", "#fafaf9", "#0ea5e9"]
            )
            thumb = save_thumb(f"jrc_zoom_{label}_{s['name']}", vis, geom.bounds(), dims=768)
            record(
                f"jrc_zoom_{label}_{s['name']}",
                "jrc_water",
                ok,
                info if ok else info,
                thumb,
                note=f"fine-scale zoom on {label} outlier",
                lat=lat,
                lng=lng,
            )

    # If grid returned points, zoom top non-coastal-looking
    if ok and isinstance(info, dict) and "features" in info:
        for feat in info["features"][:5]:
            props = feat.get("properties", {})
            lng, lat = props.get("lng"), props.get("lat")
            mx = props.get("max_d")
            if lng is None or mx is None or mx < 0.15:
                continue
            pt = ee.Geometry.Point([lng, lat])
            geom = pt.buffer(4000)
            # find actual max pixel location via sample
            okp, sampled_pix = gi(
                delta.sample(region=geom, scale=90, numPixels=200, geometries=True),
                f"jrc_grid_sample_{lng}_{lat}",
            )
            best = None
            if okp and isinstance(sampled_pix, dict):
                feats2 = sampled_pix.get("features", [])
                feats2 = sorted(
                    feats2,
                    key=lambda f: (f.get("properties") or {}).get("d_freq") or -999,
                    reverse=True,
                )
                if feats2:
                    best = feats2[0]
            vis = delta.visualize(min=-0.3, max=0.5, palette=["#450a0a", "#fafaf9", "#0284c8"])
            thumb = save_thumb(f"jrc_grid_cell_{lng}_{lat}", vis, geom.bounds())
            record(
                f"jrc_grid_zoom_{lng}_{lat}",
                "jrc_water",
                True,
                {"max_d": mx, "best_pixel": best},
                thumb,
                note="grid hotspot zoom",
                lat=lat,
                lng=lng,
            )


def probe_dynamic_world():
    years = [2016, 2018, 2020, 2022, 2024]
    surge = []
    for name, (lng, lat) in GROWTH.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(8000)
        traj = []
        for y in years:
            col = (
                ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                .filterBounds(pt)
                .filterDate(f"{y}-01-01", f"{y}-12-31")
                .select("built")
            )
            img = col.mean()
            ok, info = gi(
                img.reduceRegion(ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True),
                f"dw_built_{name}_{y}",
            )
            val = info.get("built") if ok and isinstance(info, dict) else None
            traj.append({"year": y, "built_prob": val, "ok": ok, "raw": info if not ok else None})
            record(
                f"dw_built_{name}_{y}",
                "dynamic_world",
                ok,
                {"built_prob": val},
                note="Dynamic World mean built probability",
                lat=lat,
                lng=lng,
            )

        # delta 2016→2024
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
            d.reduceRegion(
                ee.Reducer.percentile([50, 90, 99]),
                geom,
                30,
                maxPixels=1e8,
                bestEffort=True,
            )
        )
        okm, mean_info = gi(
            d.reduceRegion(ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True)
        )
        mean_d = mean_info.get("dbuilt") if okm and mean_info else None
        surge.append({"name": name, "lng": lng, "lat": lat, "mean_dbuilt": mean_d, "pct": info if ok else info, "traj": traj})
        vis = d.visualize(min=-0.2, max=0.4, palette=["#14532d", "#fafaf9", "#b91c1c"])
        thumb = save_thumb(f"dw_built_delta_{name}", vis, geom.bounds())
        record(
            f"dw_built_surge_{name}",
            "dynamic_world",
            okm,
            surge[-1],
            thumb,
            note="built prob 2024 minus 2016",
            lat=lat,
            lng=lng,
        )

    # Zoom biggest surge at finer scale
    surge_ok = [s for s in surge if s["mean_dbuilt"] is not None]
    surge_ok.sort(key=lambda x: x["mean_dbuilt"], reverse=True)
    if surge_ok:
        top = surge_ok[0]
        lng, lat = top["lng"], top["lat"]
        pt = ee.Geometry.Point([lng, lat])
        for buf, tag in [(2000, "2km"), (500, "500m")]:
            geom = pt.buffer(buf)
            b16 = (
                ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                .filterBounds(pt)
                .filterDate("2016-01-01", "2017-01-01")
                .select(["built", "crops", "trees", "grass", "shrub_and_scrub"])
                .mean()
            )
            b24 = (
                ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                .filterBounds(pt)
                .filterDate("2024-01-01", "2025-01-01")
                .select(["built", "crops", "trees", "grass", "shrub_and_scrub"])
                .mean()
            )
            d = b24.subtract(b16)
            ok, info = gi(
                d.reduceRegion(ee.Reducer.mean(), geom, 10, maxPixels=1e8, bestEffort=True),
                f"dw_zoom_{top['name']}_{tag}",
            )
            vis = d.select("built").visualize(
                min=-0.15, max=0.5, palette=["#052e16", "#e7e5e4", "#dc2626"]
            )
            thumb = save_thumb(f"dw_zoom_{top['name']}_{tag}", vis, geom.bounds(), dims=768)
            record(
                f"dw_zoom_{top['name']}_{tag}",
                "dynamic_world",
                ok,
                info if ok else info,
                thumb,
                note=f"finest zoom on largest built surge: {top['name']}",
                lat=lat,
                lng=lng,
            )


def probe_hansen_firms():
    hansen = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")
    lossyear = hansen.select("lossyear")
    loss = hansen.select("loss")

    sites = {
        "cascades_or": (-122.0, 44.5),
        "nocal_sierra": (-120.5, 39.0),
        "appalachia_tn": (-84.0, 35.5),
        "pnw_olympic": (-123.8, 47.8),
        "southeast_ga": (-82.5, 31.5),
        "maine": (-69.0, 45.5),
    }
    for name, (lng, lat) in sites.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(25000)
        # loss fraction + mean loss year (where loss)
        ok1, loss_frac = gi(
            loss.reduceRegion(ee.Reducer.mean(), geom, 30, maxPixels=1e8, bestEffort=True)
        )
        ok2, ly = gi(
            lossyear.updateMask(loss).reduceRegion(
                ee.Reducer.frequencyHistogram(), geom, 90, maxPixels=1e8, bestEffort=True
            ),
            f"hansen_hist_{name}",
        )
        vis = lossyear.updateMask(loss).visualize(
            min=1, max=23, palette=["#fef3c7", "#f97316", "#7f1d1d"]
        )
        thumb = save_thumb(f"hansen_lossyear_{name}", vis, geom.bounds())
        record(
            f"hansen_lossyear_{name}",
            "hansen",
            ok1,
            {"loss_fraction": loss_frac if ok1 else loss_frac, "lossyear_hist": ly if ok2 else ly},
            thumb,
            note="Hansen GFC lossyear spatial pattern",
            lat=lat,
            lng=lng,
        )

    # FIRMS density
    fire_sites = {
        "socal_2020": (-118.5, 34.3),
        "oregon_2020": (-122.5, 44.2),
        "texas_panhandle": (-101.0, 35.5),
        "florida_2022": (-81.5, 27.0),
        "canada_border_mn": (-93.0, 48.5),
    }
    for name, (lng, lat) in fire_sites.items():
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(40000)
        firms = (
            ee.ImageCollection("FIRMS")
            .filterBounds(geom)
            .filterDate("2018-01-01", "2024-12-31")
        )
        ok_n, n = gi(firms.size(), f"firms_n_{name}")
        # density: count of fire pixels as points — use T21 brightness sum or point density
        # FIRMS as ImageCollection of points — reduce to count per area via presence
        # Use reprojected count: map to constant 1 and sum (each detection is an image)
        # Better: aggregate_array or just size in buffer; also heatmap via reducing
        count_img = firms.map(lambda img: img.select("T21").gt(0).unmask(0).rename("f")).sum()
        ok, info = gi(
            count_img.reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
                geom,
                1000,
                maxPixels=1e8,
                bestEffort=True,
            ),
            f"firms_dens_{name}",
        )
        vis = count_img.visualize(min=0, max=20, palette=["#1c1917", "#fbbf24", "#ef4444", "#fff"])
        thumb = save_thumb(f"firms_density_{name}", vis, geom.bounds())
        record(
            f"firms_density_{name}",
            "firms",
            ok,
            {"n_images": n if ok_n else n, "density_stats": info if ok else info},
            thumb,
            note="FIRMS 2018-2024 detection density",
            lat=lat,
            lng=lng,
        )


def probe_climate_anomalies():
    # CHIRPS precip annual anomalies vs 1981-2010 climatology
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    sites = {
        "california_cv": (-121.0, 37.0),
        "texas_hill": (-98.5, 30.0),
        "iowa": (-93.5, 42.0),
        "arizona": (-112.0, 33.5),
        "florida": (-81.5, 28.0),
        "louisiana": (-91.0, 30.5),
    }

    # Build monthly climatology is heavy; use annual precip for drought/wet years
    drought_wet_years = {
        "drought_2012": 2012,
        "drought_2021_w": 2021,  # western drought
        "wet_2019": 2019,
        "wet_2015_el_nino": 2015,
        "baseline_mean_ref": None,
    }

    # Reference: mean annual precip 1991-2020
    def annual_precip(y):
        y = ee.Number(y)
        start = ee.Date.fromYMD(y, 1, 1)
        end = start.advance(1, "year")
        return chirps.filterDate(start, end).sum().rename("precip")

    ref_years = ee.List.sequence(1991, 2020)
    ref = ee.ImageCollection(ref_years.map(annual_precip)).mean().rename("ref")

    for yname, year in [
        ("drought_2012", 2012),
        ("drought_2021", 2021),
        ("wet_2019", 2019),
        ("elnino_2015", 2015),
        ("normalish_2017", 2017),
    ]:
        ann = annual_precip(year)
        anom = ann.subtract(ref).rename("anom")
        for name, (lng, lat) in sites.items():
            pt = ee.Geometry.Point([lng, lat])
            geom = pt.buffer(20000)
            ok, info = gi(
                ee.Image.cat([ann, ref, anom]).reduceRegion(
                    ee.Reducer.mean(), geom, 5000, maxPixels=1e7, bestEffort=True
                ),
                f"chirps_{yname}_{name}",
            )
            record(
                f"chirps_{yname}_{name}",
                "chirps",
                ok,
                info if ok else info,
                note=f"CHIRPS annual precip anomaly vs 1991-2020 mean for {year}",
                lat=lat,
                lng=lng,
            )
        # one thumb per year over CA-TX swath
        region = ee.Geometry.Rectangle([-124, 25, -90, 45])
        vis = anom.visualize(min=-400, max=400, palette=["#7f1d1d", "#fafaf9", "#1d4ed8"])
        thumb = save_thumb(f"chirps_anom_{yname}", vis, region, dims=768)
        results[-1]["thumb"] = thumb

    # ERA5 monthly temperature anomaly (2m_temperature)
    # ECMWF/ERA5_LAND/MONTHLY_AGGR or ECMWF/ERA5/MONTHLY
    for yname, year in [("hot_2012", 2012), ("hot_2021", 2021), ("cool_2019", 2019)]:
        try:
            era = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
            # summer JJA
            imgs = []
            for m in [6, 7, 8]:
                imgs.append(
                    era.filterDate(f"{year}-{m:02d}-01", f"{year}-{m:02d}-28").first()
                )
            # Use mean of available
            col = era.filterDate(f"{year}-06-01", f"{year}-09-01").select("temperature_2m")
            summer = col.mean().subtract(273.15).rename("t2m_c")
            # climatology summer 1991-2020
            clim_list = []
            for y in range(1991, 2021):
                clim_list.append(
                    era.filterDate(f"{y}-06-01", f"{y}-09-01").select("temperature_2m").mean()
                )
            clim = ee.ImageCollection(clim_list).mean().subtract(273.15).rename("clim_c")
            anom = summer.subtract(clim).rename("tanom")
            for name, (lng, lat) in list(sites.items())[:4]:
                pt = ee.Geometry.Point([lng, lat])
                ok, info = gi(
                    anom.reduceRegion(
                        ee.Reducer.mean(), pt.buffer(30000), 11132, maxPixels=1e7, bestEffort=True
                    ),
                    f"era5_{yname}_{name}",
                )
                record(
                    f"era5_jja_anom_{yname}_{name}",
                    "era5",
                    ok,
                    info if ok else info,
                    note="ERA5-Land JJA 2m temp anomaly vs 1991-2020",
                    lat=lat,
                    lng=lng,
                )
            region = ee.Geometry.Rectangle([-125, 24, -66, 50])
            vis = anom.visualize(min=-3, max=3, palette=["#1d4ed8", "#fafaf9", "#b91c1c"])
            thumb = save_thumb(f"era5_jja_anom_{yname}", vis, region, dims=768)
            if results:
                results[-1]["thumb"] = thumb
        except Exception as e:  # noqa: BLE001
            record(f"era5_{yname}", "era5", False, str(e)[:400], note="ERA5 probe failed")


def probe_extra_edge_cases():
    """More iterations: Landsat NBR fire recovery, S2 vs Landsat, etc."""
    # Paradise CA fire recovery NDVI trajectory
    lng, lat = -121.62, 39.75
    pt = ee.Geometry.Point([lng, lat])
    geom = pt.buffer(5000)
    col = landsat_sr_collection(geom, "2015-01-01", "2024-12-31").map(add_indices)
    years = ee.List.sequence(2015, 2024)

    def ann_ndvi(y):
        y = ee.Number(y)
        start = ee.Date.fromYMD(y, 1, 1)
        med = col.filterDate(start, start.advance(1, "year")).select("NDVI").median()
        d = med.reduceRegion(ee.Reducer.mean(), geom, 60, maxPixels=1e7, bestEffort=True)
        return ee.Feature(None, {"year": y, "ndvi": d.get("NDVI")})

    ok, series = gi(ee.FeatureCollection(years.map(ann_ndvi)), "paradise_recovery")
    record(
        "landsat_paradise_fire_recovery_ndvi",
        "edge",
        ok,
        series if ok else series,
        note="Camp Fire 2018 — NDVI recovery curve",
        lat=lat,
        lng=lng,
    )

    # Houston sprawl NDWI/built — floodplain water year windows
    lng, lat = -95.4, 29.8
    pt = ee.Geometry.Point([lng, lat])
    geom = pt.buffer(15000)
    for label, y0, y1 in [("pre_harvey", 2015, 2016), ("harvey_2017", 2017, 2017), ("post", 2018, 2019)]:
        col = landsat_sr_collection(geom, f"{y0}-01-01", f"{y1}-12-31").map(add_indices)
        ndwi = col.select("NDWI").median()
        ok, info = gi(
            ndwi.reduceRegion(ee.Reducer.mean(), geom, 60, maxPixels=1e8, bestEffort=True)
        )
        vis = ndwi.visualize(min=-0.3, max=0.3, palette=["#78350f", "#fafaf9", "#0369a1"])
        thumb = save_thumb(f"houston_ndwi_{label}", vis, geom.bounds())
        record(
            f"houston_ndwi_{label}",
            "edge",
            ok,
            info if ok else info,
            thumb,
            note="Houston NDWI windows around Harvey",
            lat=lat,
            lng=lng,
        )

    # Attempt BFAST-ish: not available — log dead end
    try:
        _ = ee.Reducer.bfast()
        record("bfast_reducer", "dead_end", True, "exists", note="unexpected")
    except Exception as e:  # noqa: BLE001
        record(
            "bfast_reducer",
            "dead_end",
            False,
            str(e)[:200],
            note="No native BFAST in EE reducers — use year-window slope deltas instead",
        )

    # LandTrendr availability
    try:
        # ee.Algorithms.TemporalSegmentation.LandTrendr
        lt = ee.Algorithms.TemporalSegmentation.LandTrendr
        record("landtrendr_algo", "edge", True, {"callable": str(lt)[:100]}, note="LandTrendr present")
        # Try minimal run on Cascades
        lng, lat = -122.0, 44.5
        pt = ee.Geometry.Point([lng, lat])
        geom = pt.buffer(2000)
        col = landsat_sr_collection(geom, "2000-01-01", "2023-12-31").map(add_indices)
        years = ee.List.sequence(2000, 2023)

        def ann(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            med = col.filterDate(start, start.advance(1, "year")).select("NBR").median()
            return med.set("system:time_start", start.millis()).toFloat()

        annual = ee.ImageCollection(years.map(ann))
        lt_params = {
            "timeSeries": annual,
            "maxSegments": 6,
            "spikeThreshold": 0.9,
            "vertexCountOvershoot": 3,
            "preventOneYearRecovery": True,
            "recoveryThreshold": 0.25,
            "pvalThreshold": 0.05,
            "bestModelProportion": 0.75,
            "minObservationsNeeded": 6,
        }
        lt_result = ee.Algorithms.TemporalSegmentation.LandTrendr(lt_params)
        # LT output is array image
        ok, info = gi(lt_result.bandNames(), "landtrendr_bands")
        # Extract magnitude of biggest loss
        # Standard extract is complex; just confirm it runs via reduceRegion on rmse band if present
        ok2, sample = gi(
            lt_result.select(0).arrayGet([0, 0]).reduceRegion(
                ee.Reducer.mean(), geom, 90, maxPixels=1e7, bestEffort=True
            ),
            "landtrendr_sample",
        )
        record(
            "landtrendr_cascades_nbr",
            "edge",
            ok,
            {"bandNames": info if ok else info, "sample": sample if ok2 else sample},
            note="LandTrendr on annual NBR — breakpoint segmentation",
            lat=lat,
            lng=lng,
        )
    except Exception as e:  # noqa: BLE001
        record("landtrendr_algo", "dead_end", False, str(e)[:400], note="LandTrendr failed")

    # S2 Cloud Score+ join failure modes — mismatched index
    try:
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate("2020-01-01", "2020-01-05").limit(3)
        cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED").filterDate("2020-06-01", "2020-06-05").limit(3)
        joined = ee.Join.saveFirst("cs").apply(
            s2, cs, ee.Filter.equals(leftField="system:index", rightField="system:index")
        )
        ok, n = gi(ee.ImageCollection(joined).size())
        record(
            "s2_cs_join_mismatch_dates",
            "dead_end",
            ok,
            {"joined_size": n if ok else n},
            note="Join across non-overlapping dates — expect empty/null cs props",
        )
    except Exception as e:  # noqa: BLE001
        record("s2_cs_join_mismatch_dates", "dead_end", False, str(e)[:300])


def main():
    LOG.write_text(f"start {datetime.now(timezone.utc).isoformat()}\n")
    init()
    print("=== Deep timeseries exploration ===", flush=True)

    probes = [
        ("landsat", probe_landsat_trends),
        ("sentinel2", probe_sentinel2_phenology),
        ("modis", probe_modis_biomes),
        ("jrc", probe_jrc_weird_rising),
        ("dynamic_world", probe_dynamic_world),
        ("hansen_firms", probe_hansen_firms),
        ("climate", probe_climate_anomalies),
        ("edge", probe_extra_edge_cases),
    ]
    for label, fn in probes:
        print(f"\n--- {label} ---", flush=True)
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            with LOG.open("a") as f:
                f.write(f"PROBE CRASH {label}: {e}\n{traceback.format_exc()}\n")
            record(f"PROBE_CRASH_{label}", "crash", False, str(e)[:500])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_probes": len(results),
        "n_ok": sum(1 for r in results if r["ok"]),
        "n_fail": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWrote {OUT} ({summary['n_probes']} probes, {summary['n_ok']} ok, {summary['n_fail']} fail)", flush=True)


if __name__ == "__main__":
    main()
