"""Deterministic Mireye /fetch and /fetch/batch. Never /ask for hard gates."""

from __future__ import annotations

import json
import hashlib
import re
import urllib.error
from pathlib import Path

from expedition import credits
from expedition.evidence import atom_from_mireye_field

BASE = "https://api.mireye.com"
CREDS = Path.home() / ".config/mireye-mcp/credentials.json"
CACHE = Path(__file__).resolve().parent.parent / "var" / "cache" / "mireye"
FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "mireye"
GEOCODE_CACHE = Path(__file__).resolve().parent.parent / "var" / "cache" / "geocode"
PARCEL_GRADE = {"rooftop", "nearest_rooftop_match"}


def _partial_failure_field(failure: dict) -> str | None:
    return failure.get("field") or failure.get("field_id") or failure.get("field_name")


def _field_payload(raw: dict, field_id: str) -> tuple[dict, list, bool]:
    """Preserve response- and field-level failures while retaining good values."""
    response_failures = list(raw.get("partial_failures") or [])
    value = (raw.get("fields") or {}).get(field_id)
    field_raw = dict(value) if isinstance(value, dict) else {}
    field_failures = list(field_raw.get("partial_failures") or [])
    matching_failures = [
        failure
        for failure in response_failures
        if isinstance(failure, dict) and _partial_failure_field(failure) == field_id
    ]

    # Response clocks are the fallback for fixtures and response shapes that
    # do not repeat metadata on every successful field.
    for key in ("fetched_at", "ttl", "ttl_seconds"):
        if field_raw.get(key) is None and raw.get(key) is not None:
            field_raw[key] = raw[key]

    if value is None and matching_failures:
        failure = matching_failures[0]
        field_raw.update(
            {
                "status": "failed",
                "error": failure.get("message_public")
                or failure.get("error")
                or "source failed",
                "retryable": bool(failure.get("retryable")),
                "http_status": failure.get("http_status"),
                "source": failure.get("source") or "mireye",
            }
        )

    field_is_partial = bool(field_failures) or (
        value is not None and bool(matching_failures)
    )
    return field_raw, response_failures, field_is_partial


def _token() -> str:
    data = json.loads(CREDS.read_text())
    return data["token"]


def _request(path: str, payload: dict) -> dict:
    import urllib.request

    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def quote_credits(fields: list[str], n_locations: int) -> int:
    """Unmetered quote when the API accepts it; else 1 credit per field/location."""
    try:
        q = _request(
            "/v1/fetch/quote",
            {"fields": fields, "locations": [{"lat": 39.0, "lng": -77.0}] * n_locations},
        )
        for key in ("credits", "total_credits", "estimated_credits"):
            if isinstance(q.get(key), (int, float)):
                return int(q[key])
        if isinstance(q.get("quote"), dict) and "credits" in q["quote"]:
            return int(q["quote"]["credits"])
    except Exception:
        pass
    return len(fields) * n_locations


def _address_cache_path(address: str, cache_dir: Path | None = None) -> Path:
    normalized = " ".join(address.casefold().split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return (cache_dir or GEOCODE_CACHE) / f"{digest}.json"


def _looks_like_full_us_address(address: str) -> bool:
    if not 1 <= len(address) <= 256:
        return False
    has_street_number = bool(re.search(r"\b\d+[A-Za-z-]*\b", address))
    has_state = bool(re.search(r",\s*[A-Z]{2}(?:\s+\d{5}(?:-\d{4})?)?\s*$", address, re.I))
    return has_street_number and has_state


def resolve_address(
    address: str,
    *,
    live: bool,
    expedition_spent: int = 0,
    cache_dir: Path | None = None,
) -> tuple[dict, int]:
    """Resolve once. Ambiguous/imprecise results never silently become a pin."""
    address = " ".join((address or "").split())
    if not _looks_like_full_us_address(address):
        return {
            "disposition": "clarify",
            "message": "Enter a complete US street address with state; no location was selected.",
            "candidates": [],
        }, 0

    cache_path = _address_cache_path(address, cache_dir)
    spent = 0
    if cache_path.exists():
        raw = json.loads(cache_path.read_text())
        # A successful Mireye address resolve is cached for 30 days. Reuse the
        # local copy instead of sending the retained address again.
        if raw.get("error") and not live:
            pass
    elif not live:
        raise FileNotFoundError("address has no cached resolve; turn on Live to resolve it")
    else:
        # /v1/geocode is a documented fixed one-credit operation. This is the
        # quote used for the ledger before the metered call.
        estimate = 1
        credits.authorize(
            estimate,
            reason="mireye geocode Check-a-Site address",
            expedition_spent=expedition_spent,
        )
        spent = estimate
        try:
            raw = _request("/v1/geocode", {"address": address})
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode())
            except Exception:
                body = {}
            raw = {
                "error": body.get("error") or "geocode_failed",
                "message": body.get("message") or "Address could not be resolved.",
                "http_status": exc.code,
            }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(raw, indent=2))

    if raw.get("error"):
        reason = raw.get("error")
        disposition = "clarify" if reason in {"address_too_coarse", "address_form_unsupported"} else "no_match"
        return {
            "disposition": disposition,
            "reason": reason,
            "message": raw.get("message") or "Address could not be resolved.",
            "candidates": [],
            "retention_note": "Live address resolves are retained by Mireye for about 30 days.",
        }, spent

    lat = raw.get("lat")
    lng = raw.get("lng")
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return {
            "disposition": "no_match",
            "reason": "missing_coordinate",
            "message": "The resolver returned no usable coordinate.",
        }, spent
    if not (18 <= lat <= 72 and -180 <= lng <= -65):
        return {
            "disposition": "no_match",
            "reason": "outside_us_envelope",
            "message": "The resolved point is outside the US Mireye envelope.",
        }, spent

    accuracy_type = str(raw.get("accuracy_type") or "unknown").lower()
    parcel_grade = bool(raw.get("parcel_grade")) or accuracy_type in PARCEL_GRADE
    resolved = {
        "lat": lat,
        "lng": lng,
        "normalized_address": raw.get("normalized_address") or address,
        "accuracy": raw.get("accuracy"),
        "accuracy_type": accuracy_type,
        "parcel_grade": parcel_grade,
        "match_type": raw.get("match_type"),
        "provider": raw.get("provider"),
        "source": raw.get("source"),
    }
    if not parcel_grade:
        return {
            "disposition": "clarify",
            "message": (
                f"Resolver returned {accuracy_type}, not rooftop accuracy. "
                "Confirm the shown location before screening."
            ),
            "candidates": [resolved],
            "retention_note": "Live address resolves are retained by Mireye for about 30 days.",
        }, spent
    return {
        "disposition": "resolved",
        **resolved,
        "retention_note": "Live address resolves are retained by Mireye for about 30 days.",
    }, spent


def fetch_fields(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    fields: list[str],
    live: bool,
    question_id: str,
    effects: dict[str, tuple[str, str, str]],
    expedition_spent: int,
    now=None,
) -> tuple[list, int, dict]:
    """Return (atoms, credits_spent, raw). effects[field] = (kind, effect, authority)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / f"{candidate_id}.json"
    fixture_path = FIXTURES / f"{candidate_id}.json"
    raw = None
    used_live = False
    spent = 0
    if not live and cache_path.exists():
        raw = json.loads(cache_path.read_text())
    elif not live and fixture_path.exists():
        raw = json.loads(fixture_path.read_text())
    elif live:
        estimate = quote_credits(fields, 1)
        credits.authorize(
            estimate,
            reason=f"mireye fetch {candidate_id} {len(fields)}f",
            expedition_spent=expedition_spent,
        )
        raw = _request("/v1/fetch", {"lat": lat, "lng": lng, "fields": fields})
        cache_path.write_text(json.dumps(raw, indent=2))
        used_live = True
        spent = estimate
    else:
        raise FileNotFoundError(f"no Mireye cache for {candidate_id}; pass live=True")

    atoms = []
    per = (spent / max(len(fields), 1)) if spent else 0
    for field_id in fields:
        kind, effect, authority = effects.get(
            field_id, ("FACT", "INFORM", "authoritative")
        )
        field_raw, response_failures, field_is_partial = _field_payload(
            raw, field_id
        )
        atoms.append(
            atom_from_mireye_field(
                candidate_id=candidate_id,
                question_id=question_id,
                field_id=field_id,
                raw=field_raw,
                lat=lat,
                lng=lng,
                live=used_live,
                effect=effect,
                kind=kind,
                authority=authority,
                credits=per,
                partial_failures=response_failures,
                field_is_partial=field_is_partial,
                now=now,
            )
        )
    return atoms, spent, raw
