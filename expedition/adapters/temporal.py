"""Selective Earth Engine witnesses for Farm and Data Center Missions.

The adapter is replay-first. Live calls are bounded to the declared historical
windows and write a geometry-aware cache for later replay.
"""

from __future__ import annotations

import json
from pathlib import Path

from expedition.adapters.earth import EE_PROJECT, _import_ee
from expedition.evidence import EvidenceAtom, cache_identity, geometry_hash, utc_now


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "fixtures" / "earth"
CACHE_DIR = ROOT / "var" / "cache" / "earth" / "temporal"

CDL = "USDA/NASS/CDL"
CHIRPS = "UCSB-CHG/CHIRPS/DAILY"
MODIS_LST = "MODIS/061/MOD11A1"

CDL_URL = "https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL"
CHIRPS_URL = "https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY"
MODIS_URL = "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1"

FARM_WINDOW = "2016-01-01/2024-12-31"
HEAT_WINDOW = "2024-06-01/2024-08-31"
FARM_TRANSFORM = "farm-history-ee-v1"
HEAT_TRANSFORM = "modis-summer-lst-qa-v1"

CDL_NAMES = {1: "Corn", 2: "Cotton", 5: "Soybeans"}


def _safe_id(candidate_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id)


def _payload_path(candidate_id: str, root: Path) -> Path:
    return root / f"{_safe_id(candidate_id)}.json"


def _load_replay(
    candidate_id: str,
    lat: float,
    lng: float,
    cache_dir: Path,
    fixture_dir: Path,
) -> dict | None:
    for path in (_payload_path(candidate_id, cache_dir), _payload_path(candidate_id, fixture_dir)):
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            cached_lat = payload.get("lat")
            cached_lng = payload.get("lng")
            if not isinstance(cached_lat, (int, float)) or not isinstance(cached_lng, (int, float)):
                continue
            if abs(float(cached_lat) - lat) <= 1e-7 and abs(float(cached_lng) - lng) <= 1e-7:
                return payload
    return None


def _support(
    lat: float,
    lng: float,
    *,
    radius_m: int | None,
    purpose: str,
    extra: str,
) -> dict:
    return {
        "kind": "buffer" if radius_m is not None else "point",
        "crs": "EPSG:4326",
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "radius_purpose": purpose if radius_m is not None else None,
        "parcel_id": None,
        "parcel_grade": False,
        "geometry_hash": geometry_hash(lat, lng, extra),
    }


def _atom(
    *,
    candidate_id: str,
    question_id: str,
    field_id: str,
    value,
    unit: str | None,
    source: str,
    source_url: str,
    source_family: str,
    independence_group: str,
    support: dict,
    observed_at: str,
    fetched_at: str,
    dataset_vintage: str,
    transform: str,
    live: bool,
    notes: str,
    window: str,
    confidence: str = "medium",
) -> EvidenceAtom:
    status = "live" if live else "replay"
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:{status}",
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind="FACT",
        status=status,
        decision_effect="INFORM",
        value=value,
        unit=unit,
        source=source,
        source_url=source_url,
        source_family=source_family,
        independence_group=independence_group,
        authority="authoritative",
        support=support,
        observed_at=observed_at,
        fetched_at=fetched_at,
        dataset_vintage=dataset_vintage,
        ttl=None,
        confidence=confidence,
        notes=notes,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": "ee"},
        citation={
            "source": source,
            "source_url": source_url,
            "fetched_at": fetched_at,
            "dataset_vintage": dataset_vintage,
        },
        transform_version=transform,
        cache_identity=cache_identity(
            "earth-engine",
            source,
            field_id,
            transform,
            support["geometry_hash"],
            f"{support['kind']}:{support.get('radius_m')}:{support.get('radius_purpose')}",
            window,
        ),
        live_label="live" if live else "replay",
    )


def _unknown(
    *,
    candidate_id: str,
    question_id: str,
    field_id: str,
    source: str,
    source_url: str,
    source_family: str,
    lat: float,
    lng: float,
    transform: str,
    message: str,
) -> EvidenceAtom:
    fetched = utc_now()
    support = _support(lat, lng, radius_m=None, purpose="", extra=field_id)
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:failed",
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind="UNKNOWN",
        status="failed",
        decision_effect="UNKNOWN",
        value=None,
        unit=None,
        source=source,
        source_url=source_url,
        source_family=source_family,
        independence_group=source_family,
        authority="none",
        support=support,
        observed_at=None,
        fetched_at=fetched,
        dataset_vintage=None,
        ttl=None,
        confidence=None,
        notes=message,
        failure={
            "class": "other",
            "http_status": None,
            "retryable": True,
            "message_public": message,
        },
        cost={"credits": 0, "tokens": 0, "unit": "ee"},
        citation={
            "source": source,
            "source_url": source_url,
            "fetched_at": fetched,
            "dataset_vintage": None,
        },
        transform_version=transform,
        cache_identity=cache_identity(
            "earth-engine", source, field_id, transform, support["geometry_hash"], "point", ""
        ),
        live_label="replay",
    )


def farm_history(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> tuple[list[EvidenceAtom], dict]:
    """Return annual CDL rotation and regional CHIRPS rainfall history."""
    cache_root = cache_dir or CACHE_DIR
    fixture_root = fixture_dir or FIXTURE_DIR
    payload: dict | None
    if live:
        payload = _live_farm(lat, lng)
        payload.update(
            {
                "candidate_id": candidate_id,
                "lat": lat,
                "lng": lng,
                "fetched_at": utc_now(),
            }
        )
        path = _payload_path(candidate_id, cache_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        payload = _load_replay(candidate_id, lat, lng, cache_root, fixture_root)

    if not payload or "farm_history" not in payload:
        message = "farm history unavailable; run a bounded live witness to populate replay"
        return [
            _unknown(
                candidate_id=candidate_id,
                question_id="farm.crop_rotation",
                field_id="annual_cdl_rotation",
                source=CDL,
                source_url=CDL_URL,
                source_family="USDA_CDL",
                lat=lat,
                lng=lng,
                transform=FARM_TRANSFORM,
                message=message,
            ),
            _unknown(
                candidate_id=candidate_id,
                question_id="farm.rainfall_history",
                field_id="chirps_rainfall_history",
                source=CHIRPS,
                source_url=CHIRPS_URL,
                source_family="CHIRPS",
                lat=lat,
                lng=lng,
                transform=FARM_TRANSFORM,
                message=message,
            ),
        ], {}

    history = payload["farm_history"]
    fetched = payload.get("fetched_at") or utc_now()
    cdl_support = _support(
        lat,
        lng,
        radius_m=None,
        purpose="",
        extra="point:cdl:30m:2016-2024",
    )
    rain_support = _support(
        lat,
        lng,
        radius_m=2750,
        purpose="regional_chirps_grid_context_not_parcel_rainfall",
        extra="buffer:2750:chirps:5566m:2016-2024",
    )
    atoms = [
        _atom(
            candidate_id=candidate_id,
            question_id="farm.crop_rotation",
            field_id="annual_cdl_rotation",
            value=history["cdl"],
            unit=None,
            source=CDL,
            source_url=CDL_URL,
            source_family="USDA_CDL",
            independence_group="USDA_CDL",
            support=cdl_support,
            observed_at=FARM_WINDOW,
            fetched_at=fetched,
            dataset_vintage="CDL 2016-2024",
            transform=FARM_TRANSFORM,
            live=live,
            notes=(
                "Annual 30 m crop-class context at the supplied point. Same USDA_CDL "
                "independence group as Mireye crop facts; not yield, field-boundary, or water-right evidence."
            ),
            window=FARM_WINDOW,
        ),
        _atom(
            candidate_id=candidate_id,
            question_id="farm.rainfall_history",
            field_id="chirps_rainfall_history",
            value=history["chirps"],
            unit="millimeters",
            source=CHIRPS,
            source_url=CHIRPS_URL,
            source_family="CHIRPS",
            independence_group="CHIRPS",
            support=rain_support,
            observed_at=FARM_WINDOW,
            fetched_at=fetched,
            dataset_vintage="CHIRPS Daily v2.0",
            transform=FARM_TRANSFORM,
            live=live,
            notes=(
                "Approximately 5.5 km gridded regional rainfall history. Not irrigation, "
                "future rainfall, yield, groundwater availability, or a legal water right."
            ),
            window=FARM_WINDOW,
        ),
    ]
    return atoms, payload


def observed_heat(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> tuple[list[EvidenceAtom], dict]:
    """Return QA-filtered MODIS daytime land-surface heat context."""
    cache_root = cache_dir or CACHE_DIR
    fixture_root = fixture_dir or FIXTURE_DIR
    payload: dict | None
    if live:
        payload = _live_heat(lat, lng)
        payload.update(
            {
                "candidate_id": candidate_id,
                "lat": lat,
                "lng": lng,
                "fetched_at": utc_now(),
            }
        )
        path = _payload_path(candidate_id, cache_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        payload = _load_replay(candidate_id, lat, lng, cache_root, fixture_root)

    if not payload or "observed_heat" not in payload:
        message = "observed surface heat unavailable; run a bounded live witness to populate replay"
        return [
            _unknown(
                candidate_id=candidate_id,
                question_id="data_center.observed_heat",
                field_id="modis_daytime_land_surface_temperature",
                source=MODIS_LST,
                source_url=MODIS_URL,
                source_family="MODIS_LST",
                lat=lat,
                lng=lng,
                transform=HEAT_TRANSFORM,
                message=message,
            )
        ], {}

    fetched = payload.get("fetched_at") or utc_now()
    support = _support(
        lat,
        lng,
        radius_m=500,
        purpose="modis_1km_site_context_compared_with_2km_to_15km_ring",
        extra="buffer:500:ring:2000-15000:modis:1000m:qa:mandatory_good",
    )
    heat = payload["observed_heat"]
    legacy_replay = not live and str(heat.get("qa_filter") or "").startswith("legacy")
    transform = "modis-summer-lst-legacy-v0" if legacy_replay else HEAT_TRANSFORM
    caveat = (
        " Replay fixture predates QC_Day masking; refresh live for the QA-filtered transform."
        if legacy_replay
        else ""
    )
    atom = _atom(
        candidate_id=candidate_id,
        question_id="data_center.observed_heat",
        field_id="modis_daytime_land_surface_temperature",
        value=heat,
        unit="degrees_celsius",
        source=MODIS_LST,
        source_url=MODIS_URL,
        source_family="MODIS_LST",
        independence_group="MODIS_LST",
        support=support,
        observed_at=HEAT_WINDOW,
        fetched_at=fetched,
        dataset_vintage="MOD11A1.061",
        transform=transform,
        live=live,
        notes=(
            "Clear-sky daytime land-surface temperature at approximately 1 km resolution. "
            "Not ambient air temperature, design wet-bulb, worker exposure, cooling load, "
            "deliverable MW, water capacity, or utility commitment."
            + caveat
        ),
        window=HEAT_WINDOW,
        confidence="low" if legacy_replay else "medium",
    )
    return [atom], payload


def _live_farm(lat: float, lng: float) -> dict:
    ee = _import_ee()
    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lng, lat])
    years = list(range(2016, 2025))

    cdl_features = []
    rain_features = []
    for year in years:
        crop = (
            ee.Image(f"{CDL}/{year}")
            .select("cropland")
            .reduceRegion(ee.Reducer.mode(), point, 30, maxPixels=1e6)
            .get("cropland")
        )
        rain = (
            ee.ImageCollection(CHIRPS)
            .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            .select("precipitation")
            .sum()
            .reduceRegion(ee.Reducer.mean(), point.buffer(2750), 5566, maxPixels=1e6)
            .get("precipitation")
        )
        cdl_features.append(ee.Feature(None, {"year": year, "code": crop}))
        rain_features.append(ee.Feature(None, {"year": year, "precip_mm": rain}))

    cdl_rows = ee.FeatureCollection(cdl_features).getInfo()["features"]
    rain_rows = ee.FeatureCollection(rain_features).getInfo()["features"]
    series = []
    for row in cdl_rows:
        props = row["properties"]
        code = int(props["code"]) if props.get("code") is not None else None
        series.append(
            {"year": int(props["year"]), "code": code, "label": CDL_NAMES.get(code, "Other")}
        )
    annual_rain = [
        {"year": int(row["properties"]["year"]), "precip_mm": round(row["properties"]["precip_mm"], 1)}
        for row in rain_rows
        if row["properties"].get("precip_mm") is not None
    ]
    rain_mean = (
        round(sum(row["precip_mm"] for row in annual_rain) / len(annual_rain), 1)
        if annual_rain
        else None
    )
    transitions = sum(
        left.get("code") != right.get("code")
        for left, right in zip(series, series[1:])
        if left.get("code") is not None and right.get("code") is not None
    )
    return {
        "farm_history": {
            "window": FARM_WINDOW,
            "cdl": {"annual_series": series, "transition_count": transitions, "scale_m": 30},
            "chirps": {
                "annual_series": annual_rain,
                "annual_mean_mm": rain_mean,
                "nominal_scale_m": 5566,
            },
        }
    }


def _live_heat(lat: float, lng: float) -> dict:
    ee = _import_ee()
    ee.Initialize(project=EE_PROJECT)
    point = ee.Geometry.Point([lng, lat])
    site = point.buffer(500)
    ring = point.buffer(15000).difference(point.buffer(2000), 1)
    raw = (
        ee.ImageCollection(MODIS_LST)
        .filterBounds(site)
        .filterDate("2024-06-01", "2024-09-01")
        .select(["LST_Day_1km", "QC_Day"])
    )

    def good_lst(image):
        quality = image.select("QC_Day").bitwiseAnd(3).eq(0)
        return (
            image.select("LST_Day_1km")
            .updateMask(quality)
            .multiply(0.02)
            .subtract(273.15)
            .rename("lst_c")
        )

    good = raw.map(good_lst)
    mean = good.mean()
    count = good.count()
    site_mean = mean.reduceRegion(ee.Reducer.mean(), site, 1000, maxPixels=1e6).get("lst_c")
    ring_mean = mean.reduceRegion(ee.Reducer.mean(), ring, 1000, maxPixels=1e7).get("lst_c")
    valid_count = count.reduceRegion(ee.Reducer.mean(), site, 1000, maxPixels=1e6).get("lst_c")
    result = ee.Dictionary(
        {
            "daytime_mean_c": site_mean,
            "comparison_ring_mean_c": ring_mean,
            "valid_observation_count_mean": valid_count,
            "collection_image_count": raw.size(),
        }
    ).getInfo()
    if result.get("daytime_mean_c") is not None and result.get("comparison_ring_mean_c") is not None:
        result["site_minus_ring_c"] = round(
            result["daytime_mean_c"] - result["comparison_ring_mean_c"], 2
        )
    for key in ("daytime_mean_c", "comparison_ring_mean_c", "valid_observation_count_mean"):
        if result.get(key) is not None:
            result[key] = round(result[key], 2)
    result.update(
        {
            "window": HEAT_WINDOW,
            "nominal_scale_m": 1000,
            "qa_filter": "QC_Day mandatory QA bits 0-1 equal 0",
        }
    )
    return {"observed_heat": result}
