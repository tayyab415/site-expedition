"""Earth Engine eye — independent witnesses: time (JRC water rewind) and
height (FABDEM / NASADEM vs the cited record).

Cache-first: EE runs take minutes; results land in cache/earth/<slug>.json.
"""
import json
from pathlib import Path

CACHE = Path(__file__).parent.parent / "cache" / "earth"

EE_PROJECT = "gen-lang-client-0261050164"
DATASETS = {
    "water": "JRC/GSW1_4/MonthlyHistory",
    "nasadem": "NASA/NASADEM_HGT/001",
    "fabdem": "projects/sat-io/open-datasets/FABDEM",
}


def witness(slug: str, lat: float, lng: float, live: bool = False) -> dict:
    cached = CACHE / f"{slug}.json"
    if cached.exists() and not live:
        return json.loads(cached.read_text())

    import ee
    ee.Initialize(project=EE_PROJECT)
    pt = ee.Geometry.Point([lng, lat])
    region = pt.buffer(60)

    monthly = ee.ImageCollection(DATASETS["water"])

    def year_freq(y):
        y = ee.Number(y)
        yr = monthly.filter(ee.Filter.calendarRange(y, y, "year"))
        freq = yr.map(lambda im: im.eq(2).unmask(0)).mean()
        stats = freq.reduceRegion(ee.Reducer.mean(), region, 30, maxPixels=1e8)
        return ee.Feature(None, {"year": y, "water_freq": stats.get("water")})

    rows = ee.FeatureCollection(ee.List.sequence(1985, 2021).map(year_freq)).getInfo()
    timeline = [
        {
            "year": int(r["properties"]["year"]),
            "water_freq": round(r["properties"]["water_freq"] or 0.0, 4),
        }
        for r in rows["features"]
    ]

    base = [t["water_freq"] for t in timeline if t["year"] < 2000]
    baseline = sum(base) / len(base) if base else 0.0
    breakpoint_year = None
    for i, t in enumerate(timeline):
        if t["year"] < 2000 or i < 4:
            continue
        trailing = sum(x["water_freq"] for x in timeline[i - 4 : i + 1]) / 5
        if trailing > max(2 * baseline, baseline + 0.02):
            breakpoint_year = t["year"]
            break

    elev = (
        ee.Image(DATASETS["nasadem"])
        .select("elevation")
        .addBands(ee.ImageCollection(DATASETS["fabdem"]).mosaic().rename("fabdem"))
        .reduceRegion(ee.Reducer.mean(), region, 30)
        .getInfo()
    )

    result = {
        "water": {
            "dataset": DATASETS["water"],
            "baseline_freq_1985_1999": round(baseline, 4),
            "latest_freq_2021": timeline[-1]["water_freq"],
            "breakpoint_year": breakpoint_year,
            "timeline": timeline,
        },
        "height": {
            "nasadem_m": elev.get("elevation"),
            "fabdem_m": elev.get("fabdem"),
            "datasets": [DATASETS["nasadem"], DATASETS["fabdem"]],
        },
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(result, indent=2))
    return result
