"""Google Routes via ADC. Never the restricted Maps API key."""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

from expedition.evidence import EvidenceAtom, cache_identity, geometry_hash, utc_now

PROJECT = "gen-lang-client-0261050164"
URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "var" / "cache" / "routes"


def _adc_token() -> str:
    return subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
    ).strip()


def route_matrix(origin: dict, destination: dict) -> dict:
    body = json.dumps(
        {
            "origins": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": origin["lat"],
                                "longitude": origin["lng"],
                            }
                        }
                    }
                }
            ],
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": destination["lat"],
                                "longitude": destination["lng"],
                            }
                        }
                    }
                }
            ],
            "travelMode": "DRIVE",
        }
    ).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {_adc_token()}",
            "Content-Type": "application/json",
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status",
            "X-Goog-User-Project": PROJECT,
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode())
    row = data[0] if isinstance(data, list) else data
    dur = row.get("duration") or "0s"
    seconds = int(str(dur).rstrip("s") or 0)
    return {
        "duration_s": seconds,
        "distance_m": row.get("distanceMeters"),
        "status": row.get("status") or {},
    }


def _cache_path(candidate_id: str, dest: dict, cache_dir: Path | None = None) -> Path:
    anchor_id = str(dest.get("id") or f"{dest['lat']}_{dest['lng']}")
    safe_candidate = "".join(c if c.isalnum() or c in "-_" else "_" for c in candidate_id)
    safe_anchor = "".join(c if c.isalnum() or c in "-_" else "_" for c in anchor_id)
    return (cache_dir or CACHE_DIR) / f"{safe_candidate}__{safe_anchor}.json"


def route_atom(
    candidate_id: str,
    origin: dict,
    dest: dict,
    live: bool,
    *,
    cache_dir: Path | None = None,
) -> EvidenceAtom:
    fetched = utc_now()
    cache_path = _cache_path(candidate_id, dest, cache_dir)
    anchor_id = str(dest.get("id") or f"{dest['lat']},{dest['lng']}")
    anchor_name = str(dest.get("name") or anchor_id)
    try:
        if live:
            result = route_matrix(origin, dest)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(
                    {
                        "candidate_id": candidate_id,
                        "origin": {"lat": origin["lat"], "lng": origin["lng"]},
                        "destination": dest,
                        "result": result,
                        "fetched_at": fetched,
                    },
                    indent=2,
                )
            )
        else:
            cached = json.loads(cache_path.read_text())
            result = cached["result"]
            fetched = cached.get("fetched_at") or fetched
        if not isinstance(result.get("duration_s"), (int, float)) or result["duration_s"] <= 0:
            raise RuntimeError("route_duration_missing")
        kind, status, effect, value, failure = (
            "FACT",
            "live" if live else "replay",
            "INFORM",
            int(result["duration_s"]),
            None,
        )
    except Exception as exc:
        kind, status, effect, value = "UNKNOWN", "blocked" if "403" in str(exc) else "failed", "UNKNOWN", None
        failure = {
            "class": "auth" if "403" in str(exc) else "cache" if not live else "other",
            "http_status": 403 if "403" in str(exc) else None,
            "retryable": bool(live),
            "message_public": "route time unavailable; run live once to populate replay" if not live else "route time unavailable",
        }
        result = {}
    geom = geometry_hash(origin["lat"], origin["lng"], f"to:{dest['lat']},{dest['lng']}")
    return EvidenceAtom(
        atom_id=f"{candidate_id}:route:{anchor_id}:{status}",
        candidate_id=candidate_id,
        question_id=f"logistics.route_time.{anchor_id}",
        field_id="route_duration_s",
        kind=kind,
        status=status if status in {"live", "replay", "blocked", "failed"} else "failed",
        decision_effect=effect,
        value=value,
        unit="seconds",
        source="GOOGLE_ROUTES",
        source_url="https://developers.google.com/maps/documentation/routes/compute-route-matrix",
        source_family="GOOGLE_ROUTES",
        independence_group="GOOGLE_ROUTES",
        authority="authoritative" if kind == "FACT" else "none",
        support={
            "kind": "network",
            "crs": "EPSG:4326",
            "lat": origin["lat"],
            "lng": origin["lng"],
            "destination_id": anchor_id,
            "destination_name": anchor_name,
            "destination_lat": dest["lat"],
            "destination_lng": dest["lng"],
            "geometry_hash": geom,
        },
        observed_at=fetched if kind == "FACT" else None,
        fetched_at=fetched,
        dataset_vintage=None,
        ttl=None,
        confidence="high" if kind == "FACT" else None,
        notes=(
            f"Road-network time to {anchor_name}"
            + (f"; {result.get('distance_m')} m" if result.get("distance_m") else "")
            + ". Not truck ingress, legal truck route, or driveway."
        ),
        failure=failure,
        cost={"credits": 0, "tokens": 0, "unit": "routes_element"},
        citation={
            "source": "GOOGLE_ROUTES",
            "source_url": "https://developers.google.com/maps/documentation/routes/compute-route-matrix",
            "fetched_at": fetched,
            "dataset_vintage": None,
        },
        transform_version="routes-adc-v1",
        cache_identity=cache_identity(
            "google-routes", "v2", "route_duration_s", "routes-adc-v1", geom, "network", ""
        ),
        live_label="live" if status == "live" else "replay",
    )
