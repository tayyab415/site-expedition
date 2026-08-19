"""Shared replay helpers for selective Earth Engine / Census witnesses."""

from __future__ import annotations

import json
from pathlib import Path

from expedition.evidence import EvidenceAtom, cache_identity, geometry_hash, utc_now


def safe_id(candidate_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id)


def payload_path(candidate_id: str, root: Path) -> Path:
    return root / f"{safe_id(candidate_id)}.json"


def load_replay(
    candidate_id: str,
    lat: float,
    lng: float,
    cache_dir: Path,
    fixture_dir: Path,
) -> dict | None:
    for path in (payload_path(candidate_id, cache_dir), payload_path(candidate_id, fixture_dir)):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        cached_lat = payload.get("lat")
        cached_lng = payload.get("lng")
        if not isinstance(cached_lat, (int, float)) or not isinstance(cached_lng, (int, float)):
            continue
        if abs(float(cached_lat) - lat) <= 1e-7 and abs(float(cached_lng) - lng) <= 1e-7:
            return payload
    return None


def write_payload(candidate_id: str, cache_dir: Path, payload: dict) -> None:
    path = payload_path(candidate_id, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def support(lat: float, lng: float, *, radius_m: int | None, purpose: str, extra: str) -> dict:
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


def fact_atom(
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
    support_geom: dict,
    observed_at: str | None,
    fetched_at: str,
    dataset_vintage: str | None,
    transform: str,
    live: bool,
    notes: str,
    window: str,
    kind: str = "FACT",
    authority: str = "authoritative",
    confidence: str = "medium",
    decision_effect: str = "INFORM",
) -> EvidenceAtom:
    status = "live" if live else "replay"
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:{status}",
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind=kind,
        status=status,
        decision_effect=decision_effect,
        value=value,
        unit=unit,
        source=source,
        source_url=source_url,
        source_family=source_family,
        independence_group=independence_group,
        authority=authority,
        support=support_geom,
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
            "witness",
            source,
            field_id,
            transform,
            support_geom["geometry_hash"],
            f"{support_geom['kind']}:{support_geom.get('radius_m')}:{support_geom.get('radius_purpose')}",
            window,
        ),
        live_label="live" if live else "replay",
    )


def unknown_atom(
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
    geom = support(lat, lng, radius_m=None, purpose="", extra=field_id)
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
        support=geom,
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
            "witness", source, field_id, transform, geom["geometry_hash"], "point", ""
        ),
        live_label="replay",
    )
