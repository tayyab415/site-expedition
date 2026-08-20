"""INFORM-only stretch skills: land-change, labor-access, climate-trajectory, source-scout.

Replay-first. None of these score. Unknown stays Conditional. Home never
receives labor-access. Source Scout is a constrained official follow-up catalog,
not arbitrary web discovery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from expedition.evidence import EvidenceAtom, cache_identity, geometry_hash, utc_now


ROOT = Path(__file__).resolve().parents[1]
LAND_DIR = ROOT / "data" / "fixtures" / "land_change"
CLIMATE_DIR = ROOT / "data" / "fixtures" / "climate"
LABOR_DIR = ROOT / "data" / "fixtures" / "labor"

DW = "GOOGLE/DYNAMICWORLD/V1"
DW_URL = "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1"
GDDP = "NASA/GDDP-CMIP6"
GDDP_URL = "https://developers.google.com/earth-engine/datasets/catalog/NASA_GDDP-CMIP6"

LAND_TRANSFORM = "land-change-thresholded-v1"
CLIMATE_TRANSFORM = "gddp-cmip6-ensemble-range-v1"
LABOR_TRANSFORM = "labor-shed-context-v1"
SCOUT_TRANSFORM = "official-followup-catalog-v1"

FEMA_MSC = "https://msc.fema.gov/portal/home"
EPA_ECHO = "https://echo.epa.gov/"
USGS_3DEP = "https://www.usgs.gov/3d-elevation-program"
NWI = "https://www.fws.gov/program/national-wetlands-inventory"
CROPScape = "https://nassgeodata.gmu.edu/CropScape/"

LAND_LIMITATION = (
    "Thresholded Dynamic World top-1 labels, with an NLCD developed-fraction "
    "check when the fixture carries one. INFORM only. Not scored. "
    "Disagreement is a Verification Gap, not a chosen truth."
)
CLIMATE_LIMITATION = (
    "GRIDMET historical June–August tmmx plus a NASA GDDP-CMIP6 multi-model "
    "range under SSP2-4.5 and SSP5-8.5. Regional (~28 km), not a parcel "
    "prediction. INFORM only."
)
LABOR_LIMITATION = (
    "County or commute context only. Does not claim workers are available to hire. "
    "Declared logistics destinations are not a labor shed."
)


def _safe_id(candidate_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id)


def _load_fixture(directory: Path, candidate_id: str, lat: float, lng: float) -> dict | None:
    path = directory / f"{_safe_id(candidate_id)}.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    cached_lat = payload.get("lat")
    cached_lng = payload.get("lng")
    if not isinstance(cached_lat, (int, float)) or not isinstance(cached_lng, (int, float)):
        return None
    if abs(float(cached_lat) - lat) > 1e-7 or abs(float(cached_lng) - lng) > 1e-7:
        return None
    return payload


def _load_first(candidate_id: str, lat: float, lng: float, *directories: Path) -> dict | None:
    for directory in directories:
        payload = _load_fixture(directory, candidate_id, lat, lng)
        if payload:
            return payload
    return None


def _flatten_land(change: dict) -> dict:
    dw = change.get("dynamic_world") if isinstance(change.get("dynamic_world"), dict) else {}
    nlcd = change.get("nlcd") if isinstance(change.get("nlcd"), dict) else {}
    early = change.get("early_built_frac")
    if early is None:
        early = dw.get("early_built_frac")
    late = change.get("late_built_frac")
    if late is None:
        late = dw.get("late_built_frac")
    windows = dw.get("windows") if isinstance(dw.get("windows"), dict) else {}
    out = dict(change)
    out["early_built_frac"] = early
    out["late_built_frac"] = late
    out["early_window"] = change.get("early_window") or windows.get("early")
    out["late_window"] = change.get("late_window") or windows.get("late")
    out["buffer_m"] = change.get("buffer_m") or change.get("neighborhood_radius_m") or 1000
    out["method"] = change.get("method") or change.get("change_type") or "thresholded_top1"
    out["validated_against_nlcd"] = bool(nlcd) or bool(change.get("validated_against_nlcd"))
    out["nlcd_developed_delta"] = change.get("nlcd_developed_delta") or (
        None if not nlcd else (nlcd.get("late_developed_frac") or 0) - (nlcd.get("early_developed_frac") or 0)
    )
    out["agreement"] = change.get("agreement")
    out["score_used"] = False
    return out


def _support(lat: float, lng: float, *, radius_m: int | None, purpose: str, extra: str) -> dict:
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
    value: Any,
    source: str,
    source_url: str,
    source_family: str,
    independence_group: str,
    support: dict,
    fetched_at: str,
    dataset_vintage: str | None,
    transform: str,
    notes: str,
    kind: str = "FACT",
    observed_at: str | None = None,
    unit: str | None = None,
    confidence: str = "low",
    live_label: str = "replay",
) -> EvidenceAtom:
    used_live = live_label == "live"
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:{'live' if used_live else 'replay'}",
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind=kind,
        status="live" if used_live else "replay",
        decision_effect="INFORM",
        value=value,
        unit=unit,
        source=source,
        source_url=source_url,
        source_family=source_family,
        independence_group=independence_group,
        authority="none",
        support=support,
        observed_at=observed_at,
        fetched_at=fetched_at,
        dataset_vintage=dataset_vintage,
        ttl=None,
        confidence=confidence,
        notes=notes,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": live_label},
        citation={
            "source": source,
            "source_url": source_url,
            "fetched_at": fetched_at,
            "dataset_vintage": dataset_vintage,
        },
        transform_version=transform,
        cache_identity=cache_identity(
            "expedition-inform",
            source,
            field_id,
            transform,
            support["geometry_hash"],
            f"{support['kind']}:{support.get('radius_m')}:{support.get('radius_purpose')}",
        ),
        live_label=live_label,
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
        atom_id=f"{candidate_id}:{field_id}:unknown",
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
        cost={"credits": 0, "tokens": 0, "unit": "replay"},
        citation={
            "source": source,
            "source_url": source_url,
            "fetched_at": fetched,
            "dataset_vintage": None,
        },
        transform_version=transform,
        cache_identity=cache_identity(
            "expedition-inform", source, field_id, transform, support["geometry_hash"], "point", ""
        ),
        live_label="replay",
    )


def _emit_land(
    candidate_id: str,
    lat: float,
    lng: float,
    payload: dict,
    *,
    live_label: str,
) -> tuple[list[EvidenceAtom], dict]:
    change = _flatten_land(payload["land_change"])
    fetched = payload.get("fetched_at") or utc_now()
    support = _support(
        lat,
        lng,
        radius_m=int(change.get("buffer_m") or 1000),
        purpose="neighborhood_built_fraction_not_parcel",
        extra="buffer:1000:dw:modal-top1-built",
    )
    atom = _atom(
        candidate_id=candidate_id,
        question_id="land.change",
        field_id="dw_built_fraction_change",
        value=change,
        source=DW,
        source_url=DW_URL,
        source_family="DYNAMIC_WORLD",
        independence_group="DYNAMIC_WORLD",
        support=support,
        fetched_at=fetched,
        dataset_vintage=change.get("late_window"),
        transform=LAND_TRANSFORM,
        notes=LAND_LIMITATION,
        observed_at=change.get("late_window"),
        unit="fraction",
        live_label=live_label,
    )
    witness = {
        "kind": "land_change",
        "source": DW,
        "independence_group": "DYNAMIC_WORLD",
        "early_built_frac": change.get("early_built_frac"),
        "late_built_frac": change.get("late_built_frac"),
        "early_window": change.get("early_window"),
        "late_window": change.get("late_window"),
        "buffer_m": change.get("buffer_m"),
        "method": change.get("method"),
    }
    return [atom], {"land_change": change, "witness": witness}


def land_change(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool = False,
) -> tuple[list[EvidenceAtom], dict]:
    if live:
        try:
            from expedition.adapters import change as change_mod

            _atoms, payload = change_mod.land_change(
                candidate_id=candidate_id,
                lat=lat,
                lng=lng,
                live=True,
            )
            if payload.get("land_change"):
                return _emit_land(candidate_id, lat, lng, payload, live_label="live")
        except Exception:
            pass
    payload = _load_first(candidate_id, lat, lng, ROOT / "data" / "fixtures" / "change", LAND_DIR)
    if not payload:
        atom = _unknown(
            candidate_id=candidate_id,
            question_id="land.change",
            field_id="dw_built_fraction_change",
            source=DW,
            source_url=DW_URL,
            source_family="DYNAMIC_WORLD",
            lat=lat,
            lng=lng,
            transform=LAND_TRANSFORM,
            message=(
                "No land-change replay for this pin. Live Dynamic World + NLCD "
                "is available on the bounded Earth Engine path."
            ),
        )
        return [atom], {}
    return _emit_land(candidate_id, lat, lng, payload, live_label="replay")


def _emit_climate(
    candidate_id: str,
    lat: float,
    lng: float,
    payload: dict,
    *,
    live_label: str,
) -> tuple[list[EvidenceAtom], dict]:
    climate = dict(payload["climate_trajectory"])
    delta = climate.get("delta_c")
    if delta is None:
        delta = (climate.get("delta_from_historical_c") or {}).get("median_c")
    climate["delta_c"] = delta
    climate.setdefault("model", "CMIP6-ensemble")
    climate.setdefault("ssp", "ssp245+ssp585")
    climate.setdefault("baseline", climate.get("historical_summer_tmax_c") or climate.get("historical_window"))
    climate.setdefault("horizon", climate.get("future_window"))
    climate.setdefault("models", ["ACCESS-CM2", "MIROC6", "NorESM2-LM", "GFDL-ESM4"])
    climate["prediction"] = False
    fetched = payload.get("fetched_at") or utc_now()
    support = _support(
        lat,
        lng,
        radius_m=None,
        purpose="",
        extra="point:gddp:cmip6:ensemble:jja-tasmax",
    )
    atom = _atom(
        candidate_id=candidate_id,
        question_id="climate.trajectory",
        field_id="climate_scenario_tasmax",
        value=climate,
        source=GDDP,
        source_url=GDDP_URL,
        source_family="NASA_GDDP",
        independence_group="NASA_GDDP",
        support=support,
        fetched_at=fetched,
        dataset_vintage=climate.get("horizon"),
        transform=CLIMATE_TRANSFORM,
        notes=CLIMATE_LIMITATION,
        kind="MODEL",
        observed_at=climate.get("horizon"),
        unit="degC",
        confidence="low",
        live_label=live_label,
    )
    return [atom], {"climate_trajectory": climate}


def climate_trajectory(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool = False,
) -> tuple[list[EvidenceAtom], dict]:
    if live:
        try:
            from expedition.adapters import climate as climate_mod

            _atoms, payload = climate_mod.climate_trajectory(
                candidate_id=candidate_id,
                lat=lat,
                lng=lng,
                live=True,
            )
            if payload.get("climate_trajectory"):
                return _emit_climate(candidate_id, lat, lng, payload, live_label="live")
        except Exception:
            pass
    payload = _load_fixture(CLIMATE_DIR, candidate_id, lat, lng)
    if not payload:
        atom = _unknown(
            candidate_id=candidate_id,
            question_id="climate.trajectory",
            field_id="climate_scenario_tasmax",
            source=GDDP,
            source_url=GDDP_URL,
            source_family="NASA_GDDP",
            lat=lat,
            lng=lng,
            transform=CLIMATE_TRANSFORM,
            message=(
                "No NASA GDDP-CMIP6 replay for this pin. Live ensemble path uses "
                "GRIDMET plus a labeled multi-model range."
            ),
        )
        return [atom], {}
    return _emit_climate(candidate_id, lat, lng, payload, live_label="replay")


def labor_access(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    mission: str,
    live: bool = False,
) -> tuple[list[EvidenceAtom], dict]:
    if mission == "home":
        return [], {}
    payload = None
    live_label = "replay"
    if live:
        try:
            from expedition.adapters import labor as labor_mod

            _atoms, live_payload = labor_mod.labor_access(
                candidate_id=candidate_id,
                lat=lat,
                lng=lng,
                live=True,
            )
            if live_payload.get("labor_access") or live_payload.get("labor"):
                payload = live_payload
                live_label = "live"
        except Exception:
            payload = None
    if payload is None:
        payload = _load_fixture(LABOR_DIR, candidate_id, lat, lng)
        live_label = "replay"
    fetched = (payload or {}).get("fetched_at") or utc_now()
    raw = (payload or {}).get("labor") or (payload or {}).get("labor_access") or {}
    context = {
        "labor_shed_declared": bool(raw.get("labor_shed_declared")),
        "county": raw.get("county") or raw.get("county_name"),
        "availability_claim": False,
        "civilian_labor_force": raw.get("civilian_labor_force"),
        "civilian_employed": raw.get("civilian_employed"),
        "mean_commute_minutes": raw.get("mean_commute_minutes"),
        "lodes": raw.get("lodes"),
        "workers_available": None,
        "commute_proxy": raw.get("commute_proxy"),
    }
    if payload is None:
        atom = _unknown(
            candidate_id=candidate_id,
            question_id="labor.access",
            field_id="labor_shed_context",
            source="Census / LODES (not fetched)",
            source_url="https://lehd.ces.census.gov/data/",
            source_family="CENSUS_LODES",
            lat=lat,
            lng=lng,
            transform=LABOR_TRANSFORM,
            message=(
                "No declared labor shed pin and no county labor fixture. "
                "LODES workplace-residence flows are not on this path. "
                + LABOR_LIMITATION
            ),
        )
        return [atom], {}
    support = _support(lat, lng, radius_m=None, purpose="", extra="point:labor-shed-undeclared")
    atom = _atom(
        candidate_id=candidate_id,
        question_id="labor.access",
        field_id="labor_shed_context",
        value=context,
        source="expedition labor-access catalog",
        source_url="https://lehd.ces.census.gov/data/",
        source_family="CENSUS_LODES",
        independence_group="CENSUS_LODES",
        support=support,
        fetched_at=fetched,
        dataset_vintage=None,
        transform=LABOR_TRANSFORM,
        notes=LABOR_LIMITATION,
        kind="PROXY",
        confidence="low",
        live_label=live_label,
    )
    return [atom], {"labor": context}


def _material_flags(atoms: list[EvidenceAtom]) -> set[str]:
    flags: set[str] = set()
    for atom in atoms:
        if atom.kind not in {"FACT", "PROXY"} or atom.status not in {"live", "replay"}:
            continue
        if atom.field_id in {"fema_flood_zone", "within_floodplain_polygon"}:
            flags.add("flood")
        if atom.field_id in {"elevation", "nasadem_elevation"}:
            flags.add("elevation")
        if atom.field_id == "intersects_wetland":
            flags.add("wetland")
        if atom.field_id in {
            "nearest_hazardous_facility_distance_m",
            "epa_rmp_facility_record",
            "nearest_superfund_distance_m",
        }:
            flags.add("environmental")
        if atom.field_id in {"is_cultivated", "dominant_crop_5y", "annual_cdl_rotation"}:
            flags.add("farm")
    return flags


def source_scout(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    mission: str,
    core_atoms: list[EvidenceAtom],
    live: bool = False,
    anticipated_gaps: list[str] | None = None,
) -> tuple[list[EvidenceAtom], dict]:
    del live
    from expedition.adapters.scout import CATALOG as GAP_CATALOG

    flags = _material_flags(core_atoms)
    catalog = [
        {
            "id": "fema_msc",
            "title": "FEMA Map Service Center",
            "url": FEMA_MSC,
            "when": "flood",
            "reason": "Official flood-map follow-up. FEMA still decides mapped SFHA.",
        },
        {
            "id": "epa_echo",
            "title": "EPA ECHO",
            "url": EPA_ECHO,
            "when": "environmental",
            "reason": "Official facility-record follow-up after an environmental proximity hit.",
        },
        {
            "id": "usgs_3dep",
            "title": "USGS 3DEP",
            "url": USGS_3DEP,
            "when": "elevation",
            "reason": "Official elevation program. Do not pick a favorable DEM.",
        },
        {
            "id": "usfws_nwi",
            "title": "USFWS National Wetlands Inventory",
            "url": NWI,
            "when": "wetland",
            "reason": "Official wetlands inventory follow-up.",
        },
        {
            "id": "usda_cropscape",
            "title": "USDA CropScape",
            "url": CROPScape,
            "when": "farm",
            "reason": "Official CDL viewer. Not yield and not a water right.",
        },
    ]
    wanted = set(flags) or (
        {"farm"} if mission == "farm" else {"flood", "elevation"}
    )
    followups = [row for row in catalog if row["when"] in wanted]
    if not followups:
        followups = [row for row in catalog if row["when"] in {"flood", "elevation"}]
    seen_urls = {row["url"] for row in followups}
    for gap_id in anticipated_gaps or []:
        entry = GAP_CATALOG.get(gap_id)
        if not entry:
            continue
        url = next((item for item in entry.get("urls") or [] if item), None)
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        followups.append({
            "id": gap_id,
            "title": entry["authority"],
            "url": url,
            "when": gap_id,
            "reason": entry["action"],
        })
    fetched = utc_now()
    support = _support(lat, lng, radius_m=None, purpose="", extra="point:source-scout-catalog")
    value = {
        "mode": "constrained_official_followup",
        "discovery": False,
        "followups": followups,
        "material_flags": sorted(flags),
        "anticipated_gaps": list(anticipated_gaps or []),
    }
    atom = _atom(
        candidate_id=candidate_id,
        question_id="source.scout",
        field_id="official_followup_sources",
        value=value,
        source="expedition source-scout catalog",
        source_url=followups[0]["url"] if followups else FEMA_MSC,
        source_family="OFFICIAL_FOLLOWUP",
        independence_group="OFFICIAL_FOLLOWUP",
        support=support,
        fetched_at=fetched,
        dataset_vintage=None,
        transform=SCOUT_TRANSFORM,
        notes=(
            "Constrained official follow-up pack from reviewed authorities. "
            "Not arbitrary web discovery and not a new scoring source."
        ),
        kind="PROXY",
        confidence="medium",
    )
    return [atom], value
