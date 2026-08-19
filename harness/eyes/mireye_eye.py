"""Mireye eye — the cited record for a point.

Cache-first: reads cache/mireye/<slug>.json unless live=True.
Live calls spend credits (156 left until promo codes) — never call live
unless explicitly asked.
"""
import json
from pathlib import Path

CACHE = Path(__file__).parent.parent / "cache" / "mireye"

FIELDS = [
    "fema_flood_zone", "intersects_wetland",
    "surface_water_permanence_pct", "coast_distance_m",
]


def fetch(slug: str, lat: float, lng: float, live: bool = False) -> dict:
    cached = CACHE / f"{slug}.json"
    if cached.exists() and not live:
        return json.loads(cached.read_text())
    if not live:
        raise SystemExit(
            f"no cached Mireye record for '{slug}' — rerun with --live to spend credits"
        )
    import requests
    creds = json.loads(
        (Path.home() / ".config/mireye-mcp/credentials.json").read_text()
    )
    resp = requests.post(
        "https://api.mireye.com/v1/fetch",
        headers={
            "Authorization": f"Bearer {creds['token']}",
            "content-type": "application/json",
        },
        json={"lat": lat, "lng": lng, "preset": "terrain", "fields": FIELDS},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(data, indent=2))
    return data


def record(slug: str, lat: float, lng: float, live: bool = False) -> dict:
    """The vetting-relevant view of the cited record."""
    raw = fetch(slug, lat, lng, live)
    f = raw["fields"]

    def field(name):
        v = f.get(name) or {}
        return {
            "value": v.get("value"),
            "unit": v.get("unit"),
            "source": v.get("source"),
            "source_url": v.get("source_url"),
            "confidence": v.get("confidence"),
            "vintage": v.get("dataset_vintage"),
            "fetched_at": v.get("fetched_at"),
        }

    return {
        "elevation_m": field("elevation"),
        "fema_flood_zone": field("fema_flood_zone"),
        "intersects_wetland": field("intersects_wetland"),
        "surface_water_permanence_pct": field("surface_water_permanence_pct"),
        "coast_distance_m": field("coast_distance_m"),
        "soil_drainage_class": field("soil_drainage_class"),
        "fetched_at": raw.get("fetched_at"),
    }
