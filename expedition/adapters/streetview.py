"""Google Street View Static metadata and images. Presentation only; never scores."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "var" / "cache" / "streetview"
ENV_FILE = Path.home() / ".config" / "mireye-challenge-maps.env"
META_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"


def maps_key() -> str:
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        return os.environ["GOOGLE_MAPS_API_KEY"].strip()
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _cache_path(lat: float, lng: float, cache_dir: Path | None = None, radius: int = 500) -> Path:
    return (cache_dir or CACHE_DIR) / f"{lat:.5f}_{lng:.5f}_r{int(radius)}.json"


def lookup_metadata(lat: float, lng: float, key: str, *, radius: int = 500) -> dict:
    url = META_URL + "?" + urllib.parse.urlencode(
        {
            "location": f"{lat},{lng}",
            "radius": int(radius),
            "source": "outdoor",
            "key": key,
        }
    )
    request = urllib.request.Request(url, headers={"User-Agent": "mireye-expedition-board"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def lookup_image(
    lat: float,
    lng: float,
    heading: float,
    key: str,
    *,
    size: str = "640x640",
    pano_id: str | None = None,
) -> bytes:
    params = {
        "size": size,
        "heading": int(heading) % 360,
        "pitch": 8,
        "fov": 80,
        "source": "outdoor",
        "key": key,
    }
    if pano_id:
        params["pano"] = pano_id
    else:
        params["location"] = f"{lat},{lng}"
    url = IMAGE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "mireye-expedition-board"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def street_meta(lat: float, lng: float, *, cache_dir: Path | None = None, key: str | None = None) -> dict:
    """Return coverage metadata. Does not persist image bytes."""
    radius = 500
    cache_path = _cache_path(lat, lng, cache_dir, radius)
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    api_key = key if key is not None else maps_key()
    if not api_key:
        return {"status": "KEY_MISSING", "available": False, "lat": lat, "lng": lng}
    try:
        raw = lookup_metadata(lat, lng, api_key, radius=radius)
    except urllib.error.HTTPError as exc:
        return {
            "status": "FAILED",
            "available": False,
            "http_status": exc.code,
            "lat": lat,
            "lng": lng,
        }
    except Exception:
        return {"status": "FAILED", "available": False, "lat": lat, "lng": lng}
    location = raw.get("location") or {}
    record = {
        "status": raw.get("status") or "UNKNOWN",
        "available": raw.get("status") == "OK",
        "lat": location.get("lat", lat),
        "lng": location.get("lng", lng),
        "pano_id": raw.get("pano_id"),
        "copyright": raw.get("copyright"),
        "date": raw.get("date"),
        "heading": 70,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(record, indent=2))
    return record
