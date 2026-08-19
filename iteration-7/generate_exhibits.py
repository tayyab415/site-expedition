#!/usr/bin/env python3
"""Build citable Earth Engine stills + layer recipes for iteration-7.

Google photorealistic tiles are fetched live (context only). These USDA/JRC/FABDEM
exhibits are the witnesses that may appear in the packet.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import ee

PROJECT = "gen-lang-client-0261050164"
ROOT = Path(__file__).resolve().parent
EXHIBITS = ROOT / "exhibits"
EXHIBITS.mkdir(parents=True, exist_ok=True)

SITES = {
    "san_leon": {"lat": 29.475732, "lng": -94.966533, "name": "San Leon, TX"},
    "keep_control": {"lat": 30.2363775, "lng": -97.7807633, "name": "3605 Winfield Cove, Austin"},
}

BUFFER_M = 450
THUMB = 640


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r:
        dest.write_bytes(r.read())
    print(f"  wrote {dest.name} ({dest.stat().st_size} bytes)", flush=True)


def naip_years(pt: ee.Geometry) -> list[int]:
    col = ee.ImageCollection("USDA/NAIP/DOQQ").filterBounds(pt).select(["R", "G", "B"])
    years = col.aggregate_array("system:time_start").getInfo()
    out = sorted({int(ee.Date(t).get("year").getInfo()) if False else None for t in []})
    # faster: distinct year from metadata
    ys = col.aggregate_array("year").getInfo()
    if ys:
        return sorted({int(y) for y in ys if y is not None})
    starts = col.aggregate_array("system:time_start").getInfo()
    return sorted({int(ee.Date(t).format("YYYY").getInfo()) for t in starts[:80]})


def main() -> None:
    print("EE init", flush=True)
    ee.Initialize(project=PROJECT)
    report: dict = {"project": PROJECT, "sites": {}}

    for slug, site in SITES.items():
        print(f"\n== {slug} ==", flush=True)
        pt = ee.Geometry.Point([site["lng"], site["lat"]])
        region = pt.buffer(BUFFER_M).bounds()
        row: dict = {"name": site["name"], "lat": site["lat"], "lng": site["lng"], "files": {}, "stats": {}}

        naip = (
            ee.ImageCollection("USDA/NAIP/DOQQ")
            .filterBounds(pt)
            .select(["R", "G", "B"])
        )
        years = sorted({int(y) for y in (naip.aggregate_array("year").getInfo() or []) if y is not None})
        if not years:
            # some NAIP assets store year only on system:time_start
            starts = naip.aggregate_array("system:time_start").getInfo() or []
            years = sorted({int(ee.Date(t).get("year").getInfo()) for t in starts[:120]})
        row["stats"]["naip_years"] = years
        print(f"  NAIP years: {years}", flush=True)

        pick = []
        if years:
            pick.append(years[0])
            if years[-1] != years[0]:
                pick.append(years[-1])
        for y in pick:
            img = (
                naip.filter(ee.Filter.calendarRange(y, y, "year"))
                .mosaic()
                .visualize(min=0, max=255)
            )
            url = img.getThumbURL({"region": region, "dimensions": THUMB, "format": "png"})
            dest = EXHIBITS / f"{slug}_naip_{y}.png"
            download(url, dest)
            row["files"][f"naip_{y}"] = dest.name

        occ = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0)
        occ_vis = occ.visualize(min=0, max=60, palette=["0b0b0b", "1b4f72", "5dade2", "f4d03f", "e74c3c"])
        dest = EXHIBITS / f"{slug}_jrc_occurrence.png"
        download(occ_vis.getThumbURL({"region": region, "dimensions": THUMB, "format": "png"}), dest)
        row["files"]["jrc_occurrence"] = dest.name
        occ_mean = occ.reduceRegion(ee.Reducer.mean(), pt.buffer(60), 30).getInfo()
        row["stats"]["jrc_occurrence_mean"] = occ_mean.get("occurrence")

        fab = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("fabdem")
        nasa = ee.Image("NASA/NASADEM_HGT/001").select("elevation").rename("nasadem")
        elev = fab.addBands(nasa)
        stats = elev.reduceRegion(ee.Reducer.mean(), pt.buffer(60), 30).getInfo()
        row["stats"]["fabdem_m"] = stats.get("fabdem")
        row["stats"]["nasadem_m"] = stats.get("nasadem")

        # Coastal stretch vs inland stretch so the palette actually shows relief.
        vmin, vmax = (0, 8) if slug == "san_leon" else (180, 230)
        fab_vis = fab.visualize(min=vmin, max=vmax, palette=["08306b", "2171b5", "6baed6", "c6dbef", "ffffcc", "fd8d3c", "b10026"])
        dest = EXHIBITS / f"{slug}_fabdem.png"
        download(fab_vis.getThumbURL({"region": region, "dimensions": THUMB, "format": "png"}), dest)
        row["files"]["fabdem"] = dest.name

        # Google Satellite Embedding change 2017→2024 (1 - cosine). Public EE catalog.
        col = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
        a = col.filterDate("2017-01-01", "2018-01-01").filterBounds(pt).first()
        b = col.filterDate("2024-01-01", "2025-01-01").filterBounds(pt).first()
        if a is not None and b is not None:
            bands = a.bandNames()
            dot = a.multiply(b).reduce(ee.Reducer.sum()).rename("cos")
            change = ee.Image(1).subtract(dot).rename("change")
            ch = change.reduceRegion(ee.Reducer.mean(), pt.buffer(60), 10).getInfo()
            row["stats"]["embed_change_2017_2024"] = ch.get("change")
            ch_vis = change.visualize(min=0, max=0.25, palette=["0b0b0b", "2ecc71", "f4d03f", "e74c3c"])
            dest = EXHIBITS / f"{slug}_embed_change.png"
            download(ch_vis.getThumbURL({"region": region, "dimensions": THUMB, "format": "png"}), dest)
            row["files"]["embed_change"] = dest.name
            row["stats"]["embed_bands"] = bands.size().getInfo()
        else:
            row["stats"]["embed_change_2017_2024"] = None

        report["sites"][slug] = row

    (EXHIBITS / "manifest.json").write_text(json.dumps(report, indent=2))
    print("\nmanifest written", flush=True)


if __name__ == "__main__":
    main()
