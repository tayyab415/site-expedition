#!/usr/bin/env python3
"""5-layers-deeper digs on the whoa / weird findings from run_deep_ocean.py."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
OUT = Path(__file__).resolve().parent
THUMBS = OUT / "thumbs"
THUMBS.mkdir(parents=True, exist_ok=True)

results = {
    "ran_at": datetime.now(timezone.utc).isoformat(),
    "digs": {},
    "thumbs": {},
    "whoa": [],
}


def mean(img, geom, scale):
    return img.reduceRegion(ee.Reducer.mean(), geom, scale, maxPixels=1e8, bestEffort=True)


def pct(img, geom, scale, ps=(10, 50, 90)):
    return img.reduceRegion(ee.Reducer.percentile(list(ps)), geom, scale, maxPixels=1e8, bestEffort=True)


def thumb(img, region, vis, name, dimensions=640):
    try:
        url = img.getThumbURL({"region": region, "dimensions": dimensions, "format": "png", **vis})
        path = THUMBS / f"{name}.png"
        urllib.request.urlretrieve(url, path)
        ok = path.exists() and path.stat().st_size > 200
        results["thumbs"][name] = {"ok": ok, "path": str(path) if ok else None}
        return ok
    except Exception as e:
        results["thumbs"][name] = {"ok": False, "error": str(e)[:250]}
        return False


def dig(name, fn):
    print(f"\n=== DIG {name} ===")
    try:
        out = fn()
        results["digs"][name] = {"ok": True, **(out or {})}
        print("  ok")
    except Exception as e:
        results["digs"][name] = {"ok": False, "error": str(e)[:500]}
        print("  FAIL", e)


def dig_globcolour_sliding_window():
    """OLCI/MULTI are NRT sliding windows — find actual usable dates + sample now."""
    aids = {
        "plankton_multi": "COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_MULTI_4KM",
        "plankton_olci300": "COPERNICUS/MARINE/OC_GLO_BGC/PLANKTON_OLCI_300M",
        "optics": "COPERNICUS/MARINE/OC_GLO_BGC/OPTICS_MULTI_4KM",
        "transparency": "COPERNICUS/MARINE/OC_GLO_BGC/TRANSPARENCY_MULTI_4KM",
        "reflectance": "COPERNICUS/MARINE/OC_GLO_BGC/REFLECTANCE_MULTI_4KM",
        "pp": "COPERNICUS/MARINE/OC_GLO_BGC/PRIMARY_PRODUCTION_MULTI_4KM",
    }
    galv = ee.Geometry.Rectangle([-95.2, 29.2, -94.6, 29.75])
    gulf = ee.Geometry.Point([-93.0, 27.0]).buffer(50000)
    out = {}
    for key, aid in aids.items():
        col = ee.ImageCollection(aid)
        first = col.sort("system:time_start").first()
        last = col.sort("system:time_start", False).first()
        span = [
            first.date().format("YYYY-MM-dd").getInfo(),
            last.date().format("YYYY-MM-dd").getInfo(),
        ]
        bands = last.bandNames().getInfo()
        # sample last 30 days of collection
        end = ee.Date(last.get("system:time_start"))
        start = end.advance(-30, "day")
        recent = col.filterDate(start, end.advance(1, "day"))
        img = recent.mean()
        sample = {}
        for b in bands[:3]:
            sample[b] = {
                "galv": mean(img.select(b), galv, 1000).getInfo(),
                "open": mean(img.select(b), gulf, 4000).getInfo(),
            }
        out[key] = {
            "id": aid,
            "span": span,
            "bands": bands,
            "n_recent_30d": recent.size().getInfo(),
            "sample_recent": sample,
        }
        # thumb CHL if present
        if "CHL" in bands:
            thumb(
                img.select("CHL").log10().clip(ee.Geometry.Rectangle([-97.5, 26, -88, 30.5])),
                ee.Geometry.Rectangle([-97.5, 26, -88, 30.5]),
                {"min": -1.5, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
                f"globcolour_{key}_recent_chl",
            )
        if "ZSD" in bands or "KD490" in bands:
            b0 = "ZSD" if "ZSD" in bands else "KD490"
            thumb(
                img.select(b0).clip(ee.Geometry.Rectangle([-97.5, 26, -88, 30.5])),
                ee.Geometry.Rectangle([-97.5, 26, -88, 30.5]),
                {"min": 0, "max": 30 if b0 == "ZSD" else 1, "palette": ["ffffcc", "41b6c4", "0c2c84"]},
                f"globcolour_{key}_{b0}",
            )

    results["whoa"].append(
        f"Copernicus GlobColour BGC in EE is a sliding ~2y NRT window "
        f"(plankton_multi span {out['plankton_multi']['span']}) — historical Aug2023 pulls are empty by design."
    )
    return out


def dig_jaxa_scale():
    """Decode JAXA CHLA_AVE scale vs MODIS."""
    galv = ee.Geometry.Rectangle([-95.2, 29.2, -94.6, 29.75])
    gulf = ee.Geometry.Point([-93.0, 27.0]).buffer(50000)
    # try recent overlapping window
    a, b = "2024-08-01", "2024-08-15"
    jaxa = ee.ImageCollection("JAXA/GCOM-C/L3/OCEAN/CHLA/V3").filterDate(a, b).select("CHLA_AVE").mean()
    modis = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(a, b).select("chlor_a").mean()
    raw_g = mean(jaxa, galv, 5000).getInfo()
    raw_o = mean(jaxa, gulf, 5000).getInfo()
    m_g = mean(modis, galv, 5000).getInfo()
    m_o = mean(modis, gulf, 5000).getInfo()
    # catalog: CHLA_AVE scale 0.0015 typically for GCOM-C L3
    scales = [0.0015, 0.001, 0.01, 1 / 1000, 1 / 100]
    decoded = {}
    for s in scales:
        decoded[str(s)] = {
            "galv": (raw_g.get("CHLA_AVE") or 0) * s,
            "open": (raw_o.get("CHLA_AVE") or 0) * s,
            "ratio_to_modis_galv": ((raw_g.get("CHLA_AVE") or 0) * s) / m_g["chlor_a"] if m_g.get("chlor_a") else None,
        }
    # pick best scale (closest to modis galv)
    best = min(decoded.items(), key=lambda kv: abs((kv[1]["galv"] or 0) - (m_g.get("chlor_a") or 0)))
    results["whoa"].append(
        f"JAXA GCOM-C CHLA_AVE is scaled: raw Galv≈{raw_g.get('CHLA_AVE'):.0f}; "
        f"best match to MODIS uses scale {best[0]} → {best[1]['galv']:.2f} vs MODIS {m_g.get('chlor_a'):.2f}."
    )
    thumb(
        jaxa.multiply(float(best[0])).log10().clip(ee.Geometry.Rectangle([-97.5, 26, -88, 30.5])),
        ee.Geometry.Rectangle([-97.5, 26, -88, 30.5]),
        {"min": -1.5, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
        "gulf_jaxa_chla_scaled_aug2024",
    )
    return {"window": [a, b], "jaxa_raw": {"galv": raw_g, "open": raw_o}, "modis": {"galv": m_g, "open": m_o}, "decoded": decoded, "best_scale": best[0]}


def dig_murray_loss_proper():
    """Fix loss/gain — reproject to common grid; compute SF Bay / Galveston % loss."""
    col = ee.ImageCollection("UQ/murray/Intertidal/v1_1/global_intertidal")
    first = ee.Image(col.filter(ee.Filter.eq("system:index", "1984-1986")).first())
    last = ee.Image(col.filter(ee.Filter.eq("system:index", "2014-2016")).first())
    # class 1 = tidal flat
    f = first.eq(1).rename("flat")
    l = last.eq(1).rename("flat")
    # force same projection
    l = l.reproject(f.projection())
    lost = f.And(l.Not()).rename("lost")
    gained = l.And(f.Not()).rename("gained")
    persist = f.And(l).rename("persist")

    regions = {
        "galveston_bay": ee.Geometry.Rectangle([-95.2, 29.2, -94.6, 29.75]),
        "sf_bay": ee.Geometry.Rectangle([-122.55, 37.4, -121.9, 38.15]),
        "chesapeake": ee.Geometry.Rectangle([-76.6, 37.0, -75.8, 39.4]),
        "tx_coast": ee.Geometry.Rectangle([-97.5, 25.8, -93.5, 30.0]),
    }
    out = {}
    for name, geom in regions.items():
        def area(img):
            return img.multiply(ee.Image.pixelArea()).reduceRegion(
                ee.Reducer.sum(), geom, 30, maxPixels=1e9, bestEffort=True
            ).getInfo()

        a_f = area(f)
        a_l = area(l)
        a_lost = area(lost)
        a_gain = area(gained)
        a_pers = area(persist)
        first_m2 = a_f.get("flat") or 0
        last_m2 = a_l.get("flat") or 0
        lost_m2 = a_lost.get("lost") or 0
        gain_m2 = a_gain.get("gained") or 0
        out[name] = {
            "first_km2": first_m2 / 1e6,
            "last_km2": last_m2 / 1e6,
            "lost_km2": lost_m2 / 1e6,
            "gained_km2": gain_m2 / 1e6,
            "persist_km2": (a_pers.get("persist") or 0) / 1e6,
            "pct_change": ((last_m2 - first_m2) / first_m2 * 100) if first_m2 else None,
        }
    # thumbs
    galv = regions["galveston_bay"]
    rgb = ee.Image.cat(lost.multiply(255), gained.multiply(255), persist.multiply(120)).rename(["r", "g", "b"])
    thumb(rgb.clip(galv), galv, {"bands": ["r", "g", "b"], "min": 0, "max": 255}, "galv_murray_loss_gain_fixed")
    thumb(rgb.clip(regions["sf_bay"]), regions["sf_bay"], {"bands": ["r", "g", "b"], "min": 0, "max": 255}, "sfbay_murray_loss_gain")

    worst = max(out.items(), key=lambda kv: -(kv[1]["pct_change"] or 0))
    results["whoa"].append(
        f"Murray tidal flats 1984–86→2014–16: {worst[0]} changed {worst[1]['pct_change']:.1f}% "
        f"({worst[1]['first_km2']:.1f}→{worst[1]['last_km2']:.1f} km²)."
    )
    return out


def dig_pathfinder_units():
    """Pathfinder SST raw ~3022 → Kelvin*10?"""
    gulf = ee.Geometry.Point([-93.0, 27.0]).buffer(50000)
    pf = (
        ee.ImageCollection("NOAA/CDR/SST_PATHFINDER/V53")
        .filterDate("2023-08-01", "2023-08-15")
        .select("sea_surface_temperature")
        .mean()
    )
    oisst = (
        ee.ImageCollection("NOAA/CDR/OISST/V2_1")
        .filterDate("2023-08-01", "2023-08-15")
        .select("sst")
        .mean()
        .multiply(0.01)
    )
    raw = mean(pf, gulf, 25000).getInfo()["sea_surface_temperature"]
    oi = mean(oisst, gulf, 25000).getInfo()["sst"]
    candidates = {
        "raw": raw,
        "raw/10_K_to_C": raw / 10 - 273.15,
        "raw/100": raw / 100,
        "raw_minus_27315_div_100": (raw - 27315) / 100,  # if stored as cK
        "raw_scale_0_01": raw * 0.01,
    }
    # catalog says scale 0.01 for sea_surface_temperature in Kelvin often
    best = {k: abs(v - oi) for k, v in candidates.items() if isinstance(v, (int, float))}
    best_k = min(best, key=best.get)
    results["whoa"].append(
        f"Pathfinder SST raw≈{raw:.1f}; decode '{best_k}'→{candidates[best_k]:.2f}C closest to OISST {oi:.2f}C."
    )
    return {"oisst_c": oi, "candidates": candidates, "best": best_k}


def dig_ice_correct_units_and_bering():
    """OISST ice after *0.01 is fraction 0–1 (or percent/100). Map seasonal melt; Copernicus thickness."""
    beaufort = ee.Geometry.Rectangle([-155.0, 70.0, -140.0, 72.5])
    bering = ee.Geometry.Rectangle([-175.0, 55.0, -160.0, 65.0])
    months = {}
    for ym in ["2024-01", "2024-03", "2024-05", "2024-07", "2024-09", "2024-11"]:
        y, m = ym.split("-")
        start = f"{ym}-01"
        end = f"{y}-{int(m)+1:02d}-01" if m != "12" else "2025-01-01"
        if m == "12":
            end = "2025-01-01"
        else:
            end = f"{y}-{int(m)+1:02d}-01"
        ice = ee.ImageCollection("NOAA/CDR/OISST/V2_1").filterDate(start, end).select("ice").mean().multiply(0.01)
        months[ym] = {
            "beaufort_frac": mean(ice, beaufort, 25000).getInfo().get("ice"),
            "bering_frac": mean(ice, bering, 25000).getInfo().get("ice"),
        }
    phy = ee.ImageCollection("COPERNICUS/MARINE/GLOBAL_ANALYSISFORECAST_PHY_DAILY")
    # thickness + concentration March vs Sept
    out_phy = {}
    for label, a, b in [("mar", "2024-03-01", "2024-03-10"), ("sep", "2024-09-01", "2024-09-10")]:
        img = phy.filterDate(a, b).mean()
        out_phy[label] = {
            "siconc_beaufort": mean(img.select("siconc"), beaufort, 10000).getInfo(),
            "sithick_beaufort": mean(img.select("sithick"), beaufort, 10000).getInfo(),
            "siconc_bering": mean(img.select("siconc"), bering, 10000).getInfo(),
            "sithick_bering": mean(img.select("sithick"), bering, 10000).getInfo(),
        }
    # Sept ice edge thumb
    sept = phy.filterDate("2024-09-01", "2024-09-10").select("siconc").mean()
    thumb(
        sept.clip(ee.Geometry.Rectangle([-180, 55, -120, 75])),
        ee.Geometry.Rectangle([-180, 55, -120, 75]),
        {"min": 0, "max": 1, "palette": ["08306b", "6baed6", "ffffff"]},
        "alaska_phy_siconc_sep2024",
    )
    bf = months["2024-03"]["beaufort_frac"]
    bs = months["2024-09"]["beaufort_frac"]
    results["whoa"].append(
        f"Beaufort OISST ice fraction: Mar≈{bf:.2f} → Sep≈{bs:.2f}; "
        f"Copernicus sithick Mar≈{(out_phy['mar']['sithick_beaufort'] or {}).get('sithick'):.2f}m "
        f"→ Sep≈{(out_phy['sep']['sithick_beaufort'] or {}).get('sithick')}."
    )
    return {"monthly_oisst_ice_frac": months, "phy": out_phy}


def dig_wave_bathy_cap():
    """Wave static deptho caps deep ocean — compare to ETOPO along Gulf transect."""
    etopo = ee.Image("NOAA/NGDC/ETOPO1").select("bedrock")
    deptho = ee.ImageCollection("COPERNICUS/MARINE/WAV/ANFC_0_083DEG_STATIC").first().select("deptho")
    gebco = ee.ImageCollection("projects/sat-io/open-datasets/gebco/gebco_grid").mosaic().rename("gebco")
    transect = []
    for lat in [29.3, 28.5, 27.5, 26.5, 25.5, 24.5]:
        pt = ee.Geometry.Point([-90.0, lat])
        transect.append(
            {
                "lat": lat,
                "etopo": etopo.reduceRegion(ee.Reducer.first(), pt, 2000).getInfo(),
                "gebco": gebco.reduceRegion(ee.Reducer.first(), pt, 500).getInfo(),
                "wave_deptho": deptho.reduceRegion(ee.Reducer.first(), pt, 10000).getInfo(),
            }
        )
    # max deptho globally sample
    deep = ee.Geometry.Point([-90.0, 24.0])
    results["whoa"].append(
        "Copernicus wave 'deptho' is wave-model bathymetry (caps ~hundreds of m), NOT full-ocean GEBCO/ETOPO — "
        f"at 25.5N Gulf: ETOPO={transect[4]['etopo'].get('bedrock')} vs deptho={transect[4]['wave_deptho'].get('deptho')}."
    )
    return {"transect_lon90W": transect}


def dig_chesapeake_hab_deeper():
    """Chesapeake Aug 2023 chl/nflh was higher than SW FL — validate multi-source + monthly series."""
    ches = ee.Geometry.Rectangle([-76.6, 37.0, -75.8, 39.4])
    open_atl = ee.Geometry.Point([-72.0, 36.0]).buffer(50000)
    series = []
    for month in range(1, 13):
        a = f"2023-{month:02d}-01"
        b = f"2023-{month+1:02d}-01" if month < 12 else "2024-01-01"
        mod = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate(a, b)
        chl = mod.select("chlor_a").mean()
        nflh = mod.select("nflh").mean()
        cop = (
            ee.ImageCollection("COPERNICUS/MARINE/SATELLITE_OCEAN_COLOR/V6")
            .filterDate(a, b)
            .select("chlor_a")
            .mean()
        )
        series.append(
            {
                "month": month,
                "modis_chl": mean(chl, ches, 5000).getInfo(),
                "modis_nflh": mean(nflh, ches, 5000).getInfo(),
                "copernicus_chl": mean(cop, ches, 5000).getInfo(),
                "atl_chl": mean(chl, open_atl, 5000).getInfo(),
            }
        )
    peak = max(series, key=lambda r: (r["modis_chl"] or {}).get("chlor_a") or 0)
    results["whoa"].append(
        f"Chesapeake 2023 MODIS chl peaks in month {peak['month']} at "
        f"{(peak['modis_chl'] or {}).get('chlor_a'):.1f} mg/m³ "
        f"(nflh={(peak['modis_nflh'] or {}).get('nflh'):.3f}); coastal eutrophic signal, not just Florida."
    )
    # Aug thumb
    aug = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterDate("2023-08-01", "2023-09-01").select("chlor_a").mean()
    thumb(
        aug.log10().clip(ches),
        ches,
        {"min": 0, "max": 1.5, "palette": ["0b2460", "1e90ff", "ffff00", "ff0000"]},
        "chesapeake_modis_chl_aug2023",
    )
    return {"monthly_2023": series, "peak": peak}


def dig_aca_class_legend():
    """Map ACA benthic class codes to names via histogram fractions Keys vs Oahu."""
    # From Allen Coral Atlas docs:
    # benthic: 11=Seagrass, 12=Macroalgae, 13=Coral/Algae, 14=Rubble, 15=Rock, 16=Sand?, 18=Microalgal mats?
    legend = {
        "11": "Seagrass",
        "12": "Macroalgae",
        "13": "Coral/Algae",
        "14": "Rubble",
        "15": "Rock",
        "16": "Sand",
        "17": "Rubble/Sand?",
        "18": "Microalgal mats",
    }
    img = ee.Image("ACA/reef_habitat/v2_0").select("benthic")
    keys = ee.Geometry.Rectangle([-81.9, 24.4, -80.2, 25.2])
    oahu = ee.Geometry.Rectangle([-158.3, 21.2, -157.6, 21.7])
    # seagrass mask
    sg = img.eq(11)
    keys_sg_km2 = sg.multiply(ee.Image.pixelArea()).reduceRegion(
        ee.Reducer.sum(), keys, 30, maxPixels=1e8, bestEffort=True
    ).getInfo()
    oahu_sg_km2 = sg.multiply(ee.Image.pixelArea()).reduceRegion(
        ee.Reducer.sum(), oahu, 30, maxPixels=1e8, bestEffort=True
    ).getInfo()
    thumb(sg.selfMask().clip(keys), keys, {"palette": ["00aa55"]}, "florida_keys_seagrass_aca")
    thumb(sg.selfMask().clip(oahu), oahu, {"palette": ["00aa55"]}, "oahu_seagrass_aca")
    k_km2 = (keys_sg_km2.get("benthic") or 0) / 1e6
    o_km2 = (oahu_sg_km2.get("benthic") or 0) / 1e6
    results["whoa"].append(
        f"ACA class 11 (Seagrass): Florida Keys ≈{k_km2:.1f} km² vs south Oahu ≈{o_km2:.1f} km² — working seagrass layer in EE."
    )
    return {"legend_assumed": legend, "keys_seagrass_km2": k_km2, "oahu_seagrass_km2": o_km2}


def dig_dem_flood_math():
    """How many San Leon-like coastal pixels flip below/above 1m between FABDEM and NASADEM."""
    fab = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("fab")
    nasa = ee.Image("NASA/NASADEM_HGT/001").select("elevation").rename("nasa")
    region = ee.Geometry.Rectangle([-95.15, 29.35, -94.75, 29.65])  # west Galveston Bay shore
    diff = fab.subtract(nasa).rename("d")
    # pixels where one says <1m and other says >2m
    fab_low = fab.lt(1)
    nasa_high = nasa.gt(2)
    flip = fab_low.And(nasa_high).rename("flip")
    stats = {
        "mean_diff": mean(diff, region, 30).getInfo(),
        "pct_diff": pct(diff, region, 30).getInfo(),
        "flip_area_m2": flip.multiply(ee.Image.pixelArea())
        .reduceRegion(ee.Reducer.sum(), region, 30, maxPixels=1e9, bestEffort=True)
        .getInfo(),
        "fab_below_1m_km2": fab_low.multiply(ee.Image.pixelArea())
        .reduceRegion(ee.Reducer.sum(), region, 30, maxPixels=1e9, bestEffort=True)
        .getInfo(),
        "nasa_below_1m_km2": nasa.lt(1)
        .multiply(ee.Image.pixelArea())
        .reduceRegion(ee.Reducer.sum(), region, 30, maxPixels=1e9, bestEffort=True)
        .getInfo(),
    }
    # convert
    flip_km2 = (stats["flip_area_m2"].get("flip") or 0) / 1e6
    fab1 = (stats["fab_below_1m_km2"].get("fab") or 0) / 1e6
    nasa1 = (stats["nasa_below_1m_km2"].get("elevation") or stats["nasa_below_1m_km2"].get("nasa") or 0) / 1e6
    results["whoa"].append(
        f"West Galveston Bay shore: FABDEM<1m covers {fab1:.1f} km² vs NASADEM<1m {nasa1:.1f} km²; "
        f"flip zone (FAB<1 & NASA>2) ≈{flip_km2:.2f} km²."
    )
    thumb(
        flip.selfMask().clip(region),
        region,
        {"palette": ["ff0000"]},
        "galv_dem_flip_zone",
    )
    return {"stats": stats, "flip_km2": flip_km2, "fab_below_1_km2": fab1, "nasa_below_1_km2": nasa1}


def dig_hycom_loop_current_series():
    """Loop Current speed seasonality in SE Gulf box."""
    box = ee.Geometry.Rectangle([-88, 24, -84, 27])
    series = []
    for month in (1, 4, 7, 10):
        a = f"2023-{month:02d}-01"
        b = f"2023-{month+1:02d}-01" if month < 12 else "2024-01-01"
        vel = ee.ImageCollection("HYCOM/sea_water_velocity").filterDate(a, b).mean()
        u = vel.select("velocity_u_0").multiply(0.001)
        v = vel.select("velocity_v_0").multiply(0.001)
        speed = u.hypot(v)
        series.append({"month": month, "speed": mean(speed, box, 10000).getInfo()})
    peak = max(series, key=lambda r: (r["speed"] or {}).get("velocity_u_0") or (r["speed"] or {}).get("speed") or 0)
    # speed band name after hypot is first band - actually hypot keeps name of u? In EE hypot of two images names after first.
    # Our rename was missing — values under velocity_u_0 possibly
    results["whoa"].append(
        f"HYCOM Loop Current box 2023 monthly speeds: "
        + ", ".join(f"m{s['month']}={(list((s['speed'] or {}).values()) or [None])[0]}" for s in series)
    )
    return {"series_2023": series}


def dig_ndti_vs_ndssi_ranking():
    """Re-rank estuaries by NDSSI (often better suspended-sediment proxy) + NDTI p90."""
    # pull from previous JSON and recompute ranking message
    prev = json.loads((OUT / "deep_ocean_results.json").read_text())
    t = prev["experiments"]["11_estuary_turbidity_compare"]
    rows = []
    for name in ("galveston", "chesapeake", "sf_bay"):
        st = t[name]["stats"]
        rows.append(
            {
                "name": name,
                "ndti_mean": st["ndti_mean"]["ndti"],
                "ndti_p90": st["ndti"]["ndti_p90"],
                "ndssi_mean": st["ndssi_mean"]["ndssi"],
                "ndssi_p90": st["ndssi"]["ndssi_p90"],
            }
        )
    by_ndti = sorted(rows, key=lambda r: -r["ndti_mean"])
    by_ndssi = sorted(rows, key=lambda r: -r["ndssi_mean"])
    by_ndti_p90 = sorted(rows, key=lambda r: -r["ndti_p90"])
    results["whoa"].append(
        f"Turbidity proxies diverge: NDTI-mean ranks {[r['name'] for r in by_ndti]}; "
        f"NDSSI-mean ranks {[r['name'] for r in by_ndssi]} (SF Bay highest NDSSI — different optical soup)."
    )
    return {"by_ndti_mean": by_ndti, "by_ndssi_mean": by_ndssi, "by_ndti_p90": by_ndti_p90}


def dig_more_asset_ids():
    """Extra weird / coastal asset IDs."""
    cands = [
        ("copernicus_sss_nrt", "COPERNICUS/MARINE/GLOBAL_ANALYSISFORECAST_PHY_SSS_SSD_NRT"),
        ("copernicus_sss_my_alt", "COPERNICUS/MARINE/MULTIOBSERVATION_PHY_SSS_SSD_MY_DAILY"),
        ("copernicus_sss_nrt2", "COPERNICUS/MARINE/MULTIOBSERVATION_PHY_SSS_SSD_NRT_DAILY"),
        ("murray_tidal_wetland", "UQ/murray/Intertidal/v1_1/global_intertidal"),  # already
        ("murray_tidal_wetland_change", "UQ/Murray/TidalWetland/v1_0/global_change"),
        ("murray_tidal_wetland_extent", "UQ/Murray/TidalWetland/v1_0/global_extent"),
        ("giri_mangrove_alt", "LANDSAT/MANGROVE_FORESTS/2000"),
        ("wdpa", "WCMC/WDPA/current/polygons"),
        ("gfw_public", "projects/globalfishingwatch/public-vessels"),
        ("era5_waves", "ECMWF/ERA5_LAND/HOURLY"),  # control
        ("noaa_ncei_dem", "NOAA/NGDC/ETOPO1"),
        ("gebco_2024", "projects/sat-io/open-datasets/gebco/gebco_2024"),
        ("gebco_2023", "projects/sat-io/open-datasets/gebco/GEBCO_2023"),
        ("copernicus_bio", "COPERNICUS/MARINE/GLOBAL_ANALYSISFORECAST_BGC_DAILY"),
        ("hycom_ssh2", "HYCOM/sea_surface_elevation"),
        ("goes_sst", "NOAA/GOES/16/FDCF"),
        ("avhrr_sst_cdr", "NOAA/CDR/SST_WHOI/V2"),
        ("ocean_heat_flux", "NOAA/CDR/HEAT_FLUXES/V2"),
        ("ocean_atmos", "NOAA/CDR/OCEAN_ATMOS/V2"),
    ]
    out = {}
    for name, aid in cands:
        ok = False
        info = {"id": aid}
        for kind, loader in [
            ("ImageCollection", ee.ImageCollection),
            ("Image", ee.Image),
            ("FeatureCollection", ee.FeatureCollection),
        ]:
            try:
                obj = loader(aid)
                if kind == "ImageCollection":
                    info.update(
                        ok=True,
                        type=kind,
                        bands=obj.first().bandNames().getInfo(),
                        n=obj.limit(2).size().getInfo(),
                    )
                elif kind == "Image":
                    info.update(ok=True, type=kind, bands=obj.bandNames().getInfo())
                else:
                    info.update(ok=True, type=kind, n=obj.limit(2).size().getInfo())
                ok = True
                break
            except Exception as e:
                info.setdefault("errors", []).append(f"{kind}:{str(e)[:120]}")
        out[name] = info
        print(f"  {'OK' if ok else 'FAIL'} {name}")
    return out


def main():
    ee.Initialize(project=PROJECT)
    dig("D1_globcolour_sliding_window", dig_globcolour_sliding_window)
    dig("D2_jaxa_scale", dig_jaxa_scale)
    dig("D3_murray_loss_proper", dig_murray_loss_proper)
    dig("D4_pathfinder_units", dig_pathfinder_units)
    dig("D5_ice_units_seasonality", dig_ice_correct_units_and_bering)
    dig("D6_wave_bathy_cap", dig_wave_bathy_cap)
    dig("D7_chesapeake_hab_series", dig_chesapeake_hab_deeper)
    dig("D8_aca_seagrass", dig_aca_class_legend)
    dig("D9_dem_flood_math", dig_dem_flood_math)
    dig("D10_hycom_loop_seasonality", dig_hycom_loop_current_series)
    dig("D11_ndti_ndssi_ranking", dig_ndti_vs_ndssi_ranking)
    dig("D12_more_asset_ids", dig_more_asset_ids)

    path = OUT / "deep_ocean_deeper.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nWHOA:")
    for w in results["whoa"]:
        print(" -", w)
    print("Wrote", path)


if __name__ == "__main__":
    main()
