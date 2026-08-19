"""Land-change witness. Dynamic World top-1 labels plus an NLCD check.

Mean class-probability scores are invalid. Disagreement does not pick a winner.
"""

from __future__ import annotations

from pathlib import Path

from expedition.adapters.earth import _import_ee, EE_PROJECT
from expedition.adapters.witness import (
    fact_atom,
    load_replay,
    support,
    unknown_atom,
    write_payload,
)
from expedition.evidence import utc_now


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "fixtures" / "change"
CACHE_DIR = ROOT / "var" / "cache" / "earth" / "change"

DYNAMIC_WORLD = "GOOGLE/DYNAMICWORLD/V1"
NLCD = "USGS/NLCD_RELEASES/2021_REL/NLCD"
NLCD_2016 = "USGS/NLCD_RELEASES/2016_REL/NLCD"
DW_URL = "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1"
NLCD_URL = "https://developers.google.com/earth-engine/datasets/catalog/USGS_NLCD_RELEASES_2021_REL_NLCD"
TRANSFORM = "land-change-thresholded-v1"
EARLY_WINDOW = "2016-01-01/2018-12-31"
LATE_WINDOW = "2022-01-01/2024-12-31"
SITE_M = 60
NEIGHBOR_M = 250

DW_NAMES = {
    0: "water",
    1: "trees",
    2: "grass",
    3: "flooded_vegetation",
    4: "crops",
    5: "shrub_and_scrub",
    6: "built",
    7: "bare",
    8: "snow_and_ice",
}


def land_change(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> tuple[list, dict]:
    cache_root = cache_dir or CACHE_DIR
    fixture_root = fixture_dir or FIXTURE_DIR
    if live:
        payload = _live_change(lat, lng)
        payload.update({"candidate_id": candidate_id, "lat": lat, "lng": lng, "fetched_at": utc_now()})
        write_payload(candidate_id, cache_root, payload)
    else:
        payload = load_replay(candidate_id, lat, lng, cache_root, fixture_root)

    if not payload or "land_change" not in payload:
        message = "land-change unavailable; run a bounded live witness to populate replay"
        return [
            unknown_atom(
                candidate_id=candidate_id,
                question_id="land.change",
                field_id="land_cover_change",
                source=DYNAMIC_WORLD,
                source_url=DW_URL,
                source_family="DYNAMIC_WORLD",
                lat=lat,
                lng=lng,
                transform=TRANSFORM,
                message=message,
            )
        ], {}

    change = payload["land_change"]
    fetched = payload.get("fetched_at") or utc_now()
    geom = support(
        lat,
        lng,
        radius_m=SITE_M,
        purpose="dynamic_world_top1_site_context_not_parcel",
        extra=f"buffer:{SITE_M}:dw:10m:nlcd:30m:{EARLY_WINDOW}:{LATE_WINDOW}",
    )
    agreement = change.get("agreement") or "unknown"
    kind = "FACT" if agreement in {"agree", "stable"} else "MODEL" if agreement == "disagree" else "UNKNOWN"
    notes = (
        "Thresholded Dynamic World top-1 labels plus NLCD developed fraction. "
        "Neighborhood buffer is context, not parcel condition. "
        "Sources in disagreement are a Verification Gap, not a chosen truth. "
        "Not a construction permit, listing, or competition proof."
    )
    atom = fact_atom(
        candidate_id=candidate_id,
        question_id="land.change",
        field_id="land_cover_change",
        value=change,
        unit=None,
        source=DYNAMIC_WORLD,
        source_url=DW_URL,
        source_family="DYNAMIC_WORLD",
        independence_group="DYNAMIC_WORLD",
        support_geom=geom,
        observed_at=f"{EARLY_WINDOW}|{LATE_WINDOW}",
        fetched_at=fetched,
        dataset_vintage="Dynamic World + NLCD 2016/2021",
        transform=TRANSFORM,
        live=live,
        notes=notes,
        window=f"{EARLY_WINDOW}|{LATE_WINDOW}",
        kind=kind if kind != "UNKNOWN" else "FACT",
        authority="authoritative" if agreement in {"agree", "stable"} else "model",
        confidence="medium" if agreement in {"agree", "stable"} else "low",
        decision_effect="INFORM",
    )
    return [atom], payload


def classify(change: dict) -> dict:
    """Deterministic change type from thresholded fractions. No mean-probability score."""
    dw = change.get("dynamic_world") or {}
    nlcd = change.get("nlcd") or {}
    dw_delta = (dw.get("late_built_frac") or 0) - (dw.get("early_built_frac") or 0)
    nlcd_delta = (nlcd.get("late_developed_frac") or 0) - (nlcd.get("early_developed_frac") or 0)
    dw_gain = dw_delta >= 0.15
    dw_loss = dw_delta <= -0.15
    nlcd_gain = nlcd_delta >= 0.10
    nlcd_loss = nlcd_delta <= -0.10
    if dw_gain and nlcd_loss or dw_loss and nlcd_gain:
        agreement = "disagree"
        change_type = "disagreement"
    elif dw_gain and (nlcd_gain or abs(nlcd_delta) < 0.10):
        agreement = "agree" if nlcd_gain else "partial"
        change_type = "built_gain"
    elif dw_loss and (nlcd_loss or abs(nlcd_delta) < 0.10):
        agreement = "agree" if nlcd_loss else "partial"
        change_type = "built_loss"
    elif abs(dw_delta) < 0.15 and abs(nlcd_delta) < 0.10:
        agreement = "stable"
        change_type = "stable"
    else:
        agreement = "partial"
        change_type = "other"
    out = dict(change)
    out.update({
        "change_type": change_type,
        "agreement": agreement,
        "dw_built_delta": round(dw_delta, 4),
        "nlcd_developed_delta": round(nlcd_delta, 4),
        "score_used": False,
    })
    return out


def _live_change(lat: float, lng: float) -> dict:
    ee = _import_ee()
    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lng, lat])
    site = point.buffer(SITE_M)
    neighbor = point.buffer(NEIGHBOR_M)

    def dw_stats(start, end, geom):
        col = (
            ee.ImageCollection(DYNAMIC_WORLD)
            .filterBounds(geom)
            .filterDate(start, end)
            .select("label")
        )
        mode = col.mode().reduceRegion(ee.Reducer.mode(), geom, 10, maxPixels=1e6).get("label")
        built = (
            col.map(lambda im: im.eq(6))
            .mean()
            .reduceRegion(ee.Reducer.mean(), geom, 10, maxPixels=1e6)
            .get("label")
        )
        return ee.Dictionary({"mode": mode, "built_frac": built})

    early_site = dw_stats("2016-01-01", "2019-01-01", site)
    late_site = dw_stats("2022-01-01", "2025-01-01", site)
    late_neighbor = dw_stats("2022-01-01", "2025-01-01", neighbor)

    nlcd_early = ee.Image(f"{NLCD_2016}/2016").select("landcover")
    nlcd_late = ee.Image(f"{NLCD}/2021").select("landcover")

    def developed(image, geom):
        frac = image.gte(21).And(image.lte(24)).reduceRegion(
            ee.Reducer.mean(), geom, 30, maxPixels=1e6
        ).get("landcover")
        mode = image.reduceRegion(ee.Reducer.mode(), geom, 30, maxPixels=1e6).get("landcover")
        return ee.Dictionary({"mode": mode, "developed_frac": frac})

    raw = ee.Dictionary({
        "early_site": early_site,
        "late_site": late_site,
        "late_neighbor": late_neighbor,
        "nlcd_early": developed(nlcd_early, site),
        "nlcd_late": developed(nlcd_late, site),
    }).getInfo()

    def _num(value):
        return None if value is None else round(float(value), 4)

    def _mode(block, names):
        code = block.get("mode")
        if code is None:
            return None
        code = int(code)
        return {"code": code, "label": names.get(code, "other")}

    dw = {
        "early_mode": _mode(raw["early_site"], DW_NAMES),
        "late_mode": _mode(raw["late_site"], DW_NAMES),
        "early_built_frac": _num(raw["early_site"].get("built_frac")),
        "late_built_frac": _num(raw["late_site"].get("built_frac")),
        "neighbor_built_frac": _num(raw["late_neighbor"].get("built_frac")),
        "scale_m": 10,
        "windows": {"early": EARLY_WINDOW, "late": LATE_WINDOW},
    }
    nlcd = {
        "early_developed_frac": _num(raw["nlcd_early"].get("developed_frac")),
        "late_developed_frac": _num(raw["nlcd_late"].get("developed_frac")),
        "early_mode": raw["nlcd_early"].get("mode"),
        "late_mode": raw["nlcd_late"].get("mode"),
        "scale_m": 30,
        "years": [2016, 2021],
    }
    change = classify({
        "dynamic_world": dw,
        "nlcd": nlcd,
        "site_radius_m": SITE_M,
        "neighborhood_radius_m": NEIGHBOR_M,
    })
    return {"land_change": change}
