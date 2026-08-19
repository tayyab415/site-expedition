#!/usr/bin/env python3
"""House-scale vs parcel-scale change: can we see a reroof?

Labeled Austin building permits (City of Austin 3syk-w9eu) vs a neighbor
control, a vacant-land parcel, and the San Leon water site we already proved.

Question this answers: is Counter-Adjuster's load-bearing satellite job
"date a reroof from space", or "publish a dated public-imagery timeline"?
"""
from __future__ import annotations

import json
import math
import sys
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
RESULT = OUT / "roof_scale_results.json"

print("Initializing EE...", flush=True)
ee.Initialize(project=PROJECT)
print("EE ready", flush=True)

# Labeled reroofs from Austin issued building permits (final).
# Permit dates are the known physical event. NAIP epochs straddle them.
SITES = [
    {
        "id": "winfield_metal",
        "kind": "reroof",
        "note": "Express: Replace shingle roof with metal roof (2022-03-24)",
        "permit": "2022-040285 BP",
        "event": "2022-03-24",
        "address": "3611 Winfield Cove, Austin, TX 78704",
        "lat": 30.236041,
        "lng": -97.780482,
    },
    {
        "id": "farwest_metal",
        "kind": "reroof",
        "note": "Remove metal roof and replace / redeck (2023-06-30)",
        "permit": "2023-075499 BP",
        "event": "2023-06-30",
        "address": "4302 Far West Blvd, Austin, TX 78731",
        "lat": 30.361388,
        "lng": -97.770983,
    },
    {
        "id": "redleaf_redeck",
        "kind": "reroof",
        "note": "Roof replacement full re-deck (2022-03-16)",
        "permit": "2022-036450 BP",
        "event": "2022-03-16",
        "address": "2505 Redleaf Ln, Austin, TX 78745",
        "lat": 30.199728,
        "lng": -97.815739,
    },
    {
        "id": "ellise_reroof",
        "kind": "reroof",
        "note": "Express: Re-roof (2022-01-05)",
        "permit": "2022-001039 BP",
        "event": "2022-01-05",
        "address": "2609 Ellise Ave, Austin, TX 78757",
        "lat": 30.347837,
        "lng": -97.739871,
    },
    {
        "id": "winfield_control",
        "kind": "control",
        "note": "Neighbor of metal reroof; no matching 2022 roof permit",
        "permit": None,
        "event": None,
        "address": "3605 Winfield Cove, Austin, TX 78704",
        "lat": 30.236377,
        "lng": -97.780763,
    },
    {
        "id": "vacant_burnet",
        "kind": "vacant",
        "note": "Rural Burnet County undeveloped (Title Pirate scale)",
        "permit": None,
        "event": None,
        "address": None,
        "lat": 30.7600,
        "lng": -98.2300,
    },
    {
        "id": "san_leon_water",
        "kind": "water",
        "note": "San Leon — JRC water rewind already proven",
        "permit": None,
        "event": None,
        "address": None,
        "lat": 29.475732,
        "lng": -94.966533,
    },
]


def save_thumb(img, path: Path, region, dims=384):
    try:
        url = img.getThumbURL({"region": region, "dimensions": dims, "format": "png"})
        urllib.request.urlretrieve(url, path)
        return str(path)
    except Exception as e:
        print(f"  thumb fail {path.name}: {e}", flush=True)
        return None


def l2(a: dict, b: dict) -> float | None:
    keys = sorted(set(a) & set(b))
    if not keys:
        return None
    s = 0.0
    n = 0
    for k in keys:
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            continue
        s += (float(va) - float(vb)) ** 2
        n += 1
    return math.sqrt(s) if n else None


def rgb_delta(a: dict, b: dict) -> float | None:
    bands = []
    for k in ("R", "G", "B"):
        if a.get(k) is None or b.get(k) is None:
            return None
        bands.append((float(a[k]) - float(b[k])) ** 2)
    return math.sqrt(sum(bands) / 3.0) if bands else None


def naip_years(pt):
    col = ee.ImageCollection("USDA/NAIP/DOQQ").filterBounds(pt).select(["R", "G", "B"])
    # Distinct calendar years with a sample date.
    def per_img(im):
        d = ee.Date(im.get("system:time_start"))
        return ee.Feature(None, {"year": d.get("year"), "millis": d.millis()})

    feats = col.map(per_img)
    years = feats.aggregate_array("year").distinct().sort()
    return years.getInfo()


def naip_year_mosaic(pt, year: int):
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"
    col = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterBounds(pt)
        .filterDate(start, end)
        .select(["R", "G", "B"])
    )
    n = col.size()
    dates = col.aggregate_array("system:time_start")
    mosaic = col.mosaic()
    return mosaic, n, dates


def reduce_rgb(img, geom, scale):
    return img.select(["R", "G", "B"]).reduceRegion(
        ee.Reducer.mean(), geom, scale, maxPixels=1e8, bestEffort=True
    )


def embedding_year(pt, year: int, geom, scale):
    col = (
        ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
        .filterBounds(pt)
        .filter(ee.Filter.calendarRange(year, year, "year"))
    )
    im = col.first()
    stats = im.reduceRegion(ee.Reducer.mean(), geom, scale, maxPixels=1e8, bestEffort=True)
    return stats, col.size()


def s2_summer(pt, year: int, geom):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(pt)
        .filterDate(f"{year}-06-01", f"{year}-09-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .select(["B4", "B3", "B2", "B8"])
    )
    med = col.median()
    ndvi = med.normalizedDifference(["B8", "B4"]).rename("ndvi")
    stats = med.select(["B4", "B3", "B2"]).addBands(ndvi).reduceRegion(
        ee.Reducer.mean(), geom, 10, maxPixels=1e8, bestEffort=True
    )
    return stats, col.size()


def probe_site(site: dict) -> dict:
    print(f"\n=== {site['id']} ({site['kind']}) ===", flush=True)
    pt = ee.Geometry.Point([site["lng"], site["lat"]])
    roof = pt.buffer(12)  # ~house roof
    yard = pt.buffer(40)
    parcelish = pt.buffer(80)
    view = pt.buffer(60).bounds()
    vacant_view = pt.buffer(200).bounds()
    region = vacant_view if site["kind"] in ("vacant", "water") else view

    out = {
        "site": site,
        "ok": True,
        "naip": {},
        "embeddings": {},
        "s2": {},
        "thumbs": {},
        "error": None,
    }
    try:
        years = naip_years(pt)
        print(f"  NAIP years: {years}", flush=True)
        out["naip"]["years"] = years
        mosaics = {}
        for y in years or []:
            mosaic, n, dates = naip_year_mosaic(pt, int(y))
            n_i = n.getInfo()
            date_ms = dates.getInfo() or []
            date_iso = sorted(
                {
                    datetime.utcfromtimestamp(int(m) / 1000).date().isoformat()
                    for m in date_ms
                    if m
                }
            )
            roof_rgb = reduce_rgb(mosaic, roof, 1).getInfo()
            yard_rgb = reduce_rgb(mosaic, yard, 1).getInfo()
            mosaics[int(y)] = mosaic
            out["naip"][str(y)] = {
                "n_tiles": n_i,
                "capture_dates": date_iso,
                "roof_rgb": roof_rgb,
                "yard_rgb": yard_rgb,
            }
            print(f"    {y}: tiles={n_i} dates={date_iso} roof={roof_rgb}", flush=True)

        # consecutive NAIP deltas at roof vs yard
        ys = sorted(int(y) for y in (years or []))
        deltas = []
        for a, b in zip(ys, ys[1:]):
            ra = out["naip"][str(a)]["roof_rgb"]
            rb = out["naip"][str(b)]["roof_rgb"]
            ya = out["naip"][str(a)]["yard_rgb"]
            yb = out["naip"][str(b)]["yard_rgb"]
            deltas.append(
                {
                    "from": a,
                    "to": b,
                    "roof_rgb_l2": rgb_delta(ra, rb),
                    "yard_rgb_l2": rgb_delta(ya, yb),
                }
            )
        out["naip"]["deltas"] = deltas

        # thumbs: last two NAIP years (before/after around typical 2022 reroof)
        if len(ys) >= 2:
            y0, y1 = ys[-2], ys[-1]
            vis = {"bands": ["R", "G", "B"], "min": 0, "max": 180}
            out["thumbs"][f"naip_{y0}"] = save_thumb(
                mosaics[y0].visualize(**vis), THUMBS / f"{site['id']}_naip_{y0}.png", region
            )
            out["thumbs"][f"naip_{y1}"] = save_thumb(
                mosaics[y1].visualize(**vis), THUMBS / f"{site['id']}_naip_{y1}.png", region
            )

        # embeddings 2018 vs 2022 vs 2024 at roof / yard / 80m
        emb_years = [2018, 2022, 2024]
        for y in emb_years:
            try:
                stats_roof, n = embedding_year(pt, y, roof, 10)
                stats_yard, _ = embedding_year(pt, y, yard, 10)
                stats_big, _ = embedding_year(pt, y, parcelish, 10)
                n_i = n.getInfo()
                out["embeddings"][str(y)] = {
                    "n": n_i,
                    "roof": stats_roof.getInfo() if n_i else None,
                    "yard": stats_yard.getInfo() if n_i else None,
                    "buf80": stats_big.getInfo() if n_i else None,
                }
                print(f"  embed {y}: n={n_i}", flush=True)
            except Exception as e:
                out["embeddings"][str(y)] = {"error": str(e)}
                print(f"  embed {y} FAIL: {e}", flush=True)

        emb_d = {}
        for a, b in ((2018, 2022), (2022, 2024), (2018, 2024)):
            ea = out["embeddings"].get(str(a), {})
            eb = out["embeddings"].get(str(b), {})
            if not ea.get("roof") or not eb.get("roof"):
                continue
            emb_d[f"{a}_{b}"] = {
                "roof_l2": l2(ea["roof"], eb["roof"]),
                "yard_l2": l2(ea["yard"], eb["yard"]) if ea.get("yard") and eb.get("yard") else None,
                "buf80_l2": l2(ea["buf80"], eb["buf80"]) if ea.get("buf80") and eb.get("buf80") else None,
            }
        out["embeddings"]["deltas"] = emb_d

        # Sentinel-2 summer 2021 vs 2023 (straddles 2022 reroofs)
        for y in (2021, 2023):
            try:
                stats, n = s2_summer(pt, y, roof)
                out["s2"][str(y)] = {"n": n.getInfo(), "stats": stats.getInfo()}
                print(f"  S2 {y}: n={out['s2'][str(y)]['n']}", flush=True)
            except Exception as e:
                out["s2"][str(y)] = {"error": str(e)}
        s21 = out["s2"].get("2021", {}).get("stats") or {}
        s23 = out["s2"].get("2023", {}).get("stats") or {}
        if s21 and s23:
            out["s2"]["delta_ndvi"] = None
            if s21.get("ndvi") is not None and s23.get("ndvi") is not None:
                out["s2"]["delta_ndvi"] = float(s23["ndvi"]) - float(s21["ndvi"])
            out["s2"]["delta_rgb_l2"] = rgb_delta(
                {"R": s21.get("B4"), "G": s21.get("B3"), "B": s21.get("B2")},
                {"R": s23.get("B4"), "G": s23.get("B3"), "B": s23.get("B2")},
            )

    except Exception as e:
        out["ok"] = False
        out["error"] = f"{e}\n{traceback.format_exc()[-400:]}"
        print(f"  FAIL: {e}", flush=True)
    return out


def main():
    results = []
    for site in SITES:
        results.append(probe_site(site))
        RESULT.write_text(
            json.dumps(
                {
                    "when": datetime.now(timezone.utc).isoformat(),
                    "n": len(results),
                    "results": results,
                },
                indent=2,
                default=str,
            )
        )

    # compact scoreboard
    print("\n======== SCOREBOARD ========", flush=True)
    for r in results:
        s = r["site"]
        deltas = r.get("naip", {}).get("deltas") or []
        # pick the NAIP pair that straddles the event if possible
        pick = deltas[-1] if deltas else None
        if s.get("event") and deltas:
            ev = int(s["event"][:4])
            straddles = [d for d in deltas if d["from"] < ev <= d["to"] or d["from"] <= ev < d["to"]]
            if straddles:
                pick = straddles[0]
        emb = (r.get("embeddings", {}).get("deltas") or {}).get("2018_2024") or {}
        print(
            f"{s['id']:18} kind={s['kind']:7} "
            f"naip_roof={None if not pick else round(pick['roof_rgb_l2'] or -1, 2):>7} "
            f"naip_yard={None if not pick else round(pick['yard_rgb_l2'] or -1, 2):>7} "
            f"emb_roof={None if emb.get('roof_l2') is None else round(emb['roof_l2'], 3):>7} "
            f"emb_yard={None if emb.get('yard_l2') is None else round(emb['yard_l2'], 3):>7} "
            f"s2_ndvi={r.get('s2', {}).get('delta_ndvi')}",
            flush=True,
        )
    print(f"saved {RESULT}", flush=True)


if __name__ == "__main__":
    main()
