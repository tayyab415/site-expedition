"""Google Aerial View metadata. Presentation only; never enters scoring."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from expedition.evidence import EvidenceAtom, cache_identity, geometry_hash, utc_now

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "var" / "cache" / "aerial"
ENV_FILE = Path.home() / ".config" / "mireye-challenge-maps.env"
METADATA_URL = "https://aerialview.googleapis.com/v1/videos:lookupVideoMetadata"
VIDEO_URL = "https://aerialview.googleapis.com/v1/videos:lookupVideo"


def maps_key() -> str:
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        return os.environ["GOOGLE_MAPS_API_KEY"].strip()
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if line.startswith("export "):
                line = line[7:]
            if line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def lookup_metadata(query: str, key: str) -> dict:
    url = METADATA_URL + "?" + urllib.parse.urlencode({"address": query, "key": key})
    request = urllib.request.Request(url, headers={"User-Agent": "mireye-expedition-board"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode())


def lookup_playback(video_id: str, key: str) -> dict:
    url = VIDEO_URL + "?" + urllib.parse.urlencode({"videoId": video_id, "key": key})
    request = urllib.request.Request(url, headers={"User-Agent": "mireye-expedition-board"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode())


def playback_uri(playback: dict) -> str | None:
    """Return a playable HTTPS URI. Google nests landscapeUri under each format."""
    uris = playback.get("uris") or playback.get("videoUris") or {}
    if not isinstance(uris, dict):
        return None
    for key in ("MP4_HIGH", "MP4_MEDIUM", "MP4_LOW", "HLS"):
        value = uris.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
        if isinstance(value, dict):
            for inner in ("landscapeUri", "portraitUri", "uri", "url", "value"):
                candidate = value.get(inner)
                if isinstance(candidate, str) and candidate.startswith("http"):
                    return candidate
    return None


def _cache_path(candidate_id: str, cache_dir: Path | None = None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id)
    return (cache_dir or CACHE_DIR) / f"{safe}.json"


def _presentation_atom(
    candidate_id: str,
    site: dict,
    *,
    field_id: str,
    value,
    status: str,
    fetched_at: str,
    notes: str,
) -> EvidenceAtom:
    geom = geometry_hash(site["lat"], site["lng"])
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:{status}",
        candidate_id=candidate_id,
        question_id="presentation.today_scene",
        field_id=field_id,
        kind="PRESENTATION",
        status=status,
        decision_effect="NONE",
        value=value,
        unit=None,
        source="GOOGLE_AERIAL_VIEW" if field_id == "aerial_video_id" else "GOOGLE_PHOTOREALISTIC_3D",
        source_url=(
            "https://developers.google.com/maps/documentation/aerial-view/overview"
            if field_id == "aerial_video_id"
            else "https://developers.google.com/maps/documentation/tile/3d-tiles-overview"
        ),
        source_family="GOOGLE_VISUAL",
        independence_group="GOOGLE_VISUAL",
        authority="presentation",
        support={
            "kind": "point",
            "crs": "EPSG:4326",
            "lat": site["lat"],
            "lng": site["lng"],
            "geometry_hash": geom,
        },
        observed_at=None,
        fetched_at=fetched_at,
        dataset_vintage=None,
        ttl=None,
        confidence=None,
        notes=notes,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": "presentation_lookup"},
        citation={
            "source": "GOOGLE_VISUAL",
            "source_url": "https://developers.google.com/maps/documentation/aerial-view/overview",
            "fetched_at": fetched_at,
            "dataset_vintage": None,
        },
        transform_version="google-visual-v1",
        cache_identity=cache_identity(
            "google-visual", "v1", field_id, "google-visual-v1", geom, "point", ""
        ),
        live_label="live" if status == "live" else "replay",
    )


def _failed_aerial_atom(
    candidate_id: str,
    site: dict,
    *,
    fetched_at: str,
    failure_class: str,
    http_status: int | None,
    message: str,
) -> EvidenceAtom:
    geom = geometry_hash(site["lat"], site["lng"])
    return EvidenceAtom(
        atom_id=f"{candidate_id}:aerial_video_id:failed",
        candidate_id=candidate_id,
        question_id="presentation.today_scene",
        field_id="aerial_video_id",
        kind="FAILED",
        status="failed",
        decision_effect="NONE",
        value=None,
        unit=None,
        source="GOOGLE_AERIAL_VIEW",
        source_url="https://developers.google.com/maps/documentation/aerial-view/overview",
        source_family="GOOGLE_VISUAL",
        independence_group="GOOGLE_VISUAL",
        authority="presentation",
        support={
            "kind": "point",
            "crs": "EPSG:4326",
            "lat": site["lat"],
            "lng": site["lng"],
            "geometry_hash": geom,
        },
        observed_at=None,
        fetched_at=fetched_at,
        dataset_vintage=None,
        ttl=None,
        confidence=None,
        notes=message,
        failure={
            "class": failure_class,
            "http_status": http_status,
            "retryable": failure_class not in {"no_coverage", "auth"},
            "message_public": message,
        },
        cost={"credits": 0, "tokens": 0, "unit": "presentation_lookup"},
        citation={
            "source": "GOOGLE_AERIAL_VIEW",
            "source_url": "https://developers.google.com/maps/documentation/aerial-view/overview",
            "fetched_at": fetched_at,
            "dataset_vintage": None,
        },
        transform_version="aerial-metadata-v1",
        cache_identity=cache_identity(
            "google-aerial", "v1", "aerial_video_id", "aerial-metadata-v1", geom, "point", ""
        ),
        live_label="replay",
    )


def aerial_atoms(
    candidate_id: str,
    site: dict,
    live: bool,
    *,
    cache_dir: Path | None = None,
    key: str | None = None,
) -> tuple[list[EvidenceAtom], dict]:
    """Return Aerial metadata plus a 3D fallback when no ACTIVE orbit exists."""
    cache_path = _cache_path(candidate_id, cache_dir)
    fetched_at = utc_now()
    query = site.get("address") or f"{site['lat']:.7f},{site['lng']:.7f}"
    record: dict
    if live:
        try:
            api_key = key if key is not None else maps_key()
            if not api_key:
                raise RuntimeError("maps_key_missing")
            raw = lookup_metadata(query, api_key)
            state = str(raw.get("state") or "").upper()
            video_id = raw.get("videoId")
            record = {
                "state": state,
                "video_id": video_id if state == "ACTIVE" else None,
                "http_status": 200,
                "query": query,
                "fetched_at": fetched_at,
            }
        except urllib.error.HTTPError as exc:
            record = {
                "state": "NOT_FOUND" if exc.code == 404 else "FAILED",
                "video_id": None,
                "http_status": exc.code,
                "query": query,
                "fetched_at": fetched_at,
            }
        except Exception as exc:
            record = {
                "state": "BLOCKED" if "key" in str(exc).lower() else "FAILED",
                "video_id": None,
                "http_status": None,
                "query": query,
                "fetched_at": fetched_at,
            }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Persist metadata only. Signed playback URLs and bytes never enter this cache.
        cache_path.write_text(json.dumps(record, indent=2))
    elif cache_path.exists():
        record = json.loads(cache_path.read_text())
        fetched_at = record.get("fetched_at") or fetched_at
    else:
        record = {
            "state": "REPLAY_MISS",
            "video_id": None,
            "http_status": None,
            "query": query,
            "fetched_at": fetched_at,
        }

    state = str(record.get("state") or "").upper()
    if state == "ACTIVE" and record.get("video_id"):
        atom = _presentation_atom(
            candidate_id,
            site,
            field_id="aerial_video_id",
            value=record["video_id"],
            status="live" if live else "replay",
            fetched_at=fetched_at,
            notes="ACTIVE Aerial View orbit. Playback URLs are fetched ephemerally and not stored.",
        )
        return [atom], {"state": "ACTIVE", "video_id": record["video_id"]}

    no_coverage = state == "NOT_FOUND" or record.get("http_status") == 404
    message = (
        "no Aerial orbit at this pin (404); using TODAY photorealistic 3D"
        if no_coverage
        else "Aerial lookup unavailable in replay; using TODAY photorealistic 3D"
    )
    failed = _failed_aerial_atom(
        candidate_id,
        site,
        fetched_at=fetched_at,
        failure_class="no_coverage" if no_coverage else "auth" if state == "BLOCKED" else "other",
        http_status=record.get("http_status"),
        message=message,
    )
    fallback = _presentation_atom(
        candidate_id,
        site,
        field_id="maps_3d_scene",
        value="photorealistic_3d_fallback",
        status="live" if live else "replay",
        fetched_at=fetched_at,
        notes=message,
    )
    return [failed, fallback], {
        "state": "NOT_FOUND" if no_coverage else "UNAVAILABLE",
        "video_id": None,
        "note": message,
        "http_status": record.get("http_status"),
    }
