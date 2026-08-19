"""EPA ECHO/FRS drill-down after a Mireye environmental proximity hit.

The connector deliberately does not perform a broad environmental search.  It
is activated only after Mireye reports a nearby RMP facility, then attaches the
named federal facility record.  Both atoms remain in the same EPA independence
group: the direct record refines the proximity lead; it is not corroboration
and it is never a clean-site certification.
"""

from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from expedition.evidence import (
    EvidenceAtom,
    cache_identity,
    cache_runtime_status,
    geometry_hash,
    utc_now,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures" / "epa"
CACHE = ROOT / "var" / "cache" / "epa"
BASE = "https://echodata.epa.gov/echo"
SOURCE_PAGE = "https://echo.epa.gov/tools/web-services/facility-search-all-data"
TTL = "P30D"
TRANSFORM_VERSION = "epa-echo-rmp-v1"
QCOLUMNS = "1,2,3,4,5,6,15,16,17,18,23,24,36,37,38,39,41,43,54,55,60,61,62,95,137"


def _request_json(endpoint: str, params: dict[str, Any]) -> dict:
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "site-expedition/1.0 EPA-ECHO-drilldown",
        },
    )
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read())
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code != 429:
                raise
            if attempt == 0:
                time.sleep(0.25)
    assert last_error is not None
    raise last_error


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6_371_008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    value = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(value))


def _as_int(value: Any) -> int | None:
    try:
        return int(str(value).replace(",", "")) if value not in (None, "") else None
    except ValueError:
        return None


def _fetch_live(lat: float, lng: float, radius_m: float) -> dict:
    radius_miles = min(100.0, max(0.25, radius_m / 1609.344 + 0.5))
    search = _request_json(
        "echo_rest_services.get_facilities",
        {
            "output": "JSON",
            "p_lat": round(lat, 7),
            "p_long": round(lng, 7),
            "p_radius": round(radius_miles, 3),
            "p_med": "M",
            "responseset": 25,
        },
    ).get("Results") or {}
    if search.get("Message") != "Success" or not search.get("QueryID"):
        raise RuntimeError("EPA ECHO facility search did not return a query identifier")
    page = _request_json(
        "echo_rest_services.get_qid",
        {
            "output": "JSON",
            "qid": search["QueryID"],
            "pageno": 1,
            "qcolumns": QCOLUMNS,
        },
    ).get("Results") or {}
    rows = page.get("Facilities") or []
    if isinstance(rows, dict):
        rows = [rows]
    candidates = []
    for row in rows:
        if not row.get("RmpIDs"):
            continue
        try:
            facility_lat = float(row["FacLat"])
            facility_lng = float(row["FacLong"])
        except (KeyError, TypeError, ValueError):
            continue
        distance_m = _haversine_m(lat, lng, facility_lat, facility_lng)
        candidates.append((distance_m, row, facility_lat, facility_lng))
    candidates.sort(key=lambda item: (item[0], str(item[1].get("RegistryID") or "")))
    facility = None
    if candidates:
        distance_m, row, facility_lat, facility_lng = candidates[0]
        registry_id = str(row.get("RegistryID") or "").strip()
        dfr_url = (
            f"https://echo.epa.gov/detailed-facility-report?fid={urllib.parse.quote(registry_id)}"
            if registry_id
            else SOURCE_PAGE
        )
        facility = {
            "registry_id": registry_id or None,
            "name": row.get("FacName"),
            "address": ", ".join(
                value
                for value in (
                    row.get("FacStreet"),
                    row.get("FacCity"),
                    row.get("FacState"),
                    row.get("FacZip"),
                )
                if value
            ),
            "lat": facility_lat,
            "lng": facility_lng,
            "distance_m": round(distance_m, 1),
            "rmp_ids": [value.strip() for value in str(row.get("RmpIDs") or "").split() if value.strip()],
            "sems_ids": [value.strip() for value in str(row.get("SemsIDs") or "").split() if value.strip()],
            "sic_codes": row.get("FacSICCodes"),
            "naics_codes": row.get("FacNAICSCodes"),
            "active_flag": row.get("FacActiveFlag"),
            "compliance_status": row.get("FacComplianceStatus"),
            "air_compliance_status": row.get("CAAComplianceStatus"),
            "water_compliance_status": row.get("CWAComplianceStatus"),
            "rcra_compliance_status": row.get("RCRAComplianceStatus"),
            "inspection_count": _as_int(row.get("FacInspectionCount")),
            "last_inspection": row.get("FacDateLastInspection"),
            "formal_action_count": _as_int(row.get("FacFormalActionCount")),
            "last_formal_action": row.get("FacDateLastFormalAction"),
            "total_penalties": row.get("FacTotalPenalties"),
            "penalty_count": _as_int(row.get("FacPenaltyCount")),
            "last_penalty": row.get("FacDateLastPenalty"),
            "source_url": dfr_url,
        }
    return {
        "fetched_at": utc_now(),
        "service_version": search.get("Version"),
        "query_rows": _as_int(search.get("QueryRows")) or 0,
        "query": {
            "program": "RMP",
            "radius_m": round(radius_miles * 1609.344, 1),
            "lat": round(lat, 7),
            "lng": round(lng, 7),
        },
        "facility": facility,
        "limitations": [
            "ECHO is a lagged regulatory snapshot and completeness varies by program and state.",
            "A nearby RMP record is a due-diligence lead, not a clean-site or hazard conclusion.",
        ],
    }


def _support(lat: float, lng: float, radius_m: float) -> dict:
    return {
        "kind": "buffer",
        "crs": "EPSG:4326",
        "lat": lat,
        "lng": lng,
        "radius_m": round(radius_m, 1),
        "radius_purpose": "EPA ECHO RMP facility record drill-down after Mireye proximity hit",
        "parcel_id": None,
        "parcel_grade": False,
        "match_type": "nearest_rmp_facility_in_echo_radius",
        "match_distance_m": None,
        "boundary_source": "EPA ECHO / Facility Registry Service",
        "boundary_version": None,
        "huc": None,
        "geometry_hash": geometry_hash(lat, lng, f"epa-rmp:{radius_m:.1f}"),
    }


def _failure_atom(
    candidate_id: str,
    lat: float,
    lng: float,
    radius_m: float,
    exc: Exception,
) -> EvidenceAtom:
    http_status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
    failure_class = (
        "auth"
        if http_status in {401, 403}
        else "quota"
        if http_status == 429
        else "timeout"
        if isinstance(exc, TimeoutError)
        else "unsupported"
        if isinstance(exc, FileNotFoundError)
        else "other"
    )
    fetched_at = utc_now()
    support = _support(lat, lng, radius_m)
    message = (
        "No replay EPA ECHO record exists for this Candidate Site."
        if isinstance(exc, FileNotFoundError)
        else "EPA ECHO facility drill-down failed."
    )
    return EvidenceAtom(
        atom_id=f"{candidate_id}:environmental.record:epa_rmp_facility_record",
        candidate_id=candidate_id,
        question_id="environmental.record",
        field_id="epa_rmp_facility_record",
        kind="FAILED",
        status="failed",
        decision_effect="INFORM",
        value=None,
        unit=None,
        source="EPA ECHO / Facility Registry Service",
        source_url=SOURCE_PAGE,
        source_family="EPA_ECHO",
        independence_group="EPA",
        authority="none",
        support=support,
        observed_at=None,
        fetched_at=fetched_at,
        dataset_vintage=None,
        ttl=TTL,
        confidence=None,
        notes="Direct record drill-down; never a clean-site certification.",
        failure={
            "class": failure_class,
            "http_status": http_status,
            "retryable": failure_class in {"timeout", "quota", "other"},
            "message_public": message,
        },
        cost={"credits": 0, "tokens": 0, "unit": "public_api_call"},
        citation={
            "source": "EPA ECHO / Facility Registry Service",
            "source_url": SOURCE_PAGE,
            "fetched_at": fetched_at,
            "dataset_vintage": None,
        },
        transform_version=TRANSFORM_VERSION,
        cache_identity=cache_identity(
            "epa_echo",
            "ECHO_RMP",
            "epa_rmp_facility_record",
            TRANSFORM_VERSION,
            support["geometry_hash"],
            f"buffer:{radius_m:.1f}:rmp_drilldown",
        ),
        live_label="replay",
    )


def _atom_from_payload(
    candidate_id: str,
    lat: float,
    lng: float,
    radius_m: float,
    payload: dict,
    *,
    live: bool,
) -> EvidenceAtom:
    fetched_at = payload.get("fetched_at") or utc_now()
    facility = payload.get("facility")
    support = _support(lat, lng, radius_m)
    if facility and facility.get("distance_m") is not None:
        support["match_distance_m"] = facility["distance_m"]
    status = "live" if live else cache_runtime_status(fetched_at, TTL)
    kind = "FACT" if facility else "ABSENT"
    if not facility:
        status = "absent"
    source_url = (facility or {}).get("source_url") or SOURCE_PAGE
    notes = " ".join(payload.get("limitations") or [])
    return EvidenceAtom(
        atom_id=f"{candidate_id}:environmental.record:epa_rmp_facility_record",
        candidate_id=candidate_id,
        question_id="environmental.record",
        field_id="epa_rmp_facility_record",
        kind=kind,
        status=status,
        decision_effect="INFORM",
        value=(
            {
                "program": "RMP",
                "query_rows": payload.get("query_rows"),
                "facility": facility,
            }
            if facility
            else None
        ),
        unit=None,
        source="EPA ECHO / Facility Registry Service",
        source_url=source_url,
        source_family="EPA_ECHO",
        independence_group="EPA",
        authority="authoritative",
        support=support,
        observed_at=None,
        fetched_at=fetched_at,
        dataset_vintage=payload.get("service_version"),
        ttl=TTL,
        confidence=None,
        notes=notes,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": "public_api_call"},
        citation={
            "source": "EPA ECHO / Facility Registry Service",
            "source_url": source_url,
            "fetched_at": fetched_at,
            "dataset_vintage": payload.get("service_version"),
        },
        transform_version=TRANSFORM_VERSION,
        cache_identity=cache_identity(
            "epa_echo",
            payload.get("service_version") or "ECHO_RMP",
            "epa_rmp_facility_record",
            TRANSFORM_VERSION,
            support["geometry_hash"],
            f"buffer:{radius_m:.1f}:rmp_drilldown",
        ),
        live_label="live" if live else "replay",
        license="US Government public record; preserve EPA source and limitations.",
    )


def rmp_record(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    hit_distance_m: float,
    live: bool,
) -> tuple[list[EvidenceAtom], dict]:
    """Return one direct EPA RMP facility-record atom and its normalized payload."""
    radius_m = max(402.3, min(160_934.4, float(hit_distance_m) + 804.7))
    cache_path = CACHE / f"{candidate_id}.json"
    fixture_path = FIXTURES / f"{candidate_id}.json"
    try:
        if live:
            payload = _fetch_live(lat, lng, radius_m)
            CACHE.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload, indent=2) + "\n")
            used_live = True
        elif cache_path.exists():
            payload = json.loads(cache_path.read_text())
            used_live = False
        elif fixture_path.exists():
            payload = json.loads(fixture_path.read_text())
            used_live = False
        else:
            raise FileNotFoundError(candidate_id)
        return [
            _atom_from_payload(
                candidate_id,
                lat,
                lng,
                radius_m,
                payload,
                live=used_live,
            )
        ], payload
    except Exception as exc:
        return [_failure_atom(candidate_id, lat, lng, radius_m, exc)], {}
