"""Parcel Rewind — trial 1.

For one point, build a year-by-year water-frequency timeline from JRC
MonthlyHistory and find the year reality diverged from the cited record.
Fuses with the Mireye facts already fetched for the site (San Leon).
"""
import json
import sys
from pathlib import Path

import ee

ee.Initialize(project="gen-lang-client-0261050164")

SITE = {"name": "san_leon_rising", "lat": 29.475732110989398, "lng": -94.96653315875905}
OUT = Path(__file__).parent / "san_leon_rewind.json"

pt = ee.Geometry.Point([SITE["lng"], SITE["lat"]])
region = pt.buffer(60)  # ~2 JRC pixels around the point

monthly = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")

def year_freq(y):
    y = ee.Number(y)
    yr = monthly.filter(ee.Filter.calendarRange(y, y, "year"))
    # water class == 2; unmask(0) so no-obs months count as dry, not poison
    freq = yr.map(lambda im: im.eq(2).unmask(0)).mean()
    obs = yr.map(lambda im: im.gte(1).unmask(0)).mean()  # observed at all
    stats = freq.addBands(obs).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=30, maxPixels=1e8
    )
    return ee.Feature(None, {
        "year": y,
        "water_freq": stats.get("water"),
        "obs_freq": stats.get("water_1"),
    })

years = ee.List.sequence(1985, 2021)
fc = ee.FeatureCollection(years.map(year_freq))
rows = fc.getInfo()["features"]

timeline = [
    {
        "year": int(f["properties"]["year"]),
        "water_freq": round(f["properties"]["water_freq"] or 0.0, 4),
        "obs_freq": round(f["properties"]["obs_freq"] or 0.0, 4),
    }
    for f in rows
]

# crude breakpoint: first year where a 5-yr trailing mean doubles the 1985-1999 baseline
base_years = [t["water_freq"] for t in timeline if t["year"] < 2000]
baseline = sum(base_years) / len(base_years) if base_years else 0.0
breakpoint_year = None
for i, t in enumerate(timeline):
    if t["year"] < 2000 or i < 4:
        continue
    trailing = sum(x["water_freq"] for x in timeline[i - 4 : i + 1]) / 5
    if baseline >= 0 and trailing > max(2 * baseline, baseline + 0.02):
        breakpoint_year = t["year"]
        break

# independent elevation second opinion at same point
elev = ee.Image("NASA/NASADEM_HGT/001").select("elevation").addBands(
    ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("fabdem")
).reduceRegion(ee.Reducer.mean(), region, 30).getInfo()

result = {
    "site": SITE,
    "mireye_record": {
        "fema_flood_zone": {"value": "AE", "vintage": "48167C_STUDY1", "source": "FEMA_NFHL"},
        "surface_water_permanence_pct": {"value": 5.0, "source": "JRC_GSW"},
        "elevation_m": {"value": 2.37, "source": "USGS_3DEP_COG"},
        "intersects_wetland": {"value": True, "source": "USFWS_NWI"},
    },
    "rewind": {
        "baseline_water_freq_1985_1999": round(baseline, 4),
        "latest_water_freq_2021": timeline[-1]["water_freq"],
        "breakpoint_year": breakpoint_year,
        "timeline": timeline,
    },
    "second_opinion": {
        "nasadem_m": elev.get("elevation"),
        "fabdem_m": elev.get("fabdem"),
        "mireye_3dep_m": 2.37,
    },
}

OUT.write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result["rewind"].items() if k != "timeline"}, indent=2))
print("second_opinion:", json.dumps(result["second_opinion"]))
print(f"saved -> {OUT}", file=sys.stderr)
