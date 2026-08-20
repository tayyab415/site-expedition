"""Google Places Text Search (New). POTENTIAL POIs, never LISTED.

Uses GOOGLE_PLACES_API_KEY if set, else the challenge Maps key. Places API
(New) is enabled on that key from this VM. Nearby Search by type is retail
junk; this adapter is text queries only. Place IDs may be stored; other
Places content is session-only and is not written to the durable OSM cache.

Docs: https://developers.google.com/maps/documentation/places/web-service/text-search
Policies: https://developers.google.com/maps/documentation/places/web-service/policies
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from expedition.adapters.aerial import maps_key
from expedition.adapters.discover import USER_AGENT, _now
from expedition.discovery.schema import Seed, in_us

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
POLICY = "https://developers.google.com/maps/documentation/places/web-service/policies"
FIELD_MASK = (
    "places.id,places.displayName,places.location,"
    "places.formattedAddress,places.googleMapsUri,places.primaryType"
)
ENV_FILE = Path.home() / ".config" / "mireye-challenge-maps.env"

TEXT_QUERY = {
    # "distribution center" ranks occupied retailer DCs (Macy's, Kroger, Amazon).
    # 3PL / public warehousing is closer to space a tenant could actually use.
    "warehouse": "3PL public warehouse warehousing",
    "custom": "3PL public warehouse warehousing",
    "farm": "farm ranch",
    "data_center": "data center colocation",
}

SKIP_TYPES = frozenset(
    {
        "real_estate_agency",
        "coworking_space",
        "night_club",
        "event_venue",
        "concert_hall",
        "performing_arts_theater",
        "apartment_complex",
        "apartment_building",
        "restaurant",
        "bar",
        "cafe",
        "hotel",
        "lodging",
    }
)
CAPTIVE_MARKERS = (
    "amazon",
    "walmart",
    "target",
    "kroger",
    "heb",
    "cvs",
    "macy",
    "kohl",
    "whole foods",
    "costco",
    "home depot",
    "lowes ",
    "lowe's",
)


def places_key() -> str:
    if os.environ.get("GOOGLE_PLACES_API_KEY"):
        return os.environ["GOOGLE_PLACES_API_KEY"].strip()
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if line.startswith("export "):
                line = line[7:]
            if line.startswith("GOOGLE_PLACES_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return maps_key()


def places_available() -> bool:
    return bool(places_key())


def search_places(
    mission: str,
    lat: float,
    lng: float,
    *,
    radius_m: float = 28000,
    limit: int = 12,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    """Return POTENTIAL place pins. On 403, skip_reason is set and seeds is empty."""
    key = places_key()
    if not key:
        return [], "no Places API key"
    query = TEXT_QUERY.get(mission) or TEXT_QUERY["warehouse"]
    body = {
        "textQuery": query,
        "maxResultCount": min(20, max(1, limit)),
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    try:
        if http_json is not None:
            data = http_json(PLACES_URL, body, key)
        else:
            data = _post(body, key)
    except urllib.error.HTTPError as exc:
        snippet = exc.read().decode(errors="replace")[:240]
        if exc.code == 403:
            return [], f"Places SearchText blocked ({exc.code}). {snippet[:160]}"
        return [], f"Places HTTP {exc.code}"
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return [], f"Places failed ({type(exc).__name__})"

    seeds: list[Seed] = []
    for place in data.get("places") or []:
        loc = place.get("location") or {}
        try:
            plat = float(loc["latitude"])
            plng = float(loc["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_us(plat, plng):
            continue
        place_id = str(place.get("id") or "").split("/")[-1]
        if not place_id:
            continue
        name = ((place.get("displayName") or {}).get("text")) or f"Place {place_id[:8]}"
        primary = place.get("primaryType")
        if primary in SKIP_TYPES:
            continue
        low = name.lower()
        if any(marker in low for marker in CAPTIVE_MARKERS):
            continue
        maps_uri = place.get("googleMapsUri") or f"https://maps.google.com/?q={plat},{plng}"
        seeds.append(
            Seed(
                id=f"places_{place_id}",
                name=str(name),
                lat=plat,
                lng=plng,
                address=place.get("formattedAddress"),
                label="POTENTIAL",
                site_form="existing_asset",
                source="google_places",
                source_url=maps_uri,
                authorization=POLICY,
                family="place",
                role="candidate",
                captured_at=_now(),
                extra={
                    "place_id": place_id,
                    "primary_type": place.get("primaryType"),
                    "attribution": "Google Maps",
                },
            )
        )
        if len(seeds) >= limit:
            break
    return seeds, None


def search_places_hubs(
    mission: str,
    hubs: list[tuple[float, float, int]],
    *,
    limit: int = 12,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    """Text Search at each region hub. Dedupes by place_id. Still POTENTIAL."""
    seen: set[str] = set()
    merged: list[Seed] = []
    last_err: str | None = None
    for lat, lng, radius in hubs[:4]:
        found, err = search_places(
            mission,
            lat,
            lng,
            radius_m=float(radius),
            limit=limit,
            http_json=http_json,
        )
        if err:
            last_err = err
            continue
        for seed in found:
            place_id = str((seed.extra or {}).get("place_id") or seed.id)
            if place_id in seen:
                continue
            seen.add(place_id)
            merged.append(seed)
            if len(merged) >= limit:
                return merged, None
    if merged:
        return merged, None
    return [], last_err or "no Places results"


def _post(body: dict, key: str) -> dict:
    request = urllib.request.Request(
        PLACES_URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": FIELD_MASK,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode())
