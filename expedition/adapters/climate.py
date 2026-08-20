"""Climate-trajectory witness. Historical baseline plus a CMIP6 scenario range.

A single model/scenario number is not a prediction. CMIP6 is regional (~25–28 km).
"""

from __future__ import annotations

from pathlib import Path

from expedition.adapters.earth import EE_PROJECT, _import_ee
from expedition.adapters.witness import (
    fact_atom,
    load_replay,
    support,
    unknown_atom,
    write_payload,
)
from expedition.evidence import utc_now


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "fixtures" / "climate"
CACHE_DIR = ROOT / "var" / "cache" / "earth" / "climate"

GRIDMET = "IDAHO_EPSCOR/GRIDMET"
GDDP = "NASA/GDDP-CMIP6"
GRIDMET_URL = "https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_GRIDMET"
GDDP_URL = "https://developers.google.com/earth-engine/datasets/catalog/NASA_GDDP-CMIP6"
TRANSFORM = "climate-trajectory-gddp-range-v1"
HIST_WINDOW = "2010-06-01/2014-08-31"
FUTURE_WINDOW = "2035-06-01/2039-08-31"
MODELS = ("ACCESS-CM2", "MIROC6", "NorESM2-LM", "GFDL-ESM4")
SCENARIOS = ("ssp245", "ssp585")


def climate_trajectory(
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
        payload = _live_climate(lat, lng)
        payload.update({"candidate_id": candidate_id, "lat": lat, "lng": lng, "fetched_at": utc_now()})
        write_payload(candidate_id, cache_root, payload)
    else:
        payload = load_replay(candidate_id, lat, lng, cache_root, fixture_root)

    if not payload or "climate_trajectory" not in payload:
        message = "climate-trajectory unavailable; run a bounded live witness to populate replay"
        return [
            unknown_atom(
                candidate_id=candidate_id,
                question_id="climate.trajectory",
                field_id="cmip6_summer_tmax_range",
                source=GDDP,
                source_url=GDDP_URL,
                source_family="CMIP6_GDDP",
                lat=lat,
                lng=lng,
                transform=TRANSFORM,
                message=message,
            )
        ], {}

    climate = payload["climate_trajectory"]
    fetched = payload.get("fetched_at") or utc_now()
    geom = support(
        lat,
        lng,
        radius_m=14000,
        purpose="gddp_cmip6_regional_grid_not_parcel",
        extra="buffer:14000:gddp:25000:jja:2010-2014:2035-2039",
    )
    atom = fact_atom(
        candidate_id=candidate_id,
        question_id="climate.trajectory",
        field_id="cmip6_summer_tmax_range",
        value=climate,
        unit="degrees_celsius",
        source=GDDP,
        source_url=GDDP_URL,
        source_family="CMIP6_GDDP",
        independence_group="CMIP6_GDDP",
        support_geom=geom,
        observed_at=f"{HIST_WINDOW}|{FUTURE_WINDOW}",
        fetched_at=fetched,
        dataset_vintage="NASA GDDP-CMIP6 + GRIDMET",
        transform=TRANSFORM,
        live=live,
        notes=(
            "Historical June–August tmmx from GRIDMET plus a multi-model NASA GDDP-CMIP6 "
            "range under SSP2-4.5 and SSP5-8.5. Regional (~25–28 km), not parcel-scale. "
            "Not a single prediction, cooling-load study, or water-right forecast."
        ),
        window=f"{HIST_WINDOW}|{FUTURE_WINDOW}",
        kind="MODEL",
        authority="model",
        confidence="low",
    )
    return [atom], payload


def _live_climate(lat: float, lng: float) -> dict:
    ee = _import_ee()
    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lng, lat])
    region = point.buffer(14000)

    hist = (
        ee.ImageCollection(GRIDMET)
        .filterDate("2010-06-01", "2014-09-01")
        .filter(ee.Filter.calendarRange(6, 8, "month"))
        .select("tmmx")
        .mean()
        .subtract(273.15)
        .reduceRegion(ee.Reducer.mean(), region, 4000, maxPixels=1e6)
        .get("tmmx")
    )

    samples = []
    for model in MODELS:
        for scenario in SCENARIOS:
            future = (
                ee.ImageCollection(GDDP)
                .filter(ee.Filter.eq("model", model))
                .filter(ee.Filter.eq("scenario", scenario))
                .filterDate("2035-06-01", "2039-09-01")
                .filter(ee.Filter.calendarRange(6, 8, "month"))
                .select("tasmax")
                .mean()
                .subtract(273.15)
                .reduceRegion(ee.Reducer.mean(), region, 25000, maxPixels=1e6)
                .get("tasmax")
            )
            samples.append(ee.Feature(None, {
                "model": model,
                "scenario": scenario,
                "tmax_c": future,
            }))
    rows = ee.FeatureCollection(samples).getInfo()["features"]
    hist_c = ee.Number(hist).getInfo()
    members = []
    for row in rows:
        props = row["properties"]
        if props.get("tmax_c") is None:
            continue
        members.append({
            "model": props["model"],
            "scenario": props["scenario"],
            "summer_tmax_c": round(float(props["tmax_c"]), 2),
        })
    values = [row["summer_tmax_c"] for row in members]
    values.sort()
    median = values[len(values) // 2] if values else None
    by_scenario = {}
    for scenario in SCENARIOS:
        subset = [row["summer_tmax_c"] for row in members if row["scenario"] == scenario]
        if not subset:
            continue
        subset.sort()
        by_scenario[scenario] = {
            "min_c": round(min(subset), 2),
            "median_c": subset[len(subset) // 2],
            "max_c": round(max(subset), 2),
        }
    hist_round = None if hist_c is None else round(float(hist_c), 2)
    deltas = None
    if hist_round is not None and values:
        deltas = {
            "min_c": round(min(values) - hist_round, 2),
            "median_c": round(median - hist_round, 2) if median is not None else None,
            "max_c": round(max(values) - hist_round, 2),
        }
    return {
        "climate_trajectory": {
            "historical_summer_tmax_c": hist_round,
            "historical_source": GRIDMET,
            "historical_window": HIST_WINDOW,
            "future_window": FUTURE_WINDOW,
            "models": list(MODELS),
            "scenarios": list(SCENARIOS),
            "members": members,
            "range_c": {
                "min_c": min(values) if values else None,
                "median_c": median,
                "max_c": max(values) if values else None,
            },
            "by_scenario": by_scenario,
            "delta_from_historical_c": deltas,
            "nominal_scale_km": 28,
            "prediction": False,
        }
    }
