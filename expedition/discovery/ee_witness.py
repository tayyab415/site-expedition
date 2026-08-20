"""Earth Engine Dynamic World sample on known pins. Witness, not a site search.

Google Open Buildings v3 is not US. Ask Google Earth is a browser chat with
no export API. EE stays a raster check on pins you already have.
Dataset: GOOGLE/DYNAMICWORLD/V1
"""

from __future__ import annotations

from dataclasses import replace

from expedition.adapters.earth import EE_PROJECT, _import_ee
from expedition.discovery.schema import Seed

DYNAMIC_WORLD = "GOOGLE/DYNAMICWORLD/V1"
DW_URL = "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1"
EARLY = "2024-01-01"
LATE = "2026-08-01"


def attach_dynamic_world(seeds: list[Seed], *, limit: int = 4) -> tuple[list[Seed], dict]:
    try:
        ee = _import_ee()
        ee.Initialize(project=EE_PROJECT)
    except Exception as exc:
        return seeds, {
            "source": "earth_engine",
            "ok": False,
            "count": 0,
            "note": f"EE unavailable ({type(exc).__name__})",
        }
    n = 0
    err = None
    for i, seed in enumerate(seeds[:limit]):
        try:
            stats = _sample(ee, seed.lat, seed.lng)
        except Exception as exc:
            err = type(exc).__name__
            break
        extra = dict(seed.extra)
        extra["earth_engine"] = {
            "built": stats.get("built"),
            "water": stats.get("water"),
            "crops": stats.get("crops"),
            "dataset": DYNAMIC_WORLD,
            "source_url": DW_URL,
            "note": "Dynamic World class probabilities in a 60 m buffer. Not a parcel.",
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return seeds, {"source": "earth_engine", "ok": err is None, "count": n, "note": err}


def _sample(ee, lat: float, lng: float) -> dict:
    region = ee.Geometry.Point([lng, lat]).buffer(60)
    image = (
        ee.ImageCollection(DYNAMIC_WORLD)
        .filterDate(EARLY, LATE)
        .filterBounds(region)
        .select(["built", "water", "crops"])
        .median()
    )
    return image.reduceRegion(ee.Reducer.mean(), region, 10, maxPixels=1e6).getInfo() or {}
