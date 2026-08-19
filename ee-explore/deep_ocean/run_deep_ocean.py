#!/usr/bin/env python3
"""Deep EE ocean / coastal / weird exploration. Thumbs + JSON. No product pitch."""

from __future__ import annotations

import json
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
OUT = Path(__file__).resolve().parent
THUMBS = OUT / "thumbs"
THUMBS.mkdir(parents=True, exist_ok=True)

# Regions filled after ee.Initialize()
GULF = GALV_BAY = CHESAPEAKE = SF_BAY = GULF_OPEN = None
HAWAII = ALASKA_BEAUFORT = BERING = SAN_LEON = None
TX_COAST = FL_KEYS = MISS_DELTA = None


def init_regions():
    global GULF, GALV_BAY, CHESAPEAKE, SF_BAY, GULF_OPEN, HAWAII
    global ALASKA_BEAUFORT, BERING, SAN_LEON, TX_COAST, FL_KEYS, MISS_DELTA
    GULF = ee.Geometry.Rectangle([-97.5, 26.0, -88.0, 30.5])
    GALV_BAY = ee.Geometry.Rectangle([-95.2, 29.2, -94.6, 29.75])
    CHESAPEAKE = ee.Geometry.Rectangle([-76.6, 37.0, -75.8, 39.4])
    SF_BAY = ee.Geometry.Rectangle([-122.55, 37.4, -121.9, 38.15])
    GULF_OPEN = ee.Geometry.Point([-93.0, 27.0]).buffer(50000)
    HAWAII = ee.Geometry.Rectangle([-160.5, 18.5, -154.5, 22.5])
    ALASKA_BEAUFORT = ee.Geometry.Rectangle([-155.0, 70.0, -140.0, 72.5])
    BERING = ee.Geometry.Rectangle([-175.0, 55.0, -160.0, 65.0])
    SAN_LEON = ee.Geometry.Point([-94.96653315875905, 29.475732110989398])
    TX_COAST = ee.Geometry.Rectangle([-97.5, 25.8, -93.5, 30.0])
    FL_KEYS = ee.Geometry.Rectangle([-81.9, 24.4, -80.2, 25.2])
    MISS_DELTA = ee.Geometry.Rectangle([-90.0, 28.8, -88.8, 29.6])


results: dict = {
    "project": PROJECT,
    "ran_at": datetime.now(timezone.utc).isoformat(),
    "prior_context": (
        "Builds on ee-explore/gee_deep_coastal_ocean.json, gee_extra_coastal.json, "
        "gee_probe_results.json, gee_explore_round4.json. Prior: MODIS chl works; "
        "VIIRS path failed; OLCI window empty; HYCOM/OISST/Murray/ETOPO/FABDEM known."
    ),
    "asset_smoke": {},
    "experiments": {},
    "thumbs": {},
    "whoa": [],
}


def ok(x):
    return x is not None


def safe_getinfo(obj, label=""):
    try:
        return obj.getInfo(), None
    except Exception as e:
        return None, f"{label}: {e}"[:400]


def reduce_mean(img, geom, scale, max_pixels=1e7):
    return img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale,
        maxPixels=max_pixels,
        bestEffort=True,
    )


def reduce_pct(img, geom, scale, pcts=(10, 50, 90), max_pixels=1e7):
    return img.reduceRegion(
        reducer=ee.Reducer.percentile(list(pcts)),
        geometry=geom,
        scale=scale,
        maxPixels=max_pixels,
        bestEffort=True,
    )


def download_thumb(url: str, path: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, path)
        return path.exists() and path.stat().st_size > 200
    except Exception:
        return False


def make_thumb(img, region, vis, name, dimensions=640):
    try:
        url = img.getThumbURL(
            {
                "region": region,
                "dimensions": dimensions,
                "format": "png",
                **vis,
            }
        )
        path = THUMBS / f"{name}.png"
        ok_dl = download_thumb(url, path)
        results["thumbs"][name] = {
            "ok": ok_dl,
            "path": str(path) if ok_dl else None,
            "url": url[:120] + "...",
        }
        return ok_dl
    except Exception as e:
        results["thumbs"][name] = {"ok": False, "error": str(e)[:300]}
        return False


def smoke_asset(name: str, asset_id: str, kind_hint: str | None = None):
    """Try ImageCollection / Image / FeatureCollection load."""
    entry = {"id": asset_id, "ok": False}
    loaders = []
    if kind_hint == "Image":
        loaders = [("Image", ee.Image), ("ImageCollection", ee.ImageCollection), ("FeatureCollection", ee.FeatureCollection)]
    elif kind_hint == "FeatureCollection":
        loaders = [("FeatureCollection", ee.FeatureCollection), ("ImageCollection", ee.ImageCollection), ("Image", ee.Image)]
    else:
        loaders = [("ImageCollection", ee.ImageCollection), ("Image", ee.Image), ("FeatureCollection", ee.FeatureCollection)]

    errors = []
    for kind, loader in loaders:
        try:
            obj = loader(asset_id)
            if kind == "ImageCollection":
                first = obj.first()
                bands = first.bandNames().getInfo()
                # count in a short window if possible
                try:
                    n = obj.limit(3).size().getInfo()
                except Exception:
                    n = None
                entry.update(ok=True, type=kind, bands=bands, sample_n=n)
            elif kind == "Image":
                bands = obj.bandNames().getInfo()
                entry.update(ok=True, type=kind, bands=bands, n_bands=len(bands))
            else:
                n = obj.limit(3).size().getInfo()
                props = obj.limit(1).first().propertyNames().getInfo() if n else []
                entry.update(ok=True, type=kind, sample_n=n, sample_props=props[:20])
            break
        except Exception as e:
            errors.append(f"{kind}: {str(e)[:180]}")
    if not entry["ok"]:
        entry["errors"] = errors
    results["asset_smoke"][name] = entry
    print(f"  smoke {'OK' if entry['ok'] else 'FAIL'}: {name} ({asset_id})")
    return entry


def exp(name: str, fn):
    print(f"\n=== EXP {name} ===")
    try:
        out = fn()
        results["experiments"][name] = {"ok": True, **(out or {})}
        print(f"  done: {name}")
    except Exception as e:
        results["experiments"][name] = {
            "ok": False,
            "error": str(e)[:500],
            "trace": traceback.format_exc()[-800:],
        }
        print(f"  FAIL {name}: {e}")


# ---------------------------------------------------------------------------
# Asset smoke battery (many IDs)
# ---------------------------------------------------------------------------
ASSET_CANDIDATES = [
    ("modis_aqua_l3smi", "NASA/OCEANDATA/MODIS-Aqua/L3SMI"),
    ("modis_terra_l3smi", "NASA/OCEANDATA/MODIS-Terra/L3SMI"),
    ("seawifs_l3smi", "NASA/OCEANDATA/SeaWiFS/L3SMI"),
    ("viirs_l3smi_old", "NASA/OCEANDATA/VIIRS/L3SMI"),
    ("viirs_snpp_l3smi", "NASA/OCEANDATA/VIIRS-SNPP/L3SMI"),
    ("jaxa_chla_v3", "JAXA/GCOM-C/L3/OCEAN/CHLA/V3"),
    ("jaxa_sst_v3", "JAXA/GCOM-C/L3/OCEAN/SST/V3"),
    ("jaxa_chla_v2", "JAXA/GCOM-C/L3/OCEAN/CHLA/V2"),
    ("copernicus_ocean_color_v6", "COPERNICUS/MARINE/SATELLITE_OCEAN_COLOR/V6"),
    ("copernicus_plankton_multi_4km", "COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_MULTI_4KM"),
    ("copernicus_plankton_olci_300m", "COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_OLCI_300M"),
    ("copernicus_optics_multi_4km", "COPERNICUS/MARINE/OC_GLO_BGC/OPTICS_MULTI_4KM"),
    ("copernicus_reflectance_multi_4km", "COPERNICUS/MARINE/OC_GLO_BGC/REFLECTANCE_MULTI_4KM"),
    ("copernicus_transparency_multi_4km", "COPERNICUS/MARINE/OC_GLO_BGC/TRANSPARENCY_MULTI_4KM"),
    ("copernicus_pp_multi_4km", "COPERNICUS/MARINE/OC_GLO_BGC/PRIMARY_PRODUCTION_MULTI_4KM"),
    ("copernicus_phy_daily", "COPERNICUS/MARINE/GLOBAL_ANALYSISFORECAST_PHY_DAILY"),
    ("copernicus_waves", "COPERNICUS/MARINE/WAV/ANFC_0_083DEG_PT3H"),
    ("copernicus_wave_bathy", "COPERNICUS/MARINE/WAV/ANFC_0_083DEG_STATIC"),
    ("ecmwf_ifs_wave", "ECMWF/NRT_FORECAST/IFS/WAVE"),
    ("oisst_v2_1", "NOAA/CDR/OISST/V2_1"),
    ("pathfinder_sst", "NOAA/CDR/SST_PATHFINDER/V53"),
    ("hycom_temp_sal", "HYCOM/sea_temp_salinity"),
    ("hycom_velocity", "HYCOM/sea_water_velocity"),
    ("hycom_ssh", "HYCOM/sea_surface_elevation"),
    ("etopo1", "NOAA/NGDC/ETOPO1", "Image"),
    ("gebco_sat_io", "projects/sat-io/open-datasets/gebco/gebco_grid"),
    ("fabdem", "projects/sat-io/open-datasets/FABDEM"),
    ("nasadem", "NASA/NASADEM_HGT/001", "Image"),
    ("murray_intertidal", "UQ/murray/Intertidal/v1_1/global_intertidal"),
    ("murray_datamask", "UQ/murray/Intertidal/v1_1/data_mask", "Image"),
    ("murray_qa", "UQ/murray/Intertidal/v1_1/qa_pixel_count"),
    ("landsat_mangrove", "LANDSAT/MANGROVE_FORESTS"),
    ("gmw_v3_extent", "projects/sat-io/open-datasets/GMW/extent/GMW_V3"),
    ("gmw_2020", "projects/sat-io/open-datasets/GMW/annual-extent/GMW_MNG_2020"),
    ("cgmd_extent30", "projects/mangrovedatahub2/assets/CGMD-Extent30", "FeatureCollection"),
    ("allen_coral_v2", "ACA/reef_habitat/v2_0", "Image"),
    ("modocga", "MODIS/006/MODOCGA"),
    ("mydocga_061", "MODIS/061/MYDOCGA"),
    ("grace_ocean", "NASA/GRACE/MASS_GRIDS_V04/OCEAN"),
    ("copernicus_sss_my", "COPERNICUS/MARINE/GLOBAL_MULTIYEAR_PHY_SSS_SSD_DAILY"),
    ("nsidc_g02135", "NOAA/NSIDC/G02135/north"),
    ("nsidc_g02202", "NOAA/NSIDC/G02202_V4"),
    ("copernicus_argo", "COPERNICUS/MARINE/INSITU_GLO_PHY_UV_DISCRETE_MY_NRT"),
]


def run_smoke():
    print("\n=== ASSET SMOKE ===")
    for item in ASSET_CANDIDATES:
        if len(item) == 2:
            name, aid = item
            smoke_asset(name, aid)
        else:
            name, aid, hint = item
            smoke_asset(name, aid, hint)


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
def exp_oisst_gulf_mhw():
    """SST + anomaly + simple marine heatwave proxy (anom > 1C for >=5 days)."""
    col = ee.ImageCollection("NOAA/CDR/OISST/V2_1").filterDate("2023-06-01", "2023-09-01").filterBounds(GULF)
    # scale factors: sst/anom * 0.01
    mean_sst = col.select("sst").mean().multiply(0.01)
    mean_anom = col.select("anom").mean().multiply(0.01)
    hot = col.map(lambda i: i.select("anom").multiply(0.01).gt(1).rename("hot"))
    hot_frac = hot.mean().select("hot")
    # consecutive-ish proxy: count of hot days in Aug
    aug = col.filterDate("2023-08-01", "2023-09-01")
    hot_days = aug.map(lambda i: i.select("anom").multiply(0.01).gt(1)).sum().rename("hot_days")

    stats = ee.Dictionary(
        {
            "mean_sst_c": reduce_mean(mean_sst, GULF, 25000),
            "mean_anom_c": reduce_mean(mean_anom, GULF, 25000),
            "hot_frac_jun_aug": reduce_mean(hot_frac, GULF, 25000),
            "aug_hot_days_mean": reduce_mean(hot_days, GULF, 25000),
            "galv_aug_hot_days": reduce_mean(hot_days, GALV_BAY, 25000),
            "open_gulf_aug_hot_days": reduce_mean(hot_days, GULF_OPEN, 25000),
        }
    ).getInfo()

    make_thumb(
        mean_anom,
        GULF,
        {"min": -2, "max": 2, "palette": ["0000aa", "ffffff", "aa0000"]},
        "gulf_oisst_anom_jja2023",
    )
    make_thumb(
        hot_days.clip(GULF),
        GULF,
        {"min": 0, "max": 25, "palette": ["ffffcc", "fd8d3c", "800026"]},
        "gulf_mhw_hot_days_aug2023",
    )
    if (stats.get("aug_hot_days_mean") or {}).get("hot_days", 0) > 10:
        results["whoa"].append(
            "Gulf Aug 2023 OISST: large fraction of days with anom>1C — marine heatwave proxy lights up."
        )
    return {"stats": stats, "note": "MHW proxy = days with OISST anom>1C; not Hobday full definition"}


def exp_oisst_vs_pathfinder():
    oisst = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate("2023-08-01", "2023-08-15")
        .select("sst")
        .mean()
        .multiply(0.01)
    )
    pf = (
        ee.ImageCollection("NOAA/CDR/SST_PATHFINDER/V53")
        .filterDate("2023-08-01", "2023-08-15")
        .select("sea_surface_temperature")
        .mean()
    )
    # Pathfinder often Kelvin or scaled — check sample
    sample = ee.Dictionary(
        {
            "oisst": reduce_mean(oisst, GULF_OPEN, 25000),
            "pathfinder_raw": reduce_mean(pf, GULF_OPEN, 25000),
            "diff_raw": reduce_mean(oisst.subtract(pf), GULF_OPEN, 25000),
        }
    ).getInfo()
    return {"sample": sample}


def exp_ocean_color_multi_source():
    """Compare chl across working sources for Galveston Bay vs open Gulf, Aug 2023."""
    start, end = "2023-08-01", "2023-09-01"
    sources = {
        "modis_aqua": ("NASA/OCEANDATA/MODIS-Aqua/L3SMI", "chlor_a", 5000),
        "modis_terra": ("NASA/OCEANDATA/MODIS-Terra/L3SMI", "chlor_a", 5000),
        "copernicus_v6": ("COPERNICUS/MARINE/SATELLITE_OCEAN_COLOR/V6", "chlor_a", 5000),
        "globcolour_multi": ("COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_MULTI_4KM", "CHL", 5000),
        "globcolour_olci300": ("COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_OLCI_300M", "CHL", 1000),
        "jaxa_chla": ("JAXA/GCOM-C/L3/OCEAN/CHLA/V3", "CHLA_AVE", 5000),
    }
    out = {}
    for key, (aid, band, scale) in sources.items():
        try:
            col = ee.ImageCollection(aid).filterDate(start, end)
            # JAXA scale: CHLA often needs *0.0015 or similar — record raw
            img = col.select(band).mean()
            n = col.filterBounds(GALV_BAY).size().getInfo()
            galv = reduce_mean(img, GALV_BAY, scale).getInfo()
            gulf = reduce_mean(img, GULF_OPEN, scale).getInfo()
            out[key] = {"n_galv_scenes": n, "galv": galv, "open_gulf": gulf, "band": band, "id": aid}
        except Exception as e:
            out[key] = {"error": str(e)[:300], "id": aid}
    # thumbs for best sources
    try:
        mod = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(start, end).select("chlor_a").mean()
        make_thumb(
            mod.log10().clip(GULF),
            GULF,
            {"min": -1.5, "max": 1.5, "palette": ["0b2460", "1e90ff", "00ff7f", "ffff00", "ff4500", "8b0000"]},
            "gulf_modis_chl_log_aug2023",
        )
        gc = (
            ee.ImageCollection("COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_MULTI_4KM")
            .filterDate(start, end)
            .select("CHL")
            .mean()
        )
        make_thumb(
            gc.log10().clip(GULF),
            GULF,
            {"min": -1.5, "max": 1.5, "palette": ["0b2460", "1e90ff", "00ff7f", "ffff00", "ff4500", "8b0000"]},
            "gulf_globcolour_chl_log_aug2023",
        )
    except Exception as e:
        out["thumb_error"] = str(e)[:200]
    # ratio bay/gulf
    try:
        ma = out.get("modis_aqua", {})
        gch = (ma.get("galv") or {}).get("chlor_a")
        och = (ma.get("open_gulf") or {}).get("chlor_a")
        if gch and och and och > 0:
            ratio = gch / och
            out["modis_bay_to_gulf_ratio"] = ratio
            if ratio > 50:
                results["whoa"].append(
                    f"MODIS Aug 2023: Galveston Bay chl ~{ratio:.0f}x open Gulf ({gch:.1f} vs {och:.3f} mg/m3)."
                )
    except Exception:
        pass
    return {"compare": out}


def exp_olci_300m_dig():
    """Prior empty window — dig why; try alternate dates / Hawaii / Chesapeake."""
    aid = "COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_OLCI_300M"
    col = ee.ImageCollection(aid)
    windows = [
        ("2023-08-01", "2023-08-15", GALV_BAY, "galv_aug2023"),
        ("2024-06-01", "2024-06-15", GALV_BAY, "galv_jun2024"),
        ("2024-06-01", "2024-06-15", CHESAPEAKE, "ches_jun2024"),
        ("2024-06-01", "2024-06-15", HAWAII, "hawaii_jun2024"),
        ("2022-07-01", "2022-07-31", GULF, "gulf_jul2022"),
    ]
    out = {}
    for a, b, geom, label in windows:
        sub = col.filterDate(a, b).filterBounds(geom)
        n = sub.size().getInfo()
        mean_chl = None
        if n:
            mean_chl = reduce_mean(sub.select("CHL").mean(), geom, 500).getInfo()
        out[label] = {"n": n, "chl": mean_chl, "window": [a, b]}
    # date range of collection
    try:
        first = col.sort("system:time_start").first().date().format("YYYY-MM-dd").getInfo()
        last = col.sort("system:time_start", False).first().date().format("YYYY-MM-dd").getInfo()
        out["collection_span"] = [first, last]
    except Exception as e:
        out["span_error"] = str(e)[:200]
    if any(v.get("n", 0) > 0 and v.get("chl") for v in out.values() if isinstance(v, dict) and "n" in v):
        results["whoa"].append(
            "OLCI 300m GlobColour DOES have data — prior empty was date/region filter, not missing asset."
        )
        # thumb best
        best = max(
            [(k, v) for k, v in out.items() if isinstance(v, dict) and v.get("n")],
            key=lambda kv: kv[1]["n"],
            default=None,
        )
        if best:
            label, meta = best
            a, b = meta["window"]
            geom = {"galv_aug2023": GALV_BAY, "galv_jun2024": GALV_BAY, "ches_jun2024": CHESAPEAKE,
                    "hawaii_jun2024": HAWAII, "gulf_jul2022": GULF}[label]
            img = col.filterDate(a, b).filterBounds(geom).select("CHL").mean()
            make_thumb(
                img.log10(),
                geom,
                {"min": -1, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
                f"olci300_{label}",
            )
    return out


def exp_hycom_profiles_and_velocity():
    """Temp/salinity depth structure + surface currents in Gulf."""
    ts = (
        ee.ImageCollection("HYCOM/sea_temp_salinity")
        .filterDate("2023-08-01", "2023-08-08")
        .filterBounds(GULF_OPEN)
        .mean()
    )
    # scale: *0.001, offset for temp often +20 in older docs — check catalog: scale 0.001 offset 20 for temp?
    # From EE catalog: water_temp scale 0.001 offset 20; salinity scale 0.001 offset 20
    depths = [0, 10, 50, 100, 200]
    profile = {}
    for d in depths:
        tband = f"water_temp_{d}"
        sband = f"salinity_{d}"
        try:
            t = ts.select(tband).multiply(0.001).add(20)
            s = ts.select(sband).multiply(0.001).add(20)
            profile[f"d{d}"] = {
                "temp_c": reduce_mean(t, GULF_OPEN, 10000).getInfo(),
                "sal_psu": reduce_mean(s, GULF_OPEN, 10000).getInfo(),
            }
        except Exception as e:
            profile[f"d{d}"] = {"error": str(e)[:200]}

    vel = (
        ee.ImageCollection("HYCOM/sea_water_velocity")
        .filterDate("2023-08-01", "2023-08-08")
        .mean()
    )
    u = vel.select("velocity_u_0").multiply(0.001)
    v = vel.select("velocity_v_0").multiply(0.001)
    speed = u.hypot(v).rename("speed")
    ssh = (
        ee.ImageCollection("HYCOM/sea_surface_elevation")
        .filterDate("2023-08-01", "2023-08-08")
        .mean()
        .select("surface_elevation")
        .multiply(0.001)
    )
    flow = ee.Dictionary(
        {
            "speed_open": reduce_mean(speed, GULF_OPEN, 10000),
            "u_open": reduce_mean(u, GULF_OPEN, 10000),
            "v_open": reduce_mean(v, GULF_OPEN, 10000),
            "ssh_open": reduce_mean(ssh, GULF_OPEN, 10000),
            "speed_nearshore": reduce_mean(speed, ee.Geometry.Point([-94.9, 28.9]).buffer(20000), 10000),
        }
    ).getInfo()

    make_thumb(
        speed.clip(GULF),
        GULF,
        {"min": 0, "max": 0.8, "palette": ["081d58", "253494", "41b6c4", "ffffcc"]},
        "gulf_hycom_speed_aug2023",
    )
    make_thumb(
        ts.select("salinity_0").multiply(0.001).add(20).clip(GULF),
        GULF,
        {"min": 28, "max": 37, "palette": ["f7fcf5", "74c476", "00441b"]},
        "gulf_hycom_sal0_aug2023",
    )

    # Loop Current sniff: high speed SE Gulf
    lc = ee.Geometry.Rectangle([-88, 24, -84, 27])
    lc_speed = reduce_mean(speed, lc, 10000).getInfo()
    if (lc_speed or {}).get("speed", 0) > 0.4:
        results["whoa"].append(
            f"HYCOM Aug 2023: SE Gulf speed ~{(lc_speed or {}).get('speed'):.2f} m/s — Loop Current signature."
        )
    return {"profile_open_gulf": profile, "flow": flow, "loop_current_box_speed": lc_speed}


def exp_murray_intertidal_change():
    col = ee.ImageCollection("UQ/murray/Intertidal/v1_1/global_intertidal")
    first = col.sort("system:index").first()
    last = col.sort("system:index", False).first()
    # classification==1 is tidal flat
    fmask = first.eq(1)
    lmask = last.eq(1)
    lost = fmask.And(lmask.Not()).rename("lost")
    gained = lmask.And(fmask.Not()).rename("gained")
    # area proxies via pixel counts
    scale = 30

    def area_km2(mask, geom):
        # count pixels * 30*30 / 1e6
        stats = mask.multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), geom, scale, maxPixels=1e9, bestEffort=True
        )
        return stats

    out = {
        "first_id": first.get("system:index").getInfo(),
        "last_id": last.get("system:index").getInfo(),
        "galv": {
            "first_flat_m2": area_km2(fmask, GALV_BAY).getInfo(),
            "last_flat_m2": area_km2(lmask, GALV_BAY).getInfo(),
            "lost_m2": area_km2(lost, GALV_BAY).getInfo(),
            "gained_m2": area_km2(gained, GALV_BAY).getInfo(),
        },
        "sf_bay": {
            "first_flat_m2": area_km2(fmask, SF_BAY).getInfo(),
            "last_flat_m2": area_km2(lmask, SF_BAY).getInfo(),
            "lost_m2": area_km2(lost, SF_BAY).getInfo(),
            "gained_m2": area_km2(gained, SF_BAY).getInfo(),
        },
        "chesapeake": {
            "first_flat_m2": area_km2(fmask, CHESAPEAKE).getInfo(),
            "last_flat_m2": area_km2(lmask, CHESAPEAKE).getInfo(),
        },
    }
    # visualize loss/gain around Galveston
    rgb = ee.Image.cat(
        lost.multiply(255),
        gained.multiply(255),
        fmask.Or(lmask).multiply(80),
    ).rename(["r", "g", "b"])
    make_thumb(rgb.clip(TX_COAST), TX_COAST, {"min": 0, "max": 255, "bands": ["r", "g", "b"]}, "tx_murray_loss_gain")
    make_thumb(
        last.clip(GALV_BAY),
        GALV_BAY,
        {"min": 0, "max": 2, "palette": ["000000", "c2b280", "0000aa"]},
        "galv_murray_2014_2016",
    )
    return out


def exp_mangroves_multi():
    """LANDSAT mangrove 2000, GMW, CGMD Texas / Florida Keys."""
    out = {}
    # Giri 2000
    giri = ee.Image("LANDSAT/MANGROVE_FORESTS/2000").select("1")
    out["giri_2000_tx_pixels"] = giri.gt(0).reduceRegion(
        ee.Reducer.sum(), TX_COAST, 30, maxPixels=1e9, bestEffort=True
    ).getInfo()
    out["giri_2000_keys_pixels"] = giri.gt(0).reduceRegion(
        ee.Reducer.sum(), FL_KEYS, 30, maxPixels=1e9, bestEffort=True
    ).getInfo()

    # GMW 2020
    gmw = ee.ImageCollection("projects/sat-io/open-datasets/GMW/annual-extent/GMW_MNG_2020").mosaic()
    out["gmw_2020_tx"] = gmw.gt(0).multiply(ee.Image.pixelArea()).reduceRegion(
        ee.Reducer.sum(), TX_COAST, 20, maxPixels=1e9, bestEffort=True
    ).getInfo()
    out["gmw_2020_keys"] = gmw.gt(0).multiply(ee.Image.pixelArea()).reduceRegion(
        ee.Reducer.sum(), FL_KEYS, 20, maxPixels=1e9, bestEffort=True
    ).getInfo()

    # CGMD FC yearly TX area
    try:
        cgmd = ee.FeatureCollection("projects/mangrovedatahub2/assets/CGMD-Extent30")
        tx = ee.Geometry.Rectangle([-97.5, 25.8, -93.5, 30.0])
        for year in (1984, 2000, 2010, 2020, 2023):
            sub = cgmd.filter(ee.Filter.eq("year", year)).filterBounds(tx)
            out[f"cgmd_tx_{year}"] = {
                "n": sub.size().getInfo(),
                "area_km2": sub.aggregate_sum("area_km2").getInfo(),
            }
    except Exception as e:
        out["cgmd_error"] = str(e)[:300]

    make_thumb(
        gmw.selfMask().clip(FL_KEYS),
        FL_KEYS,
        {"min": 0, "max": 1, "palette": ["004d00"]},
        "florida_keys_gmw_2020",
    )
    make_thumb(
        giri.selfMask().clip(TX_COAST),
        TX_COAST,
        {"min": 0, "max": 1, "palette": ["006400"]},
        "tx_giri_mangrove_2000",
    )

    # Texas mangrove growth story from prior
    if out.get("cgmd_tx_1984") and out.get("cgmd_tx_2023"):
        a0 = out["cgmd_tx_1984"].get("area_km2") or 0
        a1 = out["cgmd_tx_2023"].get("area_km2") or 0
        if a0 and a1 and a1 > a0 * 2:
            results["whoa"].append(
                f"CGMD Texas mangroves: {a0:.2f} → {a1:.2f} km² (1984→2023) — large expansion."
            )
    return out


def exp_allen_coral_seagrass():
    """Allen Coral Atlas benthic classes — seagrass proxy in Keys / Hawaii."""
    img = ee.Image("ACA/reef_habitat/v2_0")
    bands = img.bandNames().getInfo()
    benthic = img.select("benthic")
    # Class values from ACA docs (approx): 11 Seagrass, 12 Macroalgae, 13 Coral/Algae, etc.
    # We'll histogram instead of assuming
    hist_keys = benthic.reduceRegion(
        ee.Reducer.frequencyHistogram(), FL_KEYS, 30, maxPixels=1e8, bestEffort=True
    ).getInfo()
    hist_hi = benthic.reduceRegion(
        ee.Reducer.frequencyHistogram(),
        ee.Geometry.Rectangle([-158.3, 21.2, -157.6, 21.7]),  # Oahu south shore
        30,
        maxPixels=1e8,
        bestEffort=True,
    ).getInfo()
    make_thumb(
        benthic.clip(FL_KEYS),
        FL_KEYS,
        {"min": 0, "max": 20, "palette": ["000000", "1f78b4", "33a02c", "e31a1c", "ff7f00", "ffff99"]},
        "florida_keys_aca_benthic",
    )
    make_thumb(
        img.select("geomorphic").clip(HAWAII),
        ee.Geometry.Rectangle([-158.3, 21.2, -157.6, 21.7]),
        {"min": 0, "max": 20, "palette": ["0d0887", "6a00a8", "b12a90", "e16462", "fca636", "f0f921"]},
        "oahu_aca_geomorphic",
    )
    # Galveston — expect almost empty (no coral reef)
    hist_galv = benthic.reduceRegion(
        ee.Reducer.frequencyHistogram(), GALV_BAY, 30, maxPixels=1e8, bestEffort=True
    ).getInfo()
    results["whoa"].append(
        "Allen Coral Atlas (ACA/reef_habitat/v2_0) exposes benthic classes incl. seagrass — rare EE habitat layer."
    )
    return {"bands": bands, "hist_keys": hist_keys, "hist_oahu": hist_hi, "hist_galv": hist_galv}


def exp_bathymetry_stack():
    etopo = ee.Image("NOAA/NGDC/ETOPO1").select("bedrock")
    gebco = ee.ImageCollection("projects/sat-io/open-datasets/gebco/gebco_grid").mosaic().rename("gebco")
    wave_bathy = ee.ImageCollection("COPERNICUS/MARINE/WAV/ANFC_0_083DEG_STATIC").first().select("deptho")
    nasadem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    fabdem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("fab")

    pts = {
        "san_leon": SAN_LEON,
        "galv_channel": ee.Geometry.Point([-94.78, 29.34]),
        "shelf_50m": ee.Geometry.Point([-94.5, 28.5]),
        "deep_gulf": ee.Geometry.Point([-90.0, 25.5]),
        "hawaii_maui_channel": ee.Geometry.Point([-156.5, 21.0]),
    }
    samples = {}
    for name, pt in pts.items():
        samples[name] = ee.Dictionary(
            {
                "etopo": etopo.reduceRegion(ee.Reducer.first(), pt, 2000),
                "gebco": gebco.reduceRegion(ee.Reducer.first(), pt, 500),
                "wave_deptho": wave_bathy.reduceRegion(ee.Reducer.first(), pt, 10000),
                "nasadem": nasadem.reduceRegion(ee.Reducer.first(), pt, 30),
                "fabdem": fabdem.reduceRegion(ee.Reducer.first(), pt, 30),
            }
        ).getInfo()

    # coastal DEM mismatch map around San Leon
    diff = fabdem.subtract(nasadem).rename("fab_minus_nasa")
    make_thumb(
        diff.clip(ee.Geometry.Point([-94.9665, 29.4757]).buffer(8000)),
        ee.Geometry.Point([-94.9665, 29.4757]).buffer(8000),
        {"min": -3, "max": 3, "palette": ["8b0000", "ffffff", "00008b"]},
        "san_leon_fabdem_minus_nasadem",
    )
    make_thumb(
        etopo.clip(GULF),
        GULF,
        {"min": -3000, "max": 50, "palette": ["08306b", "2171b5", "6baed6", "ffffcc", "238b45"]},
        "gulf_etopo_bedrock",
    )
    make_thumb(
        gebco.clip(GULF),
        GULF,
        {"min": -3000, "max": 50, "palette": ["08306b", "2171b5", "6baed6", "ffffcc", "238b45"]},
        "gulf_gebco",
    )

    # mismatch magnitude at San Leon
    sl = samples.get("san_leon", {})
    try:
        fab = (sl.get("fabdem") or {}).get("fab")
        nasa = (sl.get("nasadem") or {}).get("elevation")
        if fab is not None and nasa is not None and abs(fab - nasa) > 1:
            results["whoa"].append(
                f"San Leon DEM mismatch: FABDEM={fab:.2f}m vs NASADEM={nasa:.2f}m (Δ={fab-nasa:.2f}m) — coastal flood math flips."
            )
    except Exception:
        pass
    return {"samples": samples}


def exp_waves_gulf_vs_hawaii():
    waves = ee.ImageCollection("COPERNICUS/MARINE/WAV/ANFC_0_083DEG_PT3H").filterDate(
        "2024-01-10", "2024-01-20"
    )
    # VHM0 = significant wave height
    mean_hs = waves.select("VHM0").mean()
    ecmwf = (
        ee.ImageCollection("ECMWF/NRT_FORECAST/IFS/WAVE")
        .filterDate("2024-01-10", "2024-01-12")
        .select("significant_height_of_combined_wind_waves_and_swell_sfc")
        .mean()
    )
    stats = ee.Dictionary(
        {
            "copernicus_hs_gulf": reduce_mean(mean_hs, GULF, 10000),
            "copernicus_hs_hawaii": reduce_mean(mean_hs, HAWAII, 10000),
            "copernicus_hs_bering": reduce_mean(mean_hs, BERING, 10000),
            "ecmwf_hs_gulf": reduce_mean(ecmwf, GULF, 25000),
            "ecmwf_hs_hawaii": reduce_mean(ecmwf, HAWAII, 25000),
            "n_copernicus": waves.size(),
            "n_ecmwf": ee.ImageCollection("ECMWF/NRT_FORECAST/IFS/WAVE")
            .filterDate("2024-01-10", "2024-01-12")
            .size(),
        }
    ).getInfo()
    make_thumb(
        mean_hs.clip(ee.Geometry.Rectangle([-180, -60, 180, 60])),
        ee.Geometry.Rectangle([-160, 15, -60, 50]),
        {"min": 0, "max": 5, "palette": ["08306b", "2171b5", "6baed6", "ffffb2", "fd8d3c", "b10026"]},
        "pacific_atlantic_wave_hs_jan2024",
    )
    hi = (stats.get("copernicus_hs_hawaii") or {}).get("VHM0")
    gu = (stats.get("copernicus_hs_gulf") or {}).get("VHM0")
    if hi and gu and hi > gu * 1.5:
        results["whoa"].append(
            f"Waves Jan 2024: Hawaii Hs≈{hi:.2f}m vs Gulf≈{gu:.2f}m — Pacific swell regime visible in EE."
        )
    return {"stats": stats}


def s2_turbidity_indices(geom, start, end, name):
    """NDTI / NDSSI from Sentinel-2 over water pixels."""
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start, end)
        .filterBounds(geom)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
    )

    def add_idx(img):
        # scale reflectance
        b = img.select(["B2", "B3", "B4", "B8"]).multiply(0.0001)
        # NDTI = (Red - Green)/(Red + Green)
        ndti = b.normalizedDifference(["B4", "B3"]).rename("ndti")
        # NDSSI = (Blue - NIR)/(Blue + NIR) — suspended sediment / clarity proxy
        ndssi = b.normalizedDifference(["B2", "B8"]).rename("ndssi")
        # NDWI water mask
        ndwi = b.normalizedDifference(["B3", "B8"]).rename("ndwi")
        return img.addBands([ndti, ndssi, ndwi])

    col = s2.map(add_idx)
    n = col.size().getInfo()
    if n == 0:
        return {"n": 0}
    med = col.select(["ndti", "ndssi", "ndwi"]).median()
    water = med.select("ndwi").gt(0.1)
    ndti_w = med.select("ndti").updateMask(water)
    ndssi_w = med.select("ndssi").updateMask(water)
    stats = ee.Dictionary(
        {
            "ndti": reduce_pct(ndti_w, geom, 20),
            "ndssi": reduce_pct(ndssi_w, geom, 20),
            "ndti_mean": reduce_mean(ndti_w, geom, 20),
            "ndssi_mean": reduce_mean(ndssi_w, geom, 20),
            "water_frac": reduce_mean(water, geom, 20),
        }
    ).getInfo()
    make_thumb(
        ndti_w.clip(geom),
        geom,
        {"min": -0.2, "max": 0.4, "palette": ["2166ac", "f7f7f7", "b2182b"]},
        f"ndti_{name}",
    )
    return {"n": n, "stats": stats}


def exp_estuary_turbidity_compare():
    # late summer / early fall — typically turbid
    windows = {
        "galveston": (GALV_BAY, "2023-09-01", "2023-10-15"),
        "chesapeake": (CHESAPEAKE, "2023-09-01", "2023-10-15"),
        "sf_bay": (SF_BAY, "2023-09-01", "2023-10-15"),
    }
    out = {}
    for name, (geom, a, b) in windows.items():
        out[name] = s2_turbidity_indices(geom, a, b, name)
    # whoa if Galveston much muddier
    try:
        g = out["galveston"]["stats"]["ndti_mean"]["ndti"]
        c = out["chesapeake"]["stats"]["ndti_mean"]["ndti"]
        s = out["sf_bay"]["stats"]["ndti_mean"]["ndti"]
        ranking = sorted([("galveston", g), ("chesapeake", c), ("sf_bay", s)], key=lambda x: -x[1])
        results["whoa"].append(
            f"S2 NDTI (turbidity proxy) Sep–Oct 2023: {ranking[0][0]} muddiest "
            f"({ranking[0][1]:.3f}) > {ranking[1][0]} ({ranking[1][1]:.3f}) > {ranking[2][0]} ({ranking[2][1]:.3f})."
        )
        out["ranking_ndti"] = ranking
    except Exception as e:
        out["rank_error"] = str(e)[:200]
    return out


def exp_hab_candidates():
    """High chl events — multi-source validation Gulf / Florida / Chesapeake."""
    # Florida red tide / Karenia often SW Florida shelf
    sw_fl = ee.Geometry.Rectangle([-83.0, 26.0, -81.5, 28.0])
    periods = [
        ("gulf_bloom_aug2023", GULF, "2023-08-01", "2023-08-20"),
        ("swfl_jul2023", sw_fl, "2023-07-01", "2023-07-31"),
        ("ches_aug2023", CHESAPEAKE, "2023-08-01", "2023-08-31"),
        ("galv_aug2023", GALV_BAY, "2023-08-01", "2023-08-31"),
    ]
    out = {}
    for label, geom, a, b in periods:
        mod = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(a, b).select("chlor_a")
        cop = ee.ImageCollection("COPERNICUS/MARINE/SATELLITE_OCEAN_COLOR/V6").filterDate(a, b).select("chlor_a")
        nflh = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(a, b).select("nflh")
        entry = {
            "modis_chl": reduce_pct(mod.mean(), geom, 5000).getInfo(),
            "modis_mean": reduce_mean(mod.mean(), geom, 5000).getInfo(),
            "copernicus_chl": reduce_pct(cop.mean(), geom, 5000).getInfo(),
            "modis_nflh": reduce_mean(nflh.mean(), geom, 5000).getInfo(),
            "n_modis": mod.filterBounds(geom).size().getInfo(),
        }
        out[label] = entry
        # thumb for SW FL
        if "swfl" in label:
            make_thumb(
                mod.mean().log10().clip(sw_fl),
                sw_fl,
                {"min": -1, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000", "800000"]},
                "swfl_modis_chl_jul2023",
            )
            make_thumb(
                nflh.mean().clip(sw_fl),
                sw_fl,
                {"min": -0.1, "max": 0.5, "palette": ["000000", "00ff00", "ffff00", "ff0000"]},
                "swfl_modis_nflh_jul2023",
            )
    # flag if SW FL elevated vs open gulf
    try:
        sw = out["swfl_jul2023"]["modis_mean"]["chlor_a"]
        og = reduce_mean(
            ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI")
            .filterDate("2023-07-01", "2023-07-31")
            .select("chlor_a")
            .mean(),
            GULF_OPEN,
            5000,
        ).getInfo()["chlor_a"]
        out["swfl_vs_open"] = {"swfl": sw, "open": og, "ratio": sw / og if og else None}
        if og and sw / og > 5:
            results["whoa"].append(
                f"HAB candidate Jul 2023: SW Florida MODIS chl {sw:.2f} vs open Gulf {og:.3f} "
                f"({sw/og:.0f}x); nflh also sampled for fluorescence corroboration."
            )
    except Exception as e:
        out["ratio_error"] = str(e)[:200]
    return out


def exp_arctic_ice():
    """Sea ice via OISST ice band + Copernicus PHY siconc — Alaska / Beaufort / Bering."""
    # Winter vs summer
    oisst_winter = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate("2024-02-01", "2024-02-15")
        .select("ice")
        .mean()
        .multiply(0.01)
    )
    oisst_summer = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate("2024-08-01", "2024-08-15")
        .select("ice")
        .mean()
        .multiply(0.01)
    )
    phy = ee.ImageCollection("COPERNICUS/MARINE/GLOBAL_ANALYSISFORECAST_PHY_DAILY")
    phy_w = phy.filterDate("2024-02-01", "2024-02-10").select("siconc").mean()
    phy_s = phy.filterDate("2024-08-01", "2024-08-10").select("siconc").mean()
    phy_th_w = phy.filterDate("2024-02-01", "2024-02-10").select("sithick").mean()

    stats = ee.Dictionary(
        {
            "oisst_ice_beaufort_feb": reduce_mean(oisst_winter, ALASKA_BEAUFORT, 25000),
            "oisst_ice_beaufort_aug": reduce_mean(oisst_summer, ALASKA_BEAUFORT, 25000),
            "oisst_ice_bering_feb": reduce_mean(oisst_winter, BERING, 25000),
            "oisst_ice_bering_aug": reduce_mean(oisst_summer, BERING, 25000),
            "phy_siconc_beaufort_feb": reduce_mean(phy_w, ALASKA_BEAUFORT, 10000),
            "phy_siconc_beaufort_aug": reduce_mean(phy_s, ALASKA_BEAUFORT, 10000),
            "phy_sithick_beaufort_feb": reduce_mean(phy_th_w, ALASKA_BEAUFORT, 10000),
            "hawaii_ice_should_be_null": reduce_mean(oisst_winter, HAWAII, 25000),
        }
    ).getInfo()

    make_thumb(
        oisst_winter.clip(ee.Geometry.Rectangle([-180, 50, -120, 75])),
        ee.Geometry.Rectangle([-180, 50, -120, 75]),
        {"min": 0, "max": 100, "palette": ["08306b", "6baed6", "ffffff"]},
        "alaska_oisst_ice_feb2024",
    )
    make_thumb(
        oisst_summer.clip(ee.Geometry.Rectangle([-180, 50, -120, 75])),
        ee.Geometry.Rectangle([-180, 50, -120, 75]),
        {"min": 0, "max": 100, "palette": ["08306b", "6baed6", "ffffff"]},
        "alaska_oisst_ice_aug2024",
    )
    make_thumb(
        phy_w.clip(ALASKA_BEAUFORT),
        ALASKA_BEAUFORT,
        {"min": 0, "max": 1, "palette": ["000033", "3182bd", "ffffff"]},
        "beaufort_phy_siconc_feb2024",
    )

    feb = (stats.get("oisst_ice_beaufort_feb") or {}).get("ice")
    aug = (stats.get("oisst_ice_beaufort_aug") or {}).get("ice")
    if feb is not None and aug is not None and feb > 50 and aug < 30:
        results["whoa"].append(
            f"Beaufort OISST ice: Feb≈{feb:.0f}% → Aug≈{aug:.0f}% — seasonal collapse visible; "
            "no dedicated NSIDC asset in EE, but OISST ice + Copernicus siconc/sithick fill the gap."
        )
    return {"stats": stats, "nsidc_note": "Dedicated NSIDC G02135/G02202 assets NOT in EE catalog for this project."}


def exp_hawaii_weird():
    """Hawaii: coral atlas + SST + chl + bathymetry channel."""
    sst = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate("2023-08-01", "2023-08-31")
        .select(["sst", "anom"])
        .mean()
        .multiply(0.01)
    )
    chl = (
        ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI")
        .filterDate("2023-08-01", "2023-08-31")
        .select("chlor_a")
        .mean()
    )
    gebco = ee.ImageCollection("projects/sat-io/open-datasets/gebco/gebco_grid").mosaic()
    aca = ee.Image("ACA/reef_habitat/v2_0")
    stats = ee.Dictionary(
        {
            "sst": reduce_mean(sst.select("sst"), HAWAII, 25000),
            "anom": reduce_mean(sst.select("anom"), HAWAII, 25000),
            "chl": reduce_mean(chl, HAWAII, 5000),
            "gebco_maui_channel": gebco.reduceRegion(
                ee.Reducer.first(), ee.Geometry.Point([-156.5, 21.0]), 500
            ),
            "aca_benthic_hist_oahu": aca.select("benthic").reduceRegion(
                ee.Reducer.frequencyHistogram(),
                ee.Geometry.Rectangle([-158.3, 21.2, -157.6, 21.7]),
                30,
                maxPixels=1e8,
                bestEffort=True,
            ),
        }
    ).getInfo()
    make_thumb(
        chl.log10().clip(HAWAII),
        HAWAII,
        {"min": -1.5, "max": 0.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
        "hawaii_modis_chl_aug2023",
    )
    make_thumb(
        sst.select("anom").clip(HAWAII),
        HAWAII,
        {"min": -2, "max": 2, "palette": ["0000aa", "ffffff", "aa0000"]},
        "hawaii_oisst_anom_aug2023",
    )
    return {"stats": stats}


def exp_mississippi_plume():
    """Chl + salinity front from Mississippi River plume."""
    a, b = "2023-05-01", "2023-05-31"  # spring flood season
    chl = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(a, b).select("chlor_a").mean()
    sal = (
        ee.ImageCollection("HYCOM/sea_temp_salinity")
        .filterDate(a, b)
        .select("salinity_0")
        .mean()
        .multiply(0.001)
        .add(20)
    )
    box = ee.Geometry.Rectangle([-92.5, 27.5, -87.5, 30.5])
    # transect west to east from river mouth
    transect = []
    for lon in [-90.5, -90.0, -89.5, -89.0, -88.5, -88.0, -87.5]:
        pt = ee.Geometry.Point([lon, 28.8])
        transect.append(
            {
                "lon": lon,
                "chl": chl.reduceRegion(ee.Reducer.mean(), pt.buffer(15000), 5000).getInfo(),
                "sal": sal.reduceRegion(ee.Reducer.mean(), pt.buffer(15000), 10000).getInfo(),
            }
        )
    make_thumb(
        chl.log10().clip(box),
        box,
        {"min": -1, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
        "miss_plume_chl_may2023",
    )
    make_thumb(
        sal.clip(box),
        box,
        {"min": 20, "max": 36, "palette": ["084081", "2b8cbe", "7bccc4", "f7fcf0"]},
        "miss_plume_sal_may2023",
    )
    # whoa if fresh+green near mouth
    try:
        near = transect[1]
        far = transect[-1]
        if near["sal"]["salinity_0"] < far["sal"]["salinity_0"] - 3:
            results["whoa"].append(
                f"Mississippi May 2023 plume: salinity {near['sal']['salinity_0']:.1f}→{far['sal']['salinity_0']:.1f} PSU "
                f"offshore; chl {near['chl'].get('chlor_a')} vs {far['chl'].get('chlor_a')}."
            )
    except Exception:
        pass
    return {"transect": transect}


def exp_grace_ocean_mass():
    col = ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/OCEAN")
    # sample recent
    img = col.sort("system:time_start", False).first()
    bands = img.bandNames().getInfo()
    date = img.date().format("YYYY-MM-dd").getInfo()
    # lwe_thickness typically
    band = bands[0]
    stats = {
        "date": date,
        "bands": bands,
        "gulf": reduce_mean(img.select(band), GULF, 50000).getInfo(),
        "pacific": reduce_mean(img.select(band), ee.Geometry.Point([-140, 0]).buffer(5e5), 50000).getInfo(),
    }
    make_thumb(
        img.select(band),
        ee.Geometry.Rectangle([-180, -60, 180, 60]),
        {"min": -20, "max": 20, "palette": ["053061", "f7f7f7", "67001f"]},
        "grace_ocean_mass_latest",
    )
    results["whoa"].append(
        f"GRACE ocean mass grids in EE ({band} on {date}) — weird gravity/ocean stack beyond SST/color."
    )
    return stats


def exp_copernicus_optics_transparency():
    """Kd/ZSD style transparency if available — estuary clarity."""
    out = {}
    for aid, band_guess in [
        ("COPERNICUS/MARINE/OC_GLO_BGC/TRANSPARENCY_MULTI_4KM", None),
        ("COPERNICUS/MARINE/OC_GLO_BGC/OPTICS_MULTI_4KM", None),
    ]:
        try:
            col = ee.ImageCollection(aid).filterDate("2023-08-01", "2023-09-01")
            first = col.first()
            bands = first.bandNames().getInfo()
            img = col.mean()
            entry = {"bands": bands, "n": col.size().getInfo()}
            for b in bands[:4]:
                entry[b] = {
                    "galv": reduce_mean(img.select(b), GALV_BAY, 5000).getInfo(),
                    "open": reduce_mean(img.select(b), GULF_OPEN, 5000).getInfo(),
                }
            out[aid] = entry
            # thumb first band
            b0 = bands[0]
            make_thumb(
                img.select(b0).clip(GULF),
                GULF,
                {"min": 0, "max": 1, "palette": ["ffffcc", "41b6c4", "0c2c84"]},
                f"optics_{b0}_gulf",
            )
        except Exception as e:
            out[aid] = {"error": str(e)[:300]}
    return out


def exp_hycom_galveston_null_mystery():
    """Prior probe: HYCOM null at Galveston Island / Bay points — dig coastal masking."""
    pts = {
        "galveston_island": [-94.7977, 29.3013],
        "galveston_bay": [-94.85, 29.45],
        "gulf_30km": [-94.9, 28.9],
        "gulf_open": [-93.0, 27.0],
        "miami": [-80.13, 25.7907],
    }
    img = (
        ee.ImageCollection("HYCOM/sea_temp_salinity")
        .filterDate("2023-06-01", "2023-06-15")
        .mean()
        .select(["water_temp_0", "salinity_0"])
        .multiply(0.001)
        .add(20)
    )
    out = {}
    for name, (lon, lat) in pts.items():
        pt = ee.Geometry.Point([lon, lat])
        out[name] = {
            "point": img.reduceRegion(ee.Reducer.first(), pt, 10000).getInfo(),
            "buffer_10km": reduce_mean(img, pt.buffer(10000), 10000).getInfo(),
            "buffer_30km": reduce_mean(img, pt.buffer(30000), 10000).getInfo(),
        }
    # Count of non-null salinity pixels in Galveston Bay
    sal = img.select("salinity_0")
    valid = sal.mask()
    out["galv_bay_valid_frac"] = reduce_mean(valid, GALV_BAY, 10000).getInfo()
    results["whoa"].append(
        "HYCOM goes null on Galveston Island/Bay landmask — use buffer into shelf or MODIS/OISST for bay SST."
    )
    return out


def exp_seawifs_historical():
    """SeaWiFS older era chl vs modern MODIS same season."""
    seawifs = (
        ee.ImageCollection("NASA/OCEANDATA/SeaWiFS/L3SMI")
        .filterDate("2000-08-01", "2000-08-31")
        .select("chlor_a")
        .mean()
    )
    modis = (
        ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI")
        .filterDate("2020-08-01", "2020-08-31")
        .select("chlor_a")
        .mean()
    )
    out = {
        "seawifs_2000_galv": reduce_mean(seawifs, GALV_BAY, 5000).getInfo(),
        "seawifs_2000_gulf": reduce_mean(seawifs, GULF_OPEN, 5000).getInfo(),
        "modis_2020_galv": reduce_mean(modis, GALV_BAY, 5000).getInfo(),
        "modis_2020_gulf": reduce_mean(modis, GULF_OPEN, 5000).getInfo(),
        "seawifs_span": [
            ee.ImageCollection("NASA/OCEANDATA/SeaWiFS/L3SMI")
            .sort("system:time_start")
            .first()
            .date()
            .format("YYYY-MM-dd")
            .getInfo(),
            ee.ImageCollection("NASA/OCEANDATA/SeaWiFS/L3SMI")
            .sort("system:time_start", False)
            .first()
            .date()
            .format("YYYY-MM-dd")
            .getInfo(),
        ],
    }
    make_thumb(
        seawifs.log10().clip(GULF),
        GULF,
        {"min": -1.5, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
        "gulf_seawifs_chl_aug2000",
    )
    return out


def exp_gfw_fishing_if_accessible():
    """Global Fishing Watch — often restricted; document."""
    cands = [
        "GFW/GFW_Fishing_Hours",
        "GFW/FISHING_HOURS",
        "projects/globalfishingwatch/public-data/fishing-hours",
        "GFW/VESSEL_HOURS",
    ]
    out = {}
    for aid in cands:
        try:
            col = ee.ImageCollection(aid)
            out[aid] = {"ok": True, "n": col.limit(2).size().getInfo(), "bands": col.first().bandNames().getInfo()}
        except Exception as e:
            out[aid] = {"ok": False, "error": str(e)[:200]}
    return out


def exp_ipcc_slr():
    cands = [
        "IPCC/AR6/SLR/medium_confidence",
        "IPCC/AR6/sea_level_projections/medium_confidence",
        "projects/sat-io/open-datasets/IPCC/AR6/SLR",
    ]
    out = {}
    for aid in cands:
        for loader in (ee.ImageCollection, ee.Image, ee.FeatureCollection):
            try:
                obj = loader(aid)
                if loader is ee.ImageCollection:
                    info = {"type": "IC", "n": obj.limit(3).size().getInfo(), "bands": obj.first().bandNames().getInfo()}
                elif loader is ee.Image:
                    info = {"type": "I", "bands": obj.bandNames().getInfo()}
                else:
                    info = {"type": "FC", "n": obj.limit(3).size().getInfo()}
                out[aid] = {"ok": True, **info}
                break
            except Exception as e:
                out[aid] = out.get(aid) or {"ok": False, "error": str(e)[:200]}
    return out


def main():
    ee.Initialize(project=PROJECT)
    init_regions()
    print("EE initialized", PROJECT)

    run_smoke()

    exp("01_oisst_gulf_mhw", exp_oisst_gulf_mhw)
    exp("02_oisst_vs_pathfinder", exp_oisst_vs_pathfinder)
    exp("03_ocean_color_multi_source", exp_ocean_color_multi_source)
    exp("04_olci_300m_dig", exp_olci_300m_dig)
    exp("05_hycom_profiles_velocity", exp_hycom_profiles_and_velocity)
    exp("06_murray_intertidal_change", exp_murray_intertidal_change)
    exp("07_mangroves_multi", exp_mangroves_multi)
    exp("08_allen_coral_seagrass", exp_allen_coral_seagrass)
    exp("09_bathymetry_stack", exp_bathymetry_stack)
    exp("10_waves_gulf_vs_hawaii", exp_waves_gulf_vs_hawaii)
    exp("11_estuary_turbidity_compare", exp_estuary_turbidity_compare)
    exp("12_hab_candidates", exp_hab_candidates)
    exp("13_arctic_ice", exp_arctic_ice)
    exp("14_hawaii_weird", exp_hawaii_weird)
    exp("15_mississippi_plume", exp_mississippi_plume)
    exp("16_grace_ocean_mass", exp_grace_ocean_mass)
    exp("17_copernicus_optics_transparency", exp_copernicus_optics_transparency)
    exp("18_hycom_galveston_null_mystery", exp_hycom_galveston_null_mystery)
    exp("19_seawifs_historical", exp_seawifs_historical)
    exp("20_gfw_fishing", exp_gfw_fishing_if_accessible)
    exp("21_ipcc_slr", exp_ipcc_slr)

    # summary counts
    smoke_ok = sum(1 for v in results["asset_smoke"].values() if v.get("ok"))
    smoke_n = len(results["asset_smoke"])
    exp_ok = sum(1 for v in results["experiments"].values() if v.get("ok"))
    exp_n = len(results["experiments"])
    thumb_ok = sum(1 for v in results["thumbs"].values() if v.get("ok"))
    results["summary"] = {
        "asset_smoke_ok": smoke_ok,
        "asset_smoke_n": smoke_n,
        "experiments_ok": exp_ok,
        "experiments_n": exp_n,
        "thumbs_ok": thumb_ok,
        "thumbs_n": len(results["thumbs"]),
        "whoa_n": len(results["whoa"]),
    }

    out_path = OUT / "deep_ocean_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n=== SUMMARY ===")
    print(json.dumps(results["summary"], indent=2))
    print("WHOA:")
    for w in results["whoa"]:
        print(" -", w)
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
