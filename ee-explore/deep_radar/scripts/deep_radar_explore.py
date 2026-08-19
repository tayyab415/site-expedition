#!/usr/bin/env python3
"""Open-ended Sentinel-1 / SAR deep exploration on Google Earth Engine."""

from __future__ import annotations

import json
import math
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import ee
import requests

OUT = Path("/home/tayyabkhan/Shared/mireye-challenge/ee-explore/deep_radar")
THUMBS = OUT / "thumbs"
LOG_PATH = OUT / "logs" / "experiments.json"
SUMMARY_PATH = OUT / "FINDINGS.md"

ee.Initialize(project="gen-lang-client-0261050164")

# --- Sites ---
GALVESTON = ee.Geometry.Rectangle([-95.15, 29.15, -94.70, 29.45])
GALVESTON_PT = ee.Geometry.Point([-94.80, 29.30])
# Port of Houston / Galveston Ship Channel
PORT_HOUSTON = ee.Geometry.Rectangle([-95.25, 29.60, -94.95, 29.80])
# Inland river flood: Houston / Buffalo Bayou during Harvey (2017)
HOUSTON_FLOOD = ee.Geometry.Rectangle([-95.65, 29.60, -95.20, 29.90])
# Mississippi River floodplain near Greenville, MS (classic inland)
MS_RIVER = ee.Geometry.Rectangle([-91.20, 33.20, -90.80, 33.55])
# Gulf shipping lane south of Galveston for ship detection
GULF_SHIPS = ee.Geometry.Rectangle([-95.10, 28.70, -94.40, 29.20])
# Downtown Houston urban
HOUSTON_URBAN = ee.Geometry.Rectangle([-95.45, 29.70, -95.30, 29.80])
# Clear Lake / water near NASA
CLEAR_LAKE = ee.Geometry.Rectangle([-95.15, 29.50, -94.95, 29.62])

experiments: list[dict] = []


def log(name: str, ok: bool, params: dict, results: dict | None = None,
        paths: list[str] | None = None, notes: str = "", error: str | None = None):
    entry = {
        "name": name,
        "ok": ok,
        "params": params,
        "results": results or {},
        "paths": paths or [],
        "notes": notes,
        "error": error,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    experiments.append(entry)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {notes[:120]}" if notes else ""))
    if error:
        print(f"       ERR: {error[:240]}")
    # incremental save
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(experiments, indent=2))


def save_thumb(img: ee.Image, region: ee.Geometry, path: Path, vis: dict,
               dims: int = 768) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    url = img.visualize(**vis).getThumbURL({
        "region": region,
        "dimensions": dims,
        "format": "png",
    })
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def reduce_stats(img: ee.Image, region: ee.Geometry, scale: int = 40,
                 bands: list[str] | None = None) -> dict:
    if bands:
        img = img.select(bands)
    d = img.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
        .combine(ee.Reducer.minMax(), sharedInputs=True)
        .combine(ee.Reducer.percentile([5, 50, 95]), sharedInputs=True),
        geometry=region,
        scale=scale,
        maxPixels=1e8,
        bestEffort=True,
    ).getInfo()
    return d or {}


def s1_vvvh(region, start, end, orbit=None, pass_dir=None):
    col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )
    if orbit is not None:
        col = col.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
    if pass_dir:
        col = col.filter(ee.Filter.eq("orbitProperties_pass", pass_dir))
    return col


def to_db_ratio(img):
    """VV/VH ratio in linear space then to dB-ish: VV_dB - VH_dB."""
    return img.select("VV").subtract(img.select("VH")).rename("VV_minus_VH")


def focal_median_speckle(img, radius=50):
    return img.focalMedian(radius, "circle", "meters").copyProperties(img, img.propertyNames())


# ---------------------------------------------------------------------------
# PROBES
# ---------------------------------------------------------------------------

def probe_catalog_loads():
    """Try loading many SAR-related collections."""
    ids = [
        "COPERNICUS/S1_GRD",
        "COPERNICUS/S1_GRD_FLOAT",
        "JAXA/ALOS/PALSAR/YEARLY/SAR",
        "JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH",
        "JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR",
        "JAXA/ALOS/PALSAR-2/Level2_1/StripMap_202401",
        "JAXA/ALOS/PALSAR/YEARLY/FNF4",
        "Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/BACKSCATTER",
        "Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/COHERENCE",
        "Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/DECAY_MODEL_PARAMETERS",
        "Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/INCIDENCE_LAYOVER_SHADOW",
        "OPERA/RTC/L2_V1/S1",
        "OPERA/RTC/L2_V1/S1_STATIC",
        "OPERA/DSWX/L3_V1/S1",
        "projects/ee-pkurelab/assets/LHScat",
        "OSU/GIMP/2000_IMAGERY_MOSAIC",
        "ASF/UAVSAR",
        "ICEYE/SAR",
        "CAPELLA/SAR",
        "NASA/NISAR/L2",
        "COPERNICUS/S1_SLC",
        "ESA/S1_SLC",
    ]
    for asset_id in ids:
        try:
            # try ImageCollection first
            try:
                col = ee.ImageCollection(asset_id)
                n = col.limit(3).size().getInfo()
                first = col.first()
                bands = first.bandNames().getInfo() if n else []
                log(
                    f"catalog_load_{asset_id.replace('/', '_')}",
                    True,
                    {"asset": asset_id, "type": "ImageCollection"},
                    {"sample_size": n, "bands": bands},
                    notes=f"Loaded IC; bands={bands}",
                )
            except ee.EEException as e1:
                if "ImageCollection" in str(e1) or "not found" in str(e1).lower() or "Expected" in str(e1):
                    img = ee.Image(asset_id)
                    bands = img.bandNames().getInfo()
                    log(
                        f"catalog_load_{asset_id.replace('/', '_')}",
                        True,
                        {"asset": asset_id, "type": "Image"},
                        {"bands": bands},
                        notes=f"Loaded as Image; bands={bands}",
                    )
                else:
                    raise
        except Exception as e:
            log(
                f"catalog_load_{asset_id.replace('/', '_')}",
                False,
                {"asset": asset_id},
                error=str(e)[:500],
                notes="Not available in public EE catalog (or wrong ID)",
            )


def probe_s1_coverage_galveston():
    try:
        col = s1_vvvh(GALVESTON, "2023-01-01", "2024-01-01")
        n = col.size().getInfo()
        asc = col.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING")).size().getInfo()
        desc = col.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING")).size().getInfo()
        orbits = col.aggregate_array("relativeOrbitNumber_start").distinct().getInfo()
        platforms = col.aggregate_histogram("platform_number").getInfo()
        log(
            "s1_coverage_galveston_2023",
            True,
            {"region": "galveston", "year": 2023},
            {
                "n_scenes": n,
                "ascending": asc,
                "descending": desc,
                "orbits": sorted(orbits) if orbits else [],
                "platforms": platforms,
            },
            notes=f"{n} IW VV+VH scenes; asc={asc} desc={desc}; orbits={orbits}",
        )
    except Exception as e:
        log("s1_coverage_galveston_2023", False, {}, error=str(e))


def probe_vv_vh_contrast():
    """Urban vs water backscatter contrast in VV and VH."""
    try:
        col = s1_vvvh(HOUSTON_URBAN.union(CLEAR_LAKE, 1), "2023-06-01", "2023-09-01")
        med = col.median()
        urban = reduce_stats(med, HOUSTON_URBAN, scale=30, bands=["VV", "VH"])
        water = reduce_stats(med, CLEAR_LAKE, scale=30, bands=["VV", "VH"])
        path = THUMBS / "galveston_area_vv_vh_rgb.png"
        # RGB: VV, VH, VV-VH
        rgb = med.addBands(to_db_ratio(med))
        save_thumb(
            rgb.select(["VV", "VH", "VV_minus_VH"]),
            ee.Geometry.Rectangle([-95.50, 29.45, -94.90, 29.85]),
            path,
            {"min": [-18, -25, 0], "max": [0, -8, 12]},
        )
        contrast = {
            "urban_VV_mean": urban.get("VV_mean"),
            "urban_VH_mean": urban.get("VH_mean"),
            "water_VV_mean": water.get("VV_mean"),
            "water_VH_mean": water.get("VH_mean"),
            "delta_VV_urban_minus_water": (urban.get("VV_mean") or 0) - (water.get("VV_mean") or 0),
            "delta_VH_urban_minus_water": (urban.get("VH_mean") or 0) - (water.get("VH_mean") or 0),
        }
        log(
            "vv_vh_urban_vs_water",
            True,
            {"dates": "2023-06..09", "urban": "houston", "water": "clear_lake"},
            {**contrast, "urban_full": urban, "water_full": water},
            [str(path)],
            notes=(
                f"Urban VV mean {contrast['urban_VV_mean']:.2f} dB vs water "
                f"{contrast['water_VV_mean']:.2f} dB; ΔVV={contrast['delta_VV_urban_minus_water']:.2f} dB"
            ),
        )
    except Exception as e:
        log("vv_vh_urban_vs_water", False, {}, error=str(e) + "\n" + traceback.format_exc()[:400])


def probe_asc_vs_desc():
    try:
        region = GALVESTON
        asc = s1_vvvh(region, "2023-01-01", "2023-12-31", pass_dir="ASCENDING").median().select("VV")
        desc = s1_vvvh(region, "2023-01-01", "2023-12-31", pass_dir="DESCENDING").median().select("VV")
        diff = asc.subtract(desc).rename("asc_minus_desc")
        sa = reduce_stats(asc, region, 40, ["VV"])
        sd = reduce_stats(desc, region, 40, ["VV"])
        sdiff = reduce_stats(diff, region, 40, ["asc_minus_desc"])
        p1 = THUMBS / "galveston_asc_VV.png"
        p2 = THUMBS / "galveston_desc_VV.png"
        p3 = THUMBS / "galveston_asc_minus_desc_VV.png"
        save_thumb(asc, region, p1, {"min": -22, "max": 0, "palette": ["000000", "00ffff", "ffffff"]})
        save_thumb(desc, region, p2, {"min": -22, "max": 0, "palette": ["000000", "00ffff", "ffffff"]})
        save_thumb(diff, region, p3, {"min": -5, "max": 5, "palette": ["0000ff", "ffffff", "ff0000"]})
        log(
            "asc_vs_desc_galveston",
            True,
            {"year": 2023},
            {"asc": sa, "desc": sd, "diff": sdiff},
            [str(p1), str(p2), str(p3)],
            notes=(
                f"Asc VV mean {sa.get('VV_mean'):.2f} vs Desc {sd.get('VV_mean'):.2f}; "
                f"mean |diff| via mean of signed={sdiff.get('asc_minus_desc_mean')}"
            ),
        )
    except Exception as e:
        log("asc_vs_desc_galveston", False, {}, error=str(e))


def probe_harvey_flood():
    """Before/after Harvey flooding over Houston."""
    try:
        before = s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20").median()
        after = s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-10").median()
        # Flood: strong VV drop (smooth water)
        change = after.select("VV").subtract(before.select("VV")).rename("dVV")
        # Simple flood mask: after VV < -16 and drop > 3 dB
        flood = after.select("VV").lt(-16).And(change.lt(-3)).rename("flood")
        flood_area = (
            flood.selfMask()
            .multiply(ee.Image.pixelArea())
            .reduceRegion(ee.Reducer.sum(), HOUSTON_FLOOD, 30, maxPixels=1e9, bestEffort=True)
            .getInfo()
        )
        bstats = reduce_stats(before, HOUSTON_FLOOD, 40, ["VV", "VH"])
        astats = reduce_stats(after, HOUSTON_FLOOD, 40, ["VV", "VH"])
        cstats = reduce_stats(change, HOUSTON_FLOOD, 40, ["dVV"])
        paths = []
        for name, img, vis in [
            ("harvey_before_VV.png", before.select("VV"), {"min": -22, "max": 0, "palette": ["000033", "00aaff", "ffffff"]}),
            ("harvey_after_VV.png", after.select("VV"), {"min": -22, "max": 0, "palette": ["000033", "00aaff", "ffffff"]}),
            ("harvey_dVV.png", change, {"min": -10, "max": 5, "palette": ["ff0000", "ffffff", "0000ff"]}),
            ("harvey_flood_mask.png", flood.selfMask(), {"min": 0, "max": 1, "palette": ["000000", "00ffff"]}),
        ]:
            p = THUMBS / name
            save_thumb(img, HOUSTON_FLOOD, p, vis)
            paths.append(str(p))
        area_m2 = flood_area.get("flood", 0) or 0
        log(
            "harvey_flood_before_after",
            True,
            {"before": "2017-07-01..08-20", "after": "2017-08-27..09-10", "mask": "VV<-16 & dVV<-3"},
            {
                "before": bstats,
                "after": astats,
                "change": cstats,
                "flood_area_m2": area_m2,
                "flood_area_km2": area_m2 / 1e6,
            },
            paths,
            notes=f"Flood mask area ≈ {area_m2/1e6:.1f} km²; mean dVV={cstats.get('dVV_mean')}",
        )
        return {"interesting": True, "flood_km2": area_m2 / 1e6, "dVV_mean": cstats.get("dVV_mean")}
    except Exception as e:
        log("harvey_flood_before_after", False, {}, error=str(e) + "\n" + traceback.format_exc()[:400])
        return None


def probe_harvey_followups(flood_info):
    """Follow-ups on Harvey flood thread."""
    # F1: VH-based flood vs VV
    try:
        before = s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20").median()
        after = s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-10").median()
        dVH = after.select("VH").subtract(before.select("VH")).rename("dVH")
        flood_vh = after.select("VH").lt(-22).And(dVH.lt(-3)).rename("flood_vh")
        flood_vv = after.select("VV").lt(-16).And(
            after.select("VV").subtract(before.select("VV")).lt(-3)
        ).rename("flood_vv")
        area_vh = flood_vh.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), HOUSTON_FLOOD, 30, maxPixels=1e9, bestEffort=True
        ).getInfo()
        area_vv = flood_vv.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), HOUSTON_FLOOD, 30, maxPixels=1e9, bestEffort=True
        ).getInfo()
        agree = flood_vv.And(flood_vh).rename("agree")
        area_agree = agree.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), HOUSTON_FLOOD, 30, maxPixels=1e9, bestEffort=True
        ).getInfo()
        p = THUMBS / "harvey_vv_vs_vh_flood.png"
        # encode: R=VV-only, G=agree, B=VH-only
        comp = (
            flood_vv.And(flood_vh.Not()).multiply(255).rename("R")
            .addBands(agree.multiply(255).rename("G"))
            .addBands(flood_vh.And(flood_vv.Not()).multiply(255).rename("B"))
        )
        save_thumb(comp, HOUSTON_FLOOD, p, {"bands": ["R", "G", "B"], "min": 0, "max": 255})
        log(
            "harvey_followup_vv_vs_vh_flood",
            True,
            {},
            {
                "vv_km2": (area_vv.get("flood_vv") or 0) / 1e6,
                "vh_km2": (area_vh.get("flood_vh") or 0) / 1e6,
                "agree_km2": (area_agree.get("agree") or 0) / 1e6,
            },
            [str(p)],
            notes="Compare VV vs VH flood masks; red=VV-only green=agree blue=VH-only",
        )
    except Exception as e:
        log("harvey_followup_vv_vs_vh_flood", False, {}, error=str(e))

    # F2: orbit-restricted change (same relative orbit)
    try:
        col_b = s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20")
        orbits = col_b.aggregate_array("relativeOrbitNumber_start").distinct().getInfo()
        best = None
        for orb in (orbits or [])[:4]:
            b = s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20", orbit=orb)
            a = s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-15", orbit=orb)
            nb, na = b.size().getInfo(), a.size().getInfo()
            if nb and na:
                d = a.median().select("VV").subtract(b.median().select("VV")).rename("dVV")
                st = reduce_stats(d, HOUSTON_FLOOD, 50, ["dVV"])
                if best is None or (st.get("dVV_mean") or 0) < (best["dVV_mean"] or 0):
                    best = {"orbit": orb, "n_before": nb, "n_after": na, **st}
        if best:
            p = THUMBS / f"harvey_orbit{best['orbit']}_dVV.png"
            d = (
                s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-15", orbit=best["orbit"]).median().select("VV")
                .subtract(
                    s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20", orbit=best["orbit"]).median().select("VV")
                )
            )
            save_thumb(d, HOUSTON_FLOOD, p, {"min": -10, "max": 5, "palette": ["ff0000", "ffffff", "0000ff"]})
            log(
                "harvey_followup_same_orbit_change",
                True,
                {"selected_orbit": best["orbit"]},
                best,
                [str(p)],
                notes=f"Best same-orbit drop on orbit {best['orbit']}: mean dVV={best.get('dVV_mean')}",
            )
        else:
            log("harvey_followup_same_orbit_change", False, {"orbits": orbits}, notes="No overlapping orbits")
    except Exception as e:
        log("harvey_followup_same_orbit_change", False, {}, error=str(e))

    # F3: ratio change VV-VH
    try:
        before = s1_vvvh(HOUSTON_FLOOD, "2017-07-01", "2017-08-20").median()
        after = s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-10").median()
        rb, ra = to_db_ratio(before), to_db_ratio(after)
        dr = ra.subtract(rb).rename("dRatio")
        st = reduce_stats(dr, HOUSTON_FLOOD, 40, ["dRatio"])
        p = THUMBS / "harvey_dRatio_VVmVH.png"
        save_thumb(dr, HOUSTON_FLOOD, p, {"min": -5, "max": 5, "palette": ["0000ff", "ffffff", "ff0000"]})
        log(
            "harvey_followup_dualpol_ratio_change",
            True,
            {},
            st,
            [str(p)],
            notes=f"Δ(VV-VH) mean={st.get('dRatio_mean')}",
        )
    except Exception as e:
        log("harvey_followup_dualpol_ratio_change", False, {}, error=str(e))

    # F4: single post-event scene vs median stack
    try:
        after_col = s1_vvvh(HOUSTON_FLOOD, "2017-08-28", "2017-09-05")
        n = after_col.size().getInfo()
        dates = after_col.aggregate_array("system:time_start").getInfo()
        date_strs = [datetime.utcfromtimestamp(t / 1000).strftime("%Y-%m-%d") for t in (dates or [])]
        if n:
            scene = ee.Image(after_col.sort("system:time_start").first())
            st = reduce_stats(scene, HOUSTON_FLOOD, 40, ["VV", "VH"])
            p = THUMBS / "harvey_single_scene_VV.png"
            save_thumb(scene.select("VV"), HOUSTON_FLOOD, p, {"min": -22, "max": 0, "palette": ["000033", "00aaff", "ffffff"]})
            log(
                "harvey_followup_single_scene",
                True,
                {"n_in_window": n, "dates": date_strs},
                st,
                [str(p)],
                notes=f"First post scene {date_strs[0] if date_strs else '?'}; VV mean={st.get('VV_mean')}",
            )
        else:
            log("harvey_followup_single_scene", False, {}, notes="No scenes in tight window")
    except Exception as e:
        log("harvey_followup_single_scene", False, {}, error=str(e))

    # F5: compare to optical cloud cover (prove SAR advantage) — just count S2 cloudy
    try:
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(HOUSTON_FLOOD)
            .filterDate("2017-08-27", "2017-09-05")
        )
        n_s2 = s2.size().getInfo()
        # mean cloud percentage
        if n_s2:
            clouds = s2.aggregate_array("CLOUDY_PIXEL_PERCENTAGE").getInfo()
            mean_cloud = sum(clouds) / len(clouds) if clouds else None
        else:
            mean_cloud = None
        n_s1 = s1_vvvh(HOUSTON_FLOOD, "2017-08-27", "2017-09-05").size().getInfo()
        log(
            "harvey_followup_s1_vs_s2_availability",
            True,
            {"window": "2017-08-27..09-05"},
            {"s2_scenes": n_s2, "s2_mean_cloud_pct": mean_cloud, "s1_scenes": n_s1},
            notes=f"S2={n_s2} scenes mean cloud={mean_cloud}; S1={n_s1} usable regardless of weather",
        )
    except Exception as e:
        log("harvey_followup_s1_vs_s2_availability", False, {}, error=str(e))


def probe_ship_detection():
    """Bright target / ship detection in Gulf of Mexico."""
    try:
        col = s1_vvvh(GULF_SHIPS, "2023-08-01", "2023-08-15", pass_dir="DESCENDING")
        n = col.size().getInfo()
        if not n:
            col = s1_vvvh(GULF_SHIPS, "2023-07-01", "2023-09-01")
            n = col.size().getInfo()
        scene = ee.Image(col.sort("system:time_start", False).first())
        vv = scene.select("VV")
        # Ships: very bright specular returns
        thr = -5  # dB
        ships = vv.gt(thr).rename("ship")
        # morph clean
        ships_clean = ships.focalMax(30, "circle", "meters").focalMin(30, "circle", "meters")
        # connected components count approx via reduce
        ship_pixels = ships_clean.selfMask().reduceRegion(
            ee.Reducer.count(), GULF_SHIPS, 10, maxPixels=1e9, bestEffort=True
        ).getInfo()
        # also p99 of VV as brightness proxy
        pctl = vv.reduceRegion(
            ee.Reducer.percentile([50, 90, 99, 99.9]), GULF_SHIPS, 20, maxPixels=1e8, bestEffort=True
        ).getInfo()
        mean_ocean = vv.reduceRegion(ee.Reducer.mean(), GULF_SHIPS, 40, maxPixels=1e8, bestEffort=True).getInfo()
        p1 = THUMBS / "gulf_ships_VV.png"
        p2 = THUMBS / "gulf_ships_mask.png"
        save_thumb(vv, GULF_SHIPS, p1, {"min": -25, "max": 0, "palette": ["000000", "0033aa", "ffff00", "ffffff"]})
        save_thumb(ships_clean.selfMask(), GULF_SHIPS, p2, {"min": 0, "max": 1, "palette": ["000000", "ff0000"]})
        props = {
            k: scene.get(k).getInfo()
            for k in ["system:time_start", "orbitProperties_pass", "relativeOrbitNumber_start", "platform_number"]
        }
        if props.get("system:time_start"):
            props["date"] = datetime.utcfromtimestamp(props["system:time_start"] / 1000).isoformat()
        log(
            "gulf_ship_bright_target",
            True,
            {"threshold_dB": thr, "n_scenes_available": n, "scene": props},
            {
                "ship_pixels_gt_thr_cleaned": ship_pixels.get("ship"),
                "vv_percentiles": pctl,
                "vv_mean_ocean": mean_ocean.get("VV"),
                "contrast_p99_minus_mean": (pctl.get("VV_p99") or 0) - (mean_ocean.get("VV") or 0),
            },
            [str(p1), str(p2)],
            notes=(
                f"Ocean VV mean={mean_ocean.get('VV')}; p99={pctl.get('VV_p99')}; "
                f"bright pixels≈{ship_pixels.get('ship')}"
            ),
        )
        return {
            "contrast": (pctl.get("VV_p99") or 0) - (mean_ocean.get("VV") or 0),
            "ship_pixels": ship_pixels.get("ship"),
            "scene_date": props.get("date"),
        }
    except Exception as e:
        log("gulf_ship_bright_target", False, {}, error=str(e) + "\n" + traceback.format_exc()[:400])
        return None


def probe_ship_followups(ship_info):
    # F1: VH ships vs VV
    try:
        col = s1_vvvh(GULF_SHIPS, "2023-07-01", "2023-09-01")
        scene = ee.Image(col.sort("system:time_start", False).first())
        vv_ships = scene.select("VV").gt(-5)
        vh_ships = scene.select("VH").gt(-12)
        only_vv = vv_ships.And(vh_ships.Not())
        both = vv_ships.And(vh_ships)
        c_vv = vv_ships.selfMask().reduceRegion(ee.Reducer.count(), GULF_SHIPS, 20, maxPixels=1e9, bestEffort=True).getInfo()
        c_vh = vh_ships.selfMask().reduceRegion(ee.Reducer.count(), GULF_SHIPS, 20, maxPixels=1e9, bestEffort=True).getInfo()
        c_both = both.selfMask().reduceRegion(ee.Reducer.count(), GULF_SHIPS, 20, maxPixels=1e9, bestEffort=True).getInfo()
        p = THUMBS / "gulf_ships_VV_vs_VH.png"
        rgb = (
            only_vv.multiply(255).rename("R")
            .addBands(both.multiply(255).rename("G"))
            .addBands(vh_ships.And(vv_ships.Not()).multiply(255).rename("B"))
        )
        save_thumb(rgb, GULF_SHIPS, p, {"bands": ["R", "G", "B"], "min": 0, "max": 255})
        log(
            "ship_followup_vv_vs_vh",
            True,
            {"vv_thr": -5, "vh_thr": -12},
            {"vv_pix": c_vv.get("VV"), "vh_pix": c_vh.get("VH"), "both_pix": c_both.get("VV")},
            [str(p)],
            notes="Ships are usually stronger in VV (surface bounce)",
        )
    except Exception as e:
        log("ship_followup_vv_vs_vh", False, {}, error=str(e))

    # F2: multi-date persistent bright targets (oil platforms) vs transient (ships)
    try:
        col = s1_vvvh(GULF_SHIPS, "2023-06-01", "2023-09-01").select("VV")
        n = col.size().getInfo()
        # fraction of dates above threshold
        bright_frac = col.map(lambda im: im.gt(-5)).mean().rename("bright_frac")
        persistent = bright_frac.gt(0.4).rename("platform_like")
        transient_hot = bright_frac.gt(0.02).And(bright_frac.lt(0.2)).rename("ship_like")
        p_pix = persistent.selfMask().reduceRegion(ee.Reducer.count(), GULF_SHIPS, 40, maxPixels=1e8, bestEffort=True).getInfo()
        t_pix = transient_hot.selfMask().reduceRegion(ee.Reducer.count(), GULF_SHIPS, 40, maxPixels=1e8, bestEffort=True).getInfo()
        p = THUMBS / "gulf_persistent_vs_transient_bright.png"
        rgb = (
            persistent.multiply(255).rename("R")
            .addBands(ee.Image(0).rename("G"))
            .addBands(transient_hot.multiply(255).rename("B"))
        )
        save_thumb(rgb, GULF_SHIPS, p, {"bands": ["R", "G", "B"], "min": 0, "max": 255})
        # also show bright_frac
        p2 = THUMBS / "gulf_bright_fraction.png"
        save_thumb(bright_frac, GULF_SHIPS, p2, {"min": 0, "max": 0.5, "palette": ["000000", "ffff00", "ff0000"]})
        log(
            "ship_followup_persistent_platforms",
            True,
            {"n_scenes": n, "persist_thr": 0.4},
            {"persistent_pixels": p_pix.get("platform_like"), "transient_pixels": t_pix.get("ship_like")},
            [str(p), str(p2)],
            notes="Red≈oil platforms / fixed structures; blue≈occasional ships",
        )
    except Exception as e:
        log("ship_followup_persistent_platforms", False, {}, error=str(e))

    # F3: ascending vs descending ship scene counts / brightness
    try:
        for pass_dir in ["ASCENDING", "DESCENDING"]:
            col = s1_vvvh(GULF_SHIPS, "2023-01-01", "2023-12-31", pass_dir=pass_dir)
            n = col.size().getInfo()
            med = col.median().select("VV")
            pctl = med.reduceRegion(
                ee.Reducer.percentile([50, 99]), GULF_SHIPS, 40, maxPixels=1e8, bestEffort=True
            ).getInfo()
            log(
                f"ship_followup_pass_{pass_dir.lower()}",
                True,
                {"pass": pass_dir, "year": 2023},
                {"n": n, "percentiles": pctl},
                notes=f"{pass_dir}: {n} scenes; VV p99={pctl.get('VV_p99')}",
            )
    except Exception as e:
        log("ship_followup_pass_dirs", False, {}, error=str(e))


def probe_speckle_filtering():
    try:
        col = s1_vvvh(GALVESTON, "2023-08-01", "2023-08-20")
        scene = ee.Image(col.first()).select(["VV", "VH"])
        raw_stats = reduce_stats(scene, GALVESTON, 20, ["VV", "VH"])
        med = focal_median_speckle(scene, 50)
        med_stats = reduce_stats(med, GALVESTON, 20, ["VV", "VH"])
        # refinedLee: try ee.Image.focalMean as stand-in AND check if refinedLee exists
        has_refined = hasattr(ee.Image, "refinedLee") or hasattr(scene, "refinedLee")
        lee_note = "refinedLee not a native ee.Image method in Python API"
        try:
            # Some community snippets use a custom function; native may not exist
            lee = scene.refinedLee()  # type: ignore
            lee_stats = reduce_stats(lee, GALVESTON, 20, ["VV", "VH"])
            lee_ok = True
        except Exception as e:
            lee_ok = False
            lee_stats = {"error": str(e)[:200]}
            # implement a simple Lee-like: local mean/var damping
            ksize = 5
            mean = scene.focalMean(ksize, "square", "pixels")
            # variance approx via E[x^2]-E[x]^2 in linear domain
            lin = ee.Image(10).pow(scene.divide(10))
            lin_mean = lin.focalMean(ksize, "square", "pixels")
            lin_var = lin.pow(2).focalMean(ksize, "square", "pixels").subtract(lin_mean.pow(2))
            # ENL estimate ~ mean^2/var
            enl = lin_mean.pow(2).divide(lin_var.max(1e-10))
            weight = lin_var.divide(lin_var.add(lin_mean.pow(2).divide(enl.max(1))))
            # simpler: just use focalMean on dB as "boxcar"
            lee = mean
            lee_stats = reduce_stats(lee, GALVESTON, 20, ["VV", "VH"])
            lee_note = f"refinedLee unavailable ({str(e)[:80]}); used focalMean boxcar instead"

        p1 = THUMBS / "speckle_raw_VV.png"
        p2 = THUMBS / "speckle_focalMedian_VV.png"
        p3 = THUMBS / "speckle_boxcar_VV.png"
        save_thumb(scene.select("VV"), GALVESTON, p1, {"min": -22, "max": 0})
        save_thumb(med.select("VV"), GALVESTON, p2, {"min": -22, "max": 0})
        save_thumb(lee.select("VV"), GALVESTON, p3, {"min": -22, "max": 0})
        # ENL proxy: mean^2/var on a homogeneous water patch
        water = CLEAR_LAKE
        for label, im in [("raw", scene), ("focalMedian", med), ("boxcar", lee)]:
            st = im.select("VV").reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                water, 20, maxPixels=1e8, bestEffort=True,
            ).getInfo()
            m, s = st.get("VV_mean"), st.get("VV_stdDev")
            # in dB domain ENL is approximate; also compute linear ENL
            lin = ee.Image(10).pow(im.select("VV").divide(10))
            lst = lin.reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                water, 20, maxPixels=1e8, bestEffort=True,
            ).getInfo()
            lm, ls = lst.get("VV_mean"), lst.get("VV_stdDev")
            enl = (lm ** 2 / ls ** 2) if lm and ls else None
            log(
                f"speckle_enl_{label}",
                True,
                {"patch": "clear_lake"},
                {"dB_mean": m, "dB_std": s, "lin_mean": lm, "lin_std": ls, "ENL_approx": enl},
                notes=f"{label}: ENL≈{enl}",
            )

        log(
            "speckle_filtering_compare",
            True,
            {"focalMedian_radius_m": 50, "has_native_refinedLee": has_refined},
            {"raw": raw_stats, "focalMedian": med_stats, "lee_or_boxcar": lee_stats},
            [str(p1), str(p2), str(p3)],
            notes=lee_note,
        )
    except Exception as e:
        log("speckle_filtering_compare", False, {}, error=str(e) + "\n" + traceback.format_exc()[:400])


def probe_change_detection_port():
    """Seasonal / construction-ish change at Port of Houston."""
    try:
        winter = s1_vvvh(PORT_HOUSTON, "2023-01-01", "2023-02-28").median()
        summer = s1_vvvh(PORT_HOUSTON, "2023-07-01", "2023-08-31").median()
        d = summer.select("VV").subtract(winter.select("VV")).rename("dVV")
        st = reduce_stats(d, PORT_HOUSTON, 30, ["dVV"])
        abs_change = d.abs().gt(3).rename("changed")
        area = abs_change.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), PORT_HOUSTON, 30, maxPixels=1e8, bestEffort=True
        ).getInfo()
        p1 = THUMBS / "port_houston_winter_VV.png"
        p2 = THUMBS / "port_houston_summer_VV.png"
        p3 = THUMBS / "port_houston_seasonal_dVV.png"
        save_thumb(winter.select("VV"), PORT_HOUSTON, p1, {"min": -20, "max": 0})
        save_thumb(summer.select("VV"), PORT_HOUSTON, p2, {"min": -20, "max": 0})
        save_thumb(d, PORT_HOUSTON, p3, {"min": -6, "max": 6, "palette": ["0000ff", "ffffff", "ff0000"]})
        log(
            "port_houston_seasonal_change",
            True,
            {"winter": "2023-01..02", "summer": "2023-07..08"},
            {"dVV": st, "changed_gt3dB_km2": (area.get("changed") or 0) / 1e6},
            [str(p1), str(p2), str(p3)],
            notes=f"Seasonal |dVV|>3dB area={(area.get('changed') or 0)/1e6:.2f} km²",
        )
    except Exception as e:
        log("port_houston_seasonal_change", False, {}, error=str(e))


def probe_seasonal_composites():
    sites = {
        "galveston": GALVESTON,
        "houston_floodplain": HOUSTON_FLOOD,
        "port_houston": PORT_HOUSTON,
        "ms_river": MS_RIVER,
    }
    for site_name, region in sites.items():
        try:
            seasons = {
                "DJF": ("2022-12-01", "2023-03-01"),
                "MAM": ("2023-03-01", "2023-06-01"),
                "JJA": ("2023-06-01", "2023-09-01"),
                "SON": ("2023-09-01", "2023-12-01"),
            }
            means = {}
            for sn, (a, b) in seasons.items():
                col = s1_vvvh(region, a, b)
                n = col.size().getInfo()
                med = col.median()
                st = reduce_stats(med, region, 50, ["VV", "VH"])
                means[sn] = {"n": n, **st}
                p = THUMBS / f"seasonal_{site_name}_{sn}_VV.png"
                save_thumb(med.select("VV"), region, p, {"min": -22, "max": 0, "palette": ["000000", "0a3d62", "82ccdd", "ffffff"]})
            log(
                f"seasonal_composite_{site_name}",
                True,
                {"yearish": "2022-12..2023-12"},
                means,
                [str(THUMBS / f"seasonal_{site_name}_{s}_VV.png") for s in seasons],
                notes=f"JJA VV mean={means['JJA'].get('VV_mean')} vs DJF={means['DJF'].get('VV_mean')}",
            )
        except Exception as e:
            log(f"seasonal_composite_{site_name}", False, {}, error=str(e))


def probe_ms_river_flood():
    """Inland river: look for wet spring vs dry summer on MS river."""
    try:
        wet = s1_vvvh(MS_RIVER, "2023-03-01", "2023-04-15").median()
        dry = s1_vvvh(MS_RIVER, "2023-08-01", "2023-09-15").median()
        d = wet.select("VV").subtract(dry.select("VV")).rename("dVV")
        # wetter = lower VV in floodplain
        wet_mask = wet.select("VV").lt(-15).And(d.lt(-2))
        area = wet_mask.rename("w").selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), MS_RIVER, 40, maxPixels=1e8, bestEffort=True
        ).getInfo()
        st = reduce_stats(d, MS_RIVER, 40, ["dVV"])
        paths = []
        for name, img, vis in [
            ("ms_river_wet_VV.png", wet.select("VV"), {"min": -22, "max": 0}),
            ("ms_river_dry_VV.png", dry.select("VV"), {"min": -22, "max": 0}),
            ("ms_river_wet_minus_dry.png", d, {"min": -8, "max": 4, "palette": ["ff0000", "ffffff", "0000ff"]}),
        ]:
            p = THUMBS / name
            save_thumb(img, MS_RIVER, p, vis)
            paths.append(str(p))
        log(
            "ms_river_wet_vs_dry",
            True,
            {"wet": "2023-03..04", "dry": "2023-08..09"},
            {"dVV": st, "extra_wet_km2": (area.get("w") or 0) / 1e6},
            paths,
            notes=f"Extra low-backscatter wet area≈{(area.get('w') or 0)/1e6:.1f} km²; mean dVV={st.get('dVV_mean')}",
        )
    except Exception as e:
        log("ms_river_wet_vs_dry", False, {}, error=str(e))


def probe_dualpol_ratios():
    try:
        med = s1_vvvh(GALVESTON, "2023-06-01", "2023-08-01").median()
        ratio = to_db_ratio(med)  # VV-VH in dB
        # also VH/VV linear ratio
        lin_vv = ee.Image(10).pow(med.select("VV").divide(10))
        lin_vh = ee.Image(10).pow(med.select("VH").divide(10))
        rlin = lin_vh.divide(lin_vv).rename("VH_over_VV")
        st_r = reduce_stats(ratio, GALVESTON, 40, ["VV_minus_VH"])
        st_l = reduce_stats(rlin, GALVESTON, 40, ["VH_over_VV"])
        # urban vs water ratio
        u = reduce_stats(ratio, HOUSTON_URBAN, 30, ["VV_minus_VH"])
        w = reduce_stats(ratio, CLEAR_LAKE, 30, ["VV_minus_VH"])
        p = THUMBS / "galveston_VV_minus_VH.png"
        save_thumb(ratio, GALVESTON, p, {"min": 2, "max": 12, "palette": ["0000ff", "00ff00", "ffff00", "ff0000"]})
        p2 = THUMBS / "galveston_VH_over_VV_linear.png"
        save_thumb(rlin, GALVESTON, p2, {"min": 0.05, "max": 0.5, "palette": ["000000", "00ffff", "ffffff"]})
        log(
            "dualpol_ratios_galveston",
            True,
            {},
            {"VV_minus_VH": st_r, "VH_over_VV": st_l, "urban_ratio": u, "water_ratio": w},
            [str(p), str(p2)],
            notes=(
                f"VV-VH urban mean={u.get('VV_minus_VH_mean')} water={w.get('VV_minus_VH_mean')} "
                "(volume scattering lowers ratio over vegetation)"
            ),
        )
    except Exception as e:
        log("dualpol_ratios_galveston", False, {}, error=str(e))


def probe_coherence_dataset():
    """Interferometry-adjacent: seasonal S1 coherence product."""
    try:
        coh = ee.ImageCollection("Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/COHERENCE")
        n = coh.size().getInfo()
        bands = coh.first().bandNames().getInfo()
        # clip to galveston
        img = coh.mean().clip(GALVESTON.buffer(20000))
        # pick first few bands
        use = bands[:3] if bands else []
        st = reduce_stats(img, GALVESTON, 100, use) if use else {}
        p = THUMBS / "galveston_s1_seasonal_coherence.png"
        if use:
            save_thumb(img.select(use[0]), GALVESTON, p, {"min": 0, "max": 1, "palette": ["000000", "0000ff", "00ff00", "ffff00", "ffffff"]})
        # urban vs water coherence
        u = img.select(use[0]).reduceRegion(ee.Reducer.mean(), HOUSTON_URBAN, 100, maxPixels=1e8, bestEffort=True).getInfo() if use else {}
        w = img.select(use[0]).reduceRegion(ee.Reducer.mean(), CLEAR_LAKE, 100, maxPixels=1e8, bestEffort=True).getInfo() if use else {}
        log(
            "seasonal_s1_coherence_v2019",
            True,
            {"asset": "Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/COHERENCE"},
            {"n_images": n, "bands": bands, "stats": st, "urban_coh": u, "water_coh": w},
            [str(p)] if use else [],
            notes=f"Public seasonal coherence (not raw InSAR). Urban coh={u} water={w}. Bands={bands}",
        )
        # follow-ups
        try:
            bs = ee.ImageCollection("Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/BACKSCATTER").mean()
            bb = bs.bandNames().getInfo()
            p2 = THUMBS / "galveston_s1_seasonal_backscatter.png"
            save_thumb(bs.select(bb[0]), GALVESTON, p2, {"min": -20, "max": 0})
            st2 = reduce_stats(bs, GALVESTON, 100, bb[:2])
            log(
                "seasonal_s1_backscatter_v2019",
                True,
                {},
                {"bands": bb, "stats": st2},
                [str(p2)],
                notes="Companion seasonal backscatter mosaic",
            )
        except Exception as e:
            log("seasonal_s1_backscatter_v2019", False, {}, error=str(e))

        try:
            dec = ee.ImageCollection("Earth_Big_Data/GLOBAL_SEASONAL_S1/V2019/DECAY_MODEL_PARAMETERS")
            db = dec.first().bandNames().getInfo()
            dimg = dec.mean()
            st3 = reduce_stats(dimg, GALVESTON, 200, db[:3])
            p3 = THUMBS / "galveston_s1_coherence_decay.png"
            save_thumb(dimg.select(db[0]), GALVESTON, p3, {"min": 0, "max": 1})
            log(
                "seasonal_s1_coherence_decay_params",
                True,
                {},
                {"bands": db, "stats": st3},
                [str(p3)],
                notes="Temporal coherence decay model parameters — rare InSAR-adjacent public layer",
            )
        except Exception as e:
            log("seasonal_s1_coherence_decay_params", False, {}, error=str(e))
    except Exception as e:
        log("seasonal_s1_coherence_v2019", False, {}, error=str(e))


def probe_try_insar_slc():
    """Document that SLC / interferograms are not in public EE for S1."""
    for asset in ["COPERNICUS/S1_SLC", "COPERNICUS/S1/SLC", "ESA/COPERNICUS/S1_SLC"]:
        try:
            n = ee.ImageCollection(asset).limit(1).size().getInfo()
            log("insar_slc_attempt", True, {"asset": asset}, {"n": n}, notes="Unexpectedly found SLC!")
            return
        except Exception as e:
            log(
                f"insar_slc_fail_{asset.replace('/', '_')}",
                False,
                {"asset": asset},
                error=str(e)[:300],
                notes="S1 SLC / raw interferograms not in public EE — use ASF HyP3 or COMET for InSAR",
            )


def probe_opera_rtc():
    try:
        col = (
            ee.ImageCollection("OPERA/RTC/L2_V1/S1")
            .filterBounds(GALVESTON)
            .filterDate("2023-06-01", "2023-09-01")
        )
        n = col.size().getInfo()
        bands = col.first().bandNames().getInfo() if n else []
        if n:
            img = col.median()
            # OPERA RTC often linear power
            st = reduce_stats(img, GALVESTON, 40, bands[:2] if bands else None)
            p = THUMBS / "opera_rtc_galveston.png"
            b0 = bands[0]
            # convert if looks like linear
            vis_img = img.select(b0)
            # try dB
            vis_db = ee.Image(10).multiply(vis_img.max(1e-10).log10())
            save_thumb(vis_db, GALVESTON, p, {"min": -25, "max": 0, "palette": ["000000", "00aaff", "ffffff"]})
            log(
                "opera_rtc_galveston",
                True,
                {"asset": "OPERA/RTC/L2_V1/S1"},
                {"n": n, "bands": bands, "stats": st},
                [str(p)],
                notes=f"OPERA RTC: {n} scenes, bands={bands}",
            )
        else:
            log("opera_rtc_galveston", False, {}, notes="0 scenes in window — try wider")
            col2 = ee.ImageCollection("OPERA/RTC/L2_V1/S1").filterBounds(GALVESTON).filterDate("2022-01-01", "2025-01-01")
            n2 = col2.size().getInfo()
            log("opera_rtc_galveston_wider", True if n2 else False, {}, {"n": n2}, notes=f"Wider window n={n2}")
    except Exception as e:
        log("opera_rtc_galveston", False, {}, error=str(e))


def probe_opera_dswx():
    try:
        col = (
            ee.ImageCollection("OPERA/DSWX/L3_V1/S1")
            .filterBounds(HOUSTON_FLOOD)
            .filterDate("2024-01-01", "2025-06-01")
        )
        n = col.size().getInfo()
        if n:
            bands = col.first().bandNames().getInfo()
            img = col.mode() if "WTR" in bands or "WATER" in [b.upper() for b in bands] else col.median()
            p = THUMBS / "opera_dswx_houston.png"
            b0 = bands[0]
            save_thumb(img.select(b0), HOUSTON_FLOOD, p, {"min": 0, "max": 3, "palette": ["ffffff", "0000ff", "00ffff", "000083"]})
            st = reduce_stats(img, HOUSTON_FLOOD, 50, bands[:2])
            log(
                "opera_dswx_s1_houston",
                True,
                {},
                {"n": n, "bands": bands, "stats": st},
                [str(p)],
                notes=f"DSWx-S1 water product: {n} scenes",
            )
        else:
            # try any date
            col2 = ee.ImageCollection("OPERA/DSWX/L3_V1/S1").filterBounds(GALVESTON)
            n2 = col2.limit(50).size().getInfo()
            dates = col2.limit(5).aggregate_array("system:time_start").getInfo()
            log(
                "opera_dswx_s1_houston",
                False,
                {},
                {"n_any_galveston_sample": n2, "sample_dates": dates},
                notes="No DSWx in 2024 Houston window; sampled galveston availability",
            )
    except Exception as e:
        log("opera_dswx_s1_houston", False, {}, error=str(e))


def probe_alos_palsar():
    try:
        # Yearly mosaic
        col = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH").filterDate("2020-01-01", "2022-01-01")
        img = col.first().clip(GALVESTON)
        # DN to dB: 10*log10(DN^2) - 83.0  (classic PALSAR)
        hh = img.select("HH").pow(2).log10().multiply(10).subtract(83.0).rename("HH_dB")
        hv = img.select("HV").pow(2).log10().multiply(10).subtract(83.0).rename("HV_dB")
        st = reduce_stats(hh.addBands(hv), GALVESTON, 50, ["HH_dB", "HV_dB"])
        p = THUMBS / "alos_palsar_galveston_HH.png"
        save_thumb(hh, GALVESTON, p, {"min": -25, "max": 0, "palette": ["000000", "ffaa00", "ffffff"]})
        # RFDI-like: (HH-HV)/(HH+HV) in linear
        hh_lin = ee.Image(10).pow(hh.divide(10))
        hv_lin = ee.Image(10).pow(hv.divide(10))
        rfdi = hh_lin.subtract(hv_lin).divide(hh_lin.add(hv_lin)).rename("RFDI")
        p2 = THUMBS / "alos_palsar_galveston_RFDI.png"
        save_thumb(rfdi, GALVESTON, p2, {"min": 0, "max": 1, "palette": ["0000ff", "00ff00", "ffff00", "ff0000"]})
        log(
            "alos_palsar_yearly_galveston",
            True,
            {"asset": "JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH", "year": 2020},
            {"stats": st},
            [str(p), str(p2)],
            notes=f"L-band HH mean={st.get('HH_dB_mean')} HV={st.get('HV_dB_mean')}",
        )
    except Exception as e:
        log("alos_palsar_yearly_galveston", False, {}, error=str(e))

    # ScanSAR over Houston Harvey period?
    try:
        col = (
            ee.ImageCollection("JAXA/ALOS/PALSAR-2/Level2_2/ScanSAR")
            .filterBounds(HOUSTON_FLOOD)
            .filterDate("2017-08-01", "2017-10-01")
        )
        n = col.size().getInfo()
        if n:
            bands = col.first().bandNames().getInfo()
            img = col.first()
            # filter for HV if possible
            col_hv = col.filter(ee.Filter.listContains("Polarizations", "HV"))
            nhv = col_hv.size().getInfo()
            if nhv:
                img = col_hv.first()
                hh = img.select("HH").pow(2).log10().multiply(10).subtract(83).rename("HH_dB")
                p = THUMBS / "alos_scansar_harvey_HH.png"
                save_thumb(hh, HOUSTON_FLOOD, p, {"min": -25, "max": 0})
                st = reduce_stats(hh, HOUSTON_FLOOD, 50, ["HH_dB"])
                date = datetime.utcfromtimestamp(img.get("system:time_start").getInfo() / 1000).isoformat()
                log(
                    "alos_scansar_harvey",
                    True,
                    {"n": n, "n_with_HV": nhv, "date": date},
                    st,
                    [str(p)],
                    notes=f"PALSAR-2 ScanSAR during Harvey window: {date}",
                )
            else:
                log("alos_scansar_harvey", True, {"n": n, "n_with_HV": 0}, notes="Scenes exist but no HV")
        else:
            log("alos_scansar_harvey", False, {}, notes="No ScanSAR scenes over Houston in Harvey window")
    except Exception as e:
        log("alos_scansar_harvey", False, {}, error=str(e))

    # StripMap emergency
    try:
        col = ee.ImageCollection("JAXA/ALOS/PALSAR-2/Level2_1/StripMap_202401").filterBounds(GALVESTON)
        n = col.size().getInfo()
        log(
            "alos_stripmap_202401_galveston",
            True if n else False,
            {},
            {"n": n},
            notes="Japan-focused emergency StripMap — expect 0 over Texas" if not n else f"Unexpected coverage n={n}",
        )
    except Exception as e:
        log("alos_stripmap_202401_galveston", False, {}, error=str(e))


def probe_lhscat():
    try:
        col = ee.ImageCollection("projects/ee-pkurelab/assets/LHScat").filterBounds(GALVESTON_PT)
        n = col.limit(5).size().getInfo()
        bands = col.first().bandNames().getInfo() if n else []
        # monthly? take mean
        if n:
            img = col.filterDate("2018-01-01", "2019-01-01").mean()
            st = reduce_stats(img, GALVESTON, 5000, bands[:1] if bands else None)
            p = THUMBS / "lhscat_galveston.png"
            save_thumb(img.select(bands[0]), GALVESTON, p, {"min": -20, "max": 0})
            log("lhscat_scatterometer", True, {}, {"n_sample": n, "bands": bands, "stats": st}, [str(p)],
                notes="Long-term scatterometer (ERS/QuikSCAT/ASCAT) — coarse but multi-decadal")
        else:
            log("lhscat_scatterometer", False, {}, notes="No LHScat over Galveston sample")
    except Exception as e:
        log("lhscat_scatterometer", False, {}, error=str(e))


def probe_incidence_angle_effect():
    try:
        col = s1_vvvh(GALVESTON, "2023-01-01", "2023-12-31")
        # sample angle band correlation with VV
        img = col.median()
        # per-scene: mean VV vs mean angle
        def per(im):
            d = im.select(["VV", "angle"]).reduceRegion(
                ee.Reducer.mean(), GALVESTON, 100, maxPixels=1e7, bestEffort=True
            )
            return ee.Feature(None, d)
        fc = col.limit(40).map(per)
        data = fc.getInfo()
        pairs = []
        for f in data.get("features", []):
            p = f["properties"]
            if "VV" in p and "angle" in p and p["VV"] is not None:
                pairs.append({"VV": p["VV"], "angle": p["angle"]})
        # simple correlation
        if len(pairs) >= 5:
            mv = sum(x["VV"] for x in pairs) / len(pairs)
            ma = sum(x["angle"] for x in pairs) / len(pairs)
            num = sum((x["VV"] - mv) * (x["angle"] - ma) for x in pairs)
            den = math.sqrt(sum((x["VV"] - mv) ** 2 for x in pairs) * sum((x["angle"] - ma) ** 2 for x in pairs))
            corr = num / den if den else None
        else:
            corr = None
        log(
            "incidence_angle_vs_VV",
            True,
            {"n_scenes_sampled": len(pairs)},
            {"corr_VV_angle": corr, "pairs_sample": pairs[:8]},
            notes=f"Corr(VV, incidence angle)≈{corr} over Galveston (geometry radiometry)",
        )
    except Exception as e:
        log("incidence_angle_vs_VV", False, {}, error=str(e))


def probe_float_vs_db():
    try:
        db = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(GALVESTON)
            .filterDate("2023-08-01", "2023-08-10")
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .first()
            .select("VV")
        )
        fl = (
            ee.ImageCollection("COPERNICUS/S1_GRD_FLOAT")
            .filterBounds(GALVESTON)
            .filterDate("2023-08-01", "2023-08-10")
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .first()
            .select("VV")
        )
        # match same id if possible
        sid = db.get("system:index").getInfo()
        fl2 = ee.ImageCollection("COPERNICUS/S1_GRD_FLOAT").filter(ee.Filter.eq("system:index", sid)).first()
        st_db = reduce_stats(db, GALVESTON, 40, ["VV"])
        st_fl = reduce_stats(fl2.select("VV"), GALVESTON, 40, ["VV"])
        # convert float to dB and compare
        fl_db = ee.Image(10).multiply(fl2.select("VV").max(1e-10).log10())
        st_fl_db = reduce_stats(fl_db, GALVESTON, 40, ["VV"])
        delta = abs((st_db.get("VV_mean") or 0) - (st_fl_db.get("VV_mean") or 0))
        log(
            "grd_db_vs_float",
            True,
            {"system_index": sid},
            {"db_collection": st_db, "float_linear": st_fl, "float_as_db": st_fl_db, "abs_mean_delta_dB": delta},
            notes=f"GRD log vs FLOAT→dB mean delta={delta:.4f} dB (should be ~0)",
        )
    except Exception as e:
        log("grd_db_vs_float", False, {}, error=str(e))


def probe_orbit_mosaic_artifacts():
    """Show that mixing orbits creates striping / seams."""
    try:
        mixed = s1_vvvh(GALVESTON, "2023-01-01", "2023-03-01").median().select("VV")
        # pick dominant orbit
        orbits = (
            s1_vvvh(GALVESTON, "2023-01-01", "2023-03-01")
            .aggregate_array("relativeOrbitNumber_start")
            .distinct()
            .getInfo()
        )
        if orbits:
            single = s1_vvvh(GALVESTON, "2023-01-01", "2023-03-01", orbit=orbits[0]).median().select("VV")
            p1 = THUMBS / "mosaic_mixed_orbits_VV.png"
            p2 = THUMBS / f"mosaic_orbit{orbits[0]}_only_VV.png"
            save_thumb(mixed, GALVESTON, p1, {"min": -22, "max": 0})
            save_thumb(single, GALVESTON, p2, {"min": -22, "max": 0})
            sm = reduce_stats(mixed, GALVESTON, 40, ["VV"])
            ss = reduce_stats(single, GALVESTON, 40, ["VV"])
            log(
                "orbit_mosaic_artifacts",
                True,
                {"orbits": orbits, "single_orbit": orbits[0]},
                {"mixed": sm, "single": ss, "std_ratio_mixed_over_single": (sm.get("VV_stdDev") or 0) / (ss.get("VV_stdDev") or 1)},
                [str(p1), str(p2)],
                notes="Mixed-orbit median often noisier / seamier than single relative orbit",
            )
    except Exception as e:
        log("orbit_mosaic_artifacts", False, {}, error=str(e))


def probe_urban_double_bounce():
    """High VV and high VV-VH in downtown = double bounce."""
    try:
        med = s1_vvvh(HOUSTON_URBAN, "2023-01-01", "2023-12-31").median()
        ratio = to_db_ratio(med)
        # double-bounce proxy: VV > -8 and VV-VH > 7
        dbounce = med.select("VV").gt(-8).And(ratio.gt(7)).rename("dbounce")
        area = dbounce.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), HOUSTON_URBAN, 20, maxPixels=1e8, bestEffort=True
        ).getInfo()
        p = THUMBS / "houston_double_bounce_proxy.png"
        rgb = med.select("VV").addBands(med.select("VH")).addBands(ratio)
        save_thumb(rgb, HOUSTON_URBAN, p, {"min": [-10, -18, 4], "max": [2, -6, 14]})
        p2 = THUMBS / "houston_double_bounce_mask.png"
        save_thumb(dbounce.selfMask(), HOUSTON_URBAN, p2, {"min": 0, "max": 1, "palette": ["000000", "ff00ff"]})
        log(
            "urban_double_bounce_houston",
            True,
            {"rule": "VV>-8 & VV-VH>7"},
            {"area_km2": (area.get("dbounce") or 0) / 1e6, "vv": reduce_stats(med, HOUSTON_URBAN, 20, ["VV", "VH"])},
            [str(p), str(p2)],
            notes=f"Double-bounce proxy area={(area.get('dbounce') or 0)/1e6:.3f} km² downtown Houston",
        )
    except Exception as e:
        log("urban_double_bounce_houston", False, {}, error=str(e))


def probe_wind_roughened_sea():
    """Compare calm vs windy ocean VV (use different dates)."""
    try:
        # Use many dates; find min and max mean VV over gulf
        col = s1_vvvh(GULF_SHIPS, "2023-01-01", "2023-12-31", pass_dir="DESCENDING")
        def feat(im):
            m = im.select("VV").reduceRegion(ee.Reducer.mean(), GULF_SHIPS, 100, maxPixels=1e7, bestEffort=True)
            return ee.Feature(None, {"VV": m.get("VV"), "t": im.get("system:time_start")})
        fc = ee.FeatureCollection(col.limit(60).map(feat))
        # sort
        calm = ee.Image(col.filterDate("2023-01-01", "2024-01-01").sort("system:time_start").first())  # placeholder
        data = fc.sort("VV").limit(3).getInfo()
        data_loud = fc.sort("VV", False).limit(3).getInfo()
        calm_t = data["features"][0]["properties"]["t"]
        wind_t = data_loud["features"][0]["properties"]["t"]
        calm_img = ee.Image(col.filter(ee.Filter.eq("system:time_start", calm_t)).first()).select("VV")
        wind_img = ee.Image(col.filter(ee.Filter.eq("system:time_start", wind_t)).first()).select("VV")
        sc = reduce_stats(calm_img, GULF_SHIPS, 40, ["VV"])
        sw = reduce_stats(wind_img, GULF_SHIPS, 40, ["VV"])
        p1 = THUMBS / "gulf_calm_sea_VV.png"
        p2 = THUMBS / "gulf_rough_sea_VV.png"
        save_thumb(calm_img, GULF_SHIPS, p1, {"min": -25, "max": -5})
        save_thumb(wind_img, GULF_SHIPS, p2, {"min": -25, "max": -5})
        log(
            "wind_roughened_sea_contrast",
            True,
            {
                "calm_date": datetime.utcfromtimestamp(calm_t / 1000).isoformat(),
                "rough_date": datetime.utcfromtimestamp(wind_t / 1000).isoformat(),
            },
            {
                "calm": sc,
                "rough": sw,
                "delta_mean_dB": (sw.get("VV_mean") or 0) - (sc.get("VV_mean") or 0),
                "calm_candidates": [f["properties"] for f in data["features"]],
                "rough_candidates": [f["properties"] for f in data_loud["features"]],
            },
            [str(p1), str(p2)],
            notes=f"Rough−calm ocean VV Δ={(sw.get('VV_mean') or 0)-(sc.get('VV_mean') or 0):.2f} dB",
        )
    except Exception as e:
        log("wind_roughened_sea_contrast", False, {}, error=str(e) + "\n" + traceback.format_exc()[:400])


def probe_fail_intentionally():
    """Things expected to fail / be weird."""
    # EW mode over inland
    try:
        col = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(HOUSTON_URBAN)
            .filterDate("2023-01-01", "2024-01-01")
            .filter(ee.Filter.eq("instrumentMode", "EW"))
        )
        n = col.size().getInfo()
        log(
            "ew_mode_over_houston",
            True if n else False,
            {"mode": "EW"},
            {"n": n},
            notes="EW is ocean/arctic mode — expect ~0 over Houston" if not n else f"Surprise EW n={n}",
        )
    except Exception as e:
        log("ew_mode_over_houston", False, {}, error=str(e))

    # HH polarization mid-latitudes IW — rare
    try:
        col = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(GALVESTON)
            .filterDate("2015-01-01", "2024-01-01")
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "HH"))
        )
        n = col.size().getInfo()
        log(
            "hh_pol_galveston_iw",
            True if n else False,
            {},
            {"n": n},
            notes="HH IW rare outside polar — expect 0" if not n else f"Found HH n={n}",
        )
    except Exception as e:
        log("hh_pol_galveston_iw", False, {}, error=str(e))

    # Impossible date
    try:
        col = s1_vvvh(GALVESTON, "2010-01-01", "2012-01-01")
        n = col.size().getInfo()
        log("s1_prelaunch_2010", False if n == 0 else True, {}, {"n": n}, notes="Pre-launch should be empty")
    except Exception as e:
        log("s1_prelaunch_2010", False, {}, error=str(e))


def probe_cross_sensor_s1_vs_alos():
    try:
        s1 = s1_vvvh(GALVESTON, "2020-01-01", "2021-01-01").median().select("VV")
        alos = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH").filterDate("2020-01-01", "2021-01-01").first()
        alos_hh = alos.select("HH").pow(2).log10().multiply(10).subtract(83).rename("HH_dB")
        s1s = reduce_stats(s1, GALVESTON, 50, ["VV"])
        as_ = reduce_stats(alos_hh, GALVESTON, 50, ["HH_dB"])
        p = THUMBS / "cross_s1_VV_vs_alos_HH.png"
        # side-by-side fake: difference after normalizing means
        s1n = s1.subtract(s1s.get("VV_mean") or -12)
        an = alos_hh.subtract(as_.get("HH_dB_mean") or -12)
        diff = s1n.subtract(an).rename("d")
        save_thumb(diff, GALVESTON, p, {"min": -8, "max": 8, "palette": ["0000ff", "ffffff", "ff0000"]})
        log(
            "cross_sensor_s1_cband_vs_alos_lband",
            True,
            {"s1": "C-band VV", "alos": "L-band HH 2020 mosaic"},
            {"s1": s1s, "alos": as_},
            [str(p)],
            notes=(
                f"C-band VV mean={s1s.get('VV_mean'):.2f} vs L-band HH={as_.get('HH_dB_mean'):.2f} — "
                "different scattering regimes (esp. vegetation penetration)"
            ),
        )
    except Exception as e:
        log("cross_sensor_s1_cband_vs_alos_lband", False, {}, error=str(e))


def probe_gimp_radarsat():
    try:
        img = ee.Image("OSU/GIMP/2000_IMAGERY_MOSAIC")
        bands = img.bandNames().getInfo()
        st_tx = img.reduceRegion(ee.Reducer.mean(), GALVESTON, 1000, maxPixels=1e6, bestEffort=True).getInfo()
        greenland = ee.Geometry.Point([-45.0, 70.0]).buffer(50000).bounds()
        st_gl = img.reduceRegion(ee.Reducer.mean(), greenland, 500, maxPixels=1e7, bestEffort=True).getInfo()
        p = THUMBS / "gimp_radarsat_greenland.png"
        save_thumb(img.select(bands[0]), greenland, p, {"min": 0, "max": 255})
        log(
            "gimp_radarsat1_greenland",
            True,
            {"asset": "OSU/GIMP/2000_IMAGERY_MOSAIC"},
            {"bands": bands, "texas_stats": st_tx, "greenland_stats": st_gl},
            [str(p)],
            notes="RADARSAT-1 era Greenland mosaic — empty/null over Texas, works over Greenland",
        )
    except Exception as e:
        log("gimp_radarsat1_greenland", False, {}, error=str(e))


def probe_fnf_forest():
    try:
        img = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/FNF4").filterDate("2020-01-01", "2021-01-01").first()
        # classes over galveston / houston
        hist = img.reduceRegion(ee.Reducer.frequencyHistogram(), GALVESTON, 50, maxPixels=1e8, bestEffort=True).getInfo()
        p = THUMBS / "alos_fnf4_galveston.png"
        save_thumb(img, GALVESTON, p, {"min": 1, "max": 4, "palette": ["006400", "90ee90", "ffff00", "0000ff"]})
        log(
            "alos_fnf4_galveston",
            True,
            {"year": 2020},
            {"histogram": hist},
            [str(p)],
            notes="PALSAR-derived forest/non-forest classification over Galveston bay area",
        )
    except Exception as e:
        log("alos_fnf4_galveston", False, {}, error=str(e))


def probe_time_series_vv_point():
    """Dense VV time series at one Galveston point — look for outliers."""
    try:
        pt = GALVESTON_PT.buffer(200)
        col = s1_vvvh(pt, "2022-01-01", "2024-01-01")

        def f(im):
            m = im.select("VV").reduceRegion(ee.Reducer.mean(), pt, 20, maxPixels=1e6)
            return ee.Feature(None, {"VV": m.get("VV"), "t": im.date().format("YYYY-MM-dd"),
                                     "pass": im.get("orbitProperties_pass")})

        feats = col.map(f).getInfo()
        rows = [x["properties"] for x in feats.get("features", []) if x["properties"].get("VV") is not None]
        rows.sort(key=lambda r: r["t"])
        vals = [r["VV"] for r in rows]
        if vals:
            mean = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
            outliers = [r for r in rows if abs(r["VV"] - mean) > 2.5 * sd]
            mn, mx = min(vals), max(vals)
        else:
            mean = sd = mn = mx = None
            outliers = []
        log(
            "timeseries_galveston_point_VV",
            True,
            {"point": [-94.80, 29.30], "period": "2022-2023"},
            {
                "n": len(rows),
                "mean": mean,
                "std": sd,
                "min": mn,
                "max": mx,
                "n_outliers_2p5sd": len(outliers),
                "outlier_sample": outliers[:10],
                "first_last": (rows[0], rows[-1]) if rows else None,
            },
            notes=f"n={len(rows)} VV samples; range [{mn},{mx}] dB; outliers={len(outliers)}",
        )
    except Exception as e:
        log("timeseries_galveston_point_VV", False, {}, error=str(e))


def write_summary():
    ok = sum(1 for e in experiments if e["ok"])
    fail = sum(1 for e in experiments if not e["ok"])
    lines = [
        "# Deep Radar Exploration Findings",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Experiments: {len(experiments)} (ok={ok}, fail={fail})",
        "",
        "## Experiment index",
        "",
    ]
    for e in experiments:
        mark = "OK" if e["ok"] else "FAIL"
        lines.append(f"- **{mark}** `{e['name']}` — {e.get('notes') or e.get('error') or ''}")
    SUMMARY_PATH.write_text("\n".join(lines))
    print(f"\nWrote {LOG_PATH} and {SUMMARY_PATH} ({len(experiments)} experiments)")


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("=== Phase 1: catalog loads ===")
    probe_catalog_loads()

    print("=== Phase 2: core S1 ===")
    probe_s1_coverage_galveston()
    probe_vv_vh_contrast()
    probe_asc_vs_desc()
    probe_dualpol_ratios()
    probe_incidence_angle_effect()
    probe_float_vs_db()
    probe_orbit_mosaic_artifacts()
    probe_urban_double_bounce()
    probe_speckle_filtering()

    print("=== Phase 3: flood / change ===")
    flood_info = probe_harvey_flood()
    if flood_info:
        probe_harvey_followups(flood_info)
    probe_ms_river_flood()
    probe_change_detection_port()
    probe_seasonal_composites()

    print("=== Phase 4: ships / ocean ===")
    ship_info = probe_ship_detection()
    if ship_info:
        probe_ship_followups(ship_info)
    probe_wind_roughened_sea()

    print("=== Phase 5: interferometry-adjacent + other SAR ===")
    probe_coherence_dataset()
    probe_try_insar_slc()
    probe_opera_rtc()
    probe_opera_dswx()
    probe_alos_palsar()
    probe_lhscat()
    probe_gimp_radarsat()
    probe_fnf_forest()
    probe_cross_sensor_s1_vs_alos()
    probe_time_series_vv_point()

    print("=== Phase 6: intentional fails ===")
    probe_fail_intentionally()

    write_summary()
    print(f"Elapsed: {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
