#!/usr/bin/env python3
"""Probe EE signals that map to Can-You-Build-Here resource bars."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
OUT = Path(__file__).resolve().parent / "build_site_probe.json"
THUMB_DIR = Path(__file__).resolve().parent / "build_thumbs"

# Project cards from Earth Engine Integrator chat — different loadouts.
SITES = [
    {
        "id": "ashburn_dc_alley",
        "label": "Ashburn VA — data-center alley",
        "project": "data_center",
        "lat": 39.0438,
        "lng": -77.4874,
        "expect": "Neighbors/built high; Power story for Mireye; heat maybe elevated",
    },
    {
        "id": "midland_empty",
        "label": "Midland TX periphery — empty pad fantasy",
        "project": "solar",
        "lat": 31.8457,
        "lng": -102.3676,
        "expect": "Low built; dry; ground flat-ish; water creep low",
    },
    {
        "id": "san_leon_rising",
        "label": "San Leon TX — waterline creep kill",
        "project": "warehouse",
        "lat": 29.475732110989398,
        "lng": -94.96653315875905,
        "expect": "Water bar should fail hard despite pretty coastal vibes",
    },
    {
        "id": "round_rock_suburb",
        "label": "Round Rock TX — 3-story house",
        "project": "house",
        "lat": 30.5083,
        "lng": -97.6789,
        "expect": "Mostly clear ground/water; suburban built neighbors",
    },
    {
        "id": "quincy_wa_datahub",
        "label": "Quincy WA — hyperscale cluster",
        "project": "data_center",
        "lat": 47.2343,
        "lng": -119.8525,
        "expect": "Irrigation ag neighbors; dry climate; DC competition signal",
    },
    {
        "id": "miami_coast_pretty",
        "label": "North Miami beach-adjacent — pretty trap",
        "project": "apartment",
        "lat": 25.8910,
        "lng": -80.1450,
        "expect": "Looks buildable; water + heat pressure",
    },
]


def safe_getinfo(obj, default=None):
    try:
        return obj.getInfo()
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)[:240]} if default is None else default


def mean_in(img: ee.Image, geom: ee.Geometry, scale: int, band: str | None = None):
    src = img.select(band) if band else img
    d = src.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale,
        maxPixels=1e7,
        bestEffort=True,
    )
    info = safe_getinfo(d, {})
    if isinstance(info, dict) and "_error" in info:
        return None, info["_error"]
    key = band or src.bandNames().getInfo()[0]
    val = info.get(key) if isinstance(info, dict) else None
    return val, None


def pct_in(img: ee.Image, geom: ee.Geometry, scale: int, band: str):
    d = img.select(band).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale,
        maxPixels=1e7,
        bestEffort=True,
    )
    info = safe_getinfo(d, {})
    if isinstance(info, dict) and "_error" in info:
        return None, info["_error"]
    return info.get(band), None


def dw_class_means(start: str, end: str, geom: ee.Geometry):
    """Mean Dynamic World probabilities for built/bare/water/trees/crops."""
    col = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(geom)
        .filterDate(start, end)
        .select(["built", "bare", "water", "trees", "crops", "grass"])
    )
    n = safe_getinfo(col.size(), 0)
    if isinstance(n, dict):
        return {"_error": n.get("_error"), "n": 0}
    if not n:
        return {"n": 0}
    img = col.mean()
    d = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=30,
        maxPixels=1e7,
        bestEffort=True,
    )
    info = safe_getinfo(d, {})
    if isinstance(info, dict) and "_error" in info:
        return {"n": n, "_error": info["_error"]}
    out = {"n": int(n)}
    for k in ("built", "bare", "water", "trees", "crops", "grass"):
        v = info.get(k)
        out[k] = round(float(v), 4) if v is not None else None
    return out


def jrc_water(geom: ee.Geometry):
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    occ, e1 = pct_in(gsw, geom, 30, "occurrence")
    chg, e2 = pct_in(gsw, geom, 30, "change_abs")
    season, e3 = pct_in(gsw, geom, 30, "seasonality")

    hist = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory").filterBounds(geom)

    def water_freq(year_start: int, year_end: int):
        sub = hist.filterDate(f"{year_start}-01-01", f"{year_end}-12-31")
        # water=2 in MonthlyHistory
        water = sub.map(lambda img: img.eq(2))
        n = water.size()
        freq = ee.ImageCollection(water).sum().divide(n).rename("freq")
        val, err = mean_in(freq, geom, 30, "freq")
        return {
            "freq": round(float(val), 4) if val is not None else None,
            "months": safe_getinfo(n, None),
            "error": err,
        }

    early = water_freq(1985, 1995)
    late = water_freq(2015, 2021)
    creep = None
    if early.get("freq") is not None and late.get("freq") is not None:
        creep = round(late["freq"] - early["freq"], 4)

    return {
        "occurrence_pct": round(float(occ), 2) if occ is not None else None,
        "change_abs": round(float(chg), 2) if chg is not None else None,
        "seasonality": round(float(season), 2) if season is not None else None,
        "freq_1985_1995": early,
        "freq_2015_2021": late,
        "waterline_creep": creep,
        "errors": [e for e in (e1, e2, e3) if e],
    }


def terrain(geom: ee.Geometry):
    dem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    slope = ee.Terrain.slope(dem)
    elev, e1 = mean_in(dem, geom, 30, "elevation")
    sl, e2 = mean_in(slope, geom, 30, "slope")
    # FABDEM if available
    fab = None
    fab_err = None
    try:
        fabdem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("fab")
        fab, fab_err = mean_in(fabdem, geom, 30, "fab")
    except Exception as e:  # noqa: BLE001
        fab_err = str(e)[:200]
    return {
        "nasadem_m": round(float(elev), 2) if elev is not None else None,
        "slope_deg": round(float(sl), 2) if sl is not None else None,
        "fabdem_m": round(float(fab), 2) if fab is not None else None,
        "errors": [e for e in (e1, e2, fab_err) if e],
    }


def summer_lst_c(geom: ee.Geometry, year: int = 2024):
    col = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(geom)
        .filterDate(f"{year}-06-01", f"{year}-08-31")
        .select("LST_Day_1km")
    )
    n = safe_getinfo(col.size(), 0)
    if not n or isinstance(n, dict):
        return {"n": 0, "lst_c": None}
    lst_k = col.mean().multiply(0.02)
    lst_c = lst_k.subtract(273.15).rename("lst_c")
    # local rural-ish baseline: 15 km ring mean
    ring = geom.buffer(15000).difference(geom.buffer(2000), 1)
    site_v, e1 = mean_in(lst_c, geom.buffer(500), 1000, "lst_c")
    base_v, e2 = mean_in(lst_c, ring, 1000, "lst_c")
    anom = None
    if site_v is not None and base_v is not None:
        anom = round(float(site_v) - float(base_v), 2)
    return {
        "n": int(n) if isinstance(n, int) else n,
        "lst_c": round(float(site_v), 2) if site_v is not None else None,
        "ring_lst_c": round(float(base_v), 2) if base_v is not None else None,
        "uhi_anom_c": anom,
        "errors": [e for e in (e1, e2) if e],
    }


def hansen_loss(geom: ee.Geometry):
    img = ee.Image("UMD/hansen/global_forest_change_2024_v1_12")
    loss = img.select("loss")
    treecover = img.select("treecover2000")
    lossyear = img.select("lossyear")
    # fraction of buffer that lost forest
    loss_m, e1 = mean_in(loss, geom, 30, "loss")
    tc_m, e2 = mean_in(treecover, geom, 30, "treecover2000")
    # mean loss year where loss==1
    ly = lossyear.updateMask(loss.eq(1))
    ly_m, e3 = mean_in(ly, geom, 30, "lossyear")
    return {
        "loss_fraction": round(float(loss_m), 4) if loss_m is not None else None,
        "treecover2000_pct": round(float(tc_m), 2) if tc_m is not None else None,
        "mean_lossyear": round(float(ly_m), 1) if ly_m is not None else None,
        "errors": [e for e in (e1, e2, e3) if e],
    }


def score_bars(project: str, ee_pack: dict) -> dict:
    """Map EE metrics → rough 0-100 resource bars (demo heuristics, not underwriting)."""
    water = ee_pack["water"]
    terr = ee_pack["terrain"]
    heat = ee_pack["heat"]
    dw_recent = ee_pack["dw_recent"]
    dw_old = ee_pack["dw_old"]
    hansen = ee_pack["hansen"]

    # Water bar: high occurrence / positive creep hurts
    occ = water.get("occurrence_pct") or 0
    creep = water.get("waterline_creep") or 0
    water_score = max(0, 100 - occ * 1.2 - max(0, creep) * 800)
    if occ > 20 or creep > 0.02:
        water_flag = "KILL"
    elif occ > 8 or creep > 0.01:
        water_flag = "HOLD"
    else:
        water_flag = "OK"

    # Ground: slope
    slope = terr.get("slope_deg") or 0
    ground_score = max(0, 100 - slope * 8)
    ground_flag = "KILL" if slope > 12 else ("HOLD" if slope > 6 else "OK")

    # Heat
    anom = heat.get("uhi_anom_c")
    lst = heat.get("lst_c")
    heat_score = 70
    if anom is not None:
        heat_score = max(0, 100 - max(0, anom) * 12)
    heat_flag = "HOLD" if (anom is not None and anom > 3) or (lst is not None and lst > 45) else "OK"

    # Neighbors: recent built surge (competition / already paved)
    built_r = (dw_recent or {}).get("built") or 0
    built_o = (dw_old or {}).get("built") or 0
    bare_r = (dw_recent or {}).get("bare") or 0
    built_delta = built_r - built_o
    neighbors_score = max(0, 100 - built_r * 120 - max(0, built_delta) * 200)
    # For data centers, high built nearby can mean interconnect competition (bad) OR proven cluster (mixed)
    if project == "data_center":
        neighbors_flag = "HOLD" if built_r > 0.25 or built_delta > 0.08 else "OK"
    else:
        neighbors_flag = "HOLD" if bare_r > 0.25 and built_delta > 0.05 else "OK"

    # Dirt / disturbance
    dirt_score = max(0, 100 - bare_r * 150)
    dirt_flag = "HOLD" if bare_r > 0.2 else "OK"

    # Trees cleared
    loss_f = hansen.get("loss_fraction") or 0
    trees_score = max(0, 100 - loss_f * 200)
    trees_flag = "HOLD" if loss_f > 0.15 else "OK"

    bars = {
        "water": {"score": round(water_score, 1), "flag": water_flag},
        "ground": {"score": round(ground_score, 1), "flag": ground_flag},
        "heat": {"score": round(heat_score, 1), "flag": heat_flag},
        "neighbors": {"score": round(neighbors_score, 1), "flag": neighbors_flag, "built_delta": round(built_delta, 4)},
        "dirt": {"score": round(dirt_score, 1), "flag": dirt_flag},
        "trees": {"score": round(trees_score, 1), "flag": trees_flag},
    }

    # Project-weighted decision
    weights = {
        "data_center": {"water": 1.2, "ground": 0.8, "heat": 1.0, "neighbors": 1.3, "dirt": 0.7, "trees": 0.4},
        "solar": {"water": 0.8, "ground": 1.2, "heat": 0.6, "neighbors": 0.7, "dirt": 0.5, "trees": 0.5},
        "warehouse": {"water": 1.3, "ground": 1.0, "heat": 0.7, "neighbors": 0.8, "dirt": 0.8, "trees": 0.4},
        "house": {"water": 1.4, "ground": 1.0, "heat": 0.9, "neighbors": 0.5, "dirt": 0.6, "trees": 0.6},
        "apartment": {"water": 1.5, "ground": 0.9, "heat": 1.0, "neighbors": 0.6, "dirt": 0.6, "trees": 0.5},
    }[project]

    # Kill if any critical flag
    critical = []
    if bars["water"]["flag"] == "KILL":
        critical.append("waterline/occurrence")
    if bars["ground"]["flag"] == "KILL":
        critical.append("slope")

    if critical:
        decision = "SITE_KILLED"
    elif any(bars[k]["flag"] == "HOLD" for k in bars):
        decision = "HOLD"
    else:
        decision = "CLEAR_TO_BUILD"

    # Weighted score
    total_w = sum(weights.values())
    composite = sum(bars[k]["score"] * weights[k] for k in weights) / total_w

    return {
        "bars": bars,
        "composite": round(composite, 1),
        "decision": decision,
        "critical": critical,
        "weights": weights,
    }


def write_thumb(site_id: str, lat: float, lng: float):
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    pt = ee.Geometry.Point([lng, lat])
    region = pt.buffer(2500).bounds()
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("change_abs")
    vis = gsw.visualize(min=0, max=40, palette=["#0b1020", "#2dd4bf", "#facc15", "#ef4444"])
    url = vis.getThumbURL({"region": region, "dimensions": 512, "format": "png"})
    import urllib.request

    path = THUMB_DIR / f"{site_id}_gsw_change.png"
    urllib.request.urlretrieve(url, path)
    return str(path)


def probe_site(site: dict) -> dict:
    pt = ee.Geometry.Point([site["lng"], site["lat"]])
    buf = pt.buffer(400)  # ~parcel-ish
    print(f"… {site['id']}", flush=True)

    water = jrc_water(buf)
    terr = terrain(buf)
    heat = summer_lst_c(pt)
    dw_recent = dw_class_means("2023-01-01", "2024-12-31", buf)
    dw_old = dw_class_means("2016-01-01", "2018-12-31", buf)
    hansen = hansen_loss(buf)

    ee_pack = {
        "water": water,
        "terrain": terr,
        "heat": heat,
        "dw_recent": dw_recent,
        "dw_old": dw_old,
        "hansen": hansen,
    }
    scored = score_bars(site["project"], ee_pack)

    thumb = None
    try:
        thumb = write_thumb(site["id"], site["lat"], site["lng"])
    except Exception as e:  # noqa: BLE001
        thumb = f"thumb_error: {e}"

    return {
        **site,
        "ee": ee_pack,
        "score": scored,
        "thumb": thumb,
    }


def main():
    ee.Initialize(project=PROJECT)
    results = []
    for site in SITES:
        try:
            results.append(probe_site(site))
        except Exception as e:  # noqa: BLE001
            results.append({**site, "error": str(e)[:400]})

    payload = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT,
        "idea": "Can You Build Here / Plotcraft — EE resource bars for GO/HOLD/KILL",
        "sites": results,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT}")

    # compact table
    print("\n=== DECISIONS ===")
    for r in results:
        if "error" in r:
            print(r["id"], "ERROR", r["error"][:120])
            continue
        s = r["score"]
        w = r["ee"]["water"]
        print(
            f"{r['id']:22} {r['project']:12} {s['decision']:14} "
            f"comp={s['composite']:5} water_occ={w.get('occurrence_pct')} "
            f"creep={w.get('waterline_creep')} slope={r['ee']['terrain'].get('slope_deg')} "
            f"builtΔ={s['bars']['neighbors'].get('built_delta')}"
        )


if __name__ == "__main__":
    main()
