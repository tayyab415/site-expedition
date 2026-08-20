"""Find-a-Site candidate search from public map data.

This is not a listing feed. Results are POTENTIAL pins from OpenStreetMap
(buildings, farms, industrial sites). Google Places is enabled on the GCP
project but blocked on the Maps key we have, so OSM is the live search.
Consumer-marketplace scraping stays out.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "var" / "cache" / "discover"
FIXTURE_DIR = ROOT / "data" / "fixtures" / "discover"

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
USER_AGENT = "mireye-expedition/0.1 (site-selection; OSM attribution)"
OSM_TERMS = "https://www.openstreetmap.org/copyright"
MAX_RESULTS = 16
DEDUP_DEG = 0.0012  # ~130 m
# The board aborts /api/discover at 18 s. Both mirrors together must answer
# or fail inside that, so each request gets a slice of one shared deadline.
OVERPASS_SERVER_TIMEOUT = 12
OVERPASS_TOTAL_BUDGET = 15.0

REGION_HUBS: dict[str, tuple[tuple[float, float, int], ...]] = {
    "texas_triangle": (
        (29.7589, -95.3677, 28000),
        (30.2711, -97.7437, 22000),
        (32.7767, -96.7970, 28000),
    ),
    "houston_metro": ((29.7589, -95.3677, 36000),),
    "austin_san_antonio": (
        (30.2711, -97.7437, 24000),
        (29.4241, -98.4936, 24000),
    ),
    "dallas_fort_worth": ((32.7767, -96.7970, 36000),),
    "chicago": ((41.8756, -87.6244, 28000),),
    "atlanta": ((33.7488, -84.3883, 28000),),
    "phoenix": ((33.4484, -112.0740, 28000),),
    "denver": ((39.7392, -104.9903, 24000),),
    "seattle": ((47.6062, -122.3321, 24000),),
    "los_angeles": ((34.0522, -118.2437, 28000),),
    "new_york": ((40.7128, -74.0060, 22000),),
    "miami": ((25.7617, -80.1918, 24000),),
}

MISSION_FILTERS = {
    "warehouse": (
        'nwr["building"="warehouse"]',
        'nwr["industrial"="warehouse"]',
        'nwr["building"="industrial"]',
    ),
    "custom": (
        'nwr["building"="warehouse"]',
        'nwr["industrial"="warehouse"]',
        'nwr["building"="industrial"]',
    ),
    # landuse=farmland with a name is dropped on purpose: measured 14 s for
    # 5 hits on overpass-api.de, which alone blows the query budget.
    "farm": (
        'nwr["building"="farm"]',
        'nwr["landuse"="farmyard"]',
        'nwr["landuse"="greenhouse_horticulture"]',
    ),
    "home": (
        'nwr["building"="house"]["addr:housenumber"]',
        'nwr["building"="detached"]["addr:housenumber"]',
        'nwr["building"="residential"]["addr:housenumber"]',
    ),
    # The name-regex clause (name~"data.?center") is dropped: a regex scan
    # over every named feature in the radius blows the query budget.
    "data_center": (
        'nwr["telecom"="data_center"]',
        'nwr["building"="data_center"]',
    ),
}


class DiscoverError(RuntimeError):
    """Raised when a look-query cannot be placed in the US envelope."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _cache_key(mission: str, search_region: str, look_query: str) -> str:
    raw = f"{mission}|{search_region}|{look_query.strip().lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _http_json(url: str, *, data: bytes | None = None, timeout: int = 20) -> dict | list:
    request = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def geocode_look(query: str) -> dict:
    """Place a US city/metro with Nominatim. Not a Mireye geocode and not a listing."""
    text = query.strip()
    if not text:
        raise DiscoverError("city or metro is empty")
    if len(text) > 120:
        raise DiscoverError("city or metro is too long")
    url = NOMINATIM + "?" + urllib.parse.urlencode(
        {
            "q": text,
            "format": "json",
            "limit": 1,
            "countrycodes": "us",
            "addressdetails": 1,
        }
    )
    rows = _http_json(url, timeout=15)
    if not isinstance(rows, list) or not rows:
        raise DiscoverError(f"could not place {text} in the US")
    row = rows[0]
    lat = float(row["lat"])
    lng = float(row["lon"])
    if lat < 18 or lat > 72 or lng < -180 or lng > -65:
        raise DiscoverError(f"{text} is outside the US envelope")
    return {
        "lat": lat,
        "lng": lng,
        "name": row.get("display_name") or text,
        "query": text,
        "source": "nominatim",
        "source_url": "https://nominatim.openstreetmap.org/",
    }


def _overpass_query(mission: str, hubs: list[tuple[float, float, int]]) -> str:
    filters = MISSION_FILTERS.get(mission) or MISSION_FILTERS["warehouse"]
    clauses = []
    for lat, lng, radius in hubs:
        for selector in filters:
            clauses.append(f"  {selector}(around:{int(radius)},{lat:.5f},{lng:.5f});")
    joined = "\n".join(clauses)
    return (
        f"[out:json][timeout:{OVERPASS_SERVER_TIMEOUT}];\n"
        "(\n"
        f"{joined}\n"
        ");\n"
        "out center 48;"
    )


def _overpass_search(mission: str, hubs: list[tuple[float, float, int]]) -> list[dict]:
    payload = urllib.parse.urlencode({"data": _overpass_query(mission, hubs)}).encode()
    last_error: Exception | None = None
    data: dict | None = None
    deadline = time.monotonic() + OVERPASS_TOTAL_BUDGET
    for url in OVERPASS_URLS:
        remaining = deadline - time.monotonic()
        if remaining < 2:
            break
        try:
            raw = _http_json(url, data=payload, timeout=min(OVERPASS_SERVER_TIMEOUT + 2, remaining))
            if isinstance(raw, dict):
                data = raw
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
    if data is None:
        raise DiscoverError(f"OpenStreetMap search failed ({type(last_error).__name__ if last_error else 'empty'})")
    out = []
    for element in data.get("elements") or []:
        parsed = _element_to_site(mission, element)
        if parsed:
            out.append(parsed)
    return out



def _element_to_site(mission: str, element: dict) -> dict | None:
    tags = element.get("tags") or {}
    if element.get("type") == "node":
        lat, lng = element.get("lat"), element.get("lon")
    else:
        center = element.get("center") or {}
        lat, lng = center.get("lat"), center.get("lon")
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return None
    if lat < 18 or lat > 72 or lng < -180 or lng > -65:
        return None
    osm_type = element.get("type") or "node"
    osm_id = element.get("id")
    if osm_id is None:
        return None
    name = _site_name(mission, tags, osm_id)
    address = _site_address(tags)
    return {
        "id": f"osm_{osm_type}_{osm_id}",
        "name": name,
        "named": bool(tags.get("name")),
        "lat": lat,
        "lng": lng,
        "address": address,
        "label": "POTENTIAL",
        "site_form": "existing_asset" if mission == "home" else "either",
        "source": "openstreetmap",
        "captured_at": _now(),
        "source_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
        "authorization": OSM_TERMS,
    }


def _site_name(mission: str, tags: dict, osm_id: int) -> str:
    if tags.get("name"):
        return str(tags["name"])
    address = _site_address(tags)
    if address:
        return address
    kind = {
        "warehouse": "Warehouse",
        "custom": "Warehouse",
        "farm": "Farm",
        "home": "House",
        "data_center": "Data hall",
    }.get(mission, "Site")
    return f"{kind} OSM {osm_id}"


def _site_address(tags: dict) -> str | None:
    number = tags.get("addr:housenumber")
    street = tags.get("addr:street")
    city = tags.get("addr:city")
    if number and street:
        city_bit = f", {city}" if city else ""
        return f"{number} {street}{city_bit}"
    return None


def _dedup(sites: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for site in sites:
        lat, lng = site["lat"], site["lng"]
        if any(abs(lat - other["lat"]) <= DEDUP_DEG and abs(lng - other["lng"]) <= DEDUP_DEG for other in kept):
            continue
        kept.append(site)
    return kept


def _spread(sites: list[dict], limit: int) -> list[dict]:
    if len(sites) <= limit:
        return sites
    picked = [sites[0]]
    rest = sites[1:]
    while len(picked) < limit and rest:
        best_i = 0
        best_d = -1.0
        for i, site in enumerate(rest):
            dist = min(
                (site["lat"] - other["lat"]) ** 2 + (site["lng"] - other["lng"]) ** 2
                for other in picked
            )
            if dist > best_d:
                best_d = dist
                best_i = i
        picked.append(rest.pop(best_i))
    return picked


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    x = math.radians(lng2 - lng1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return math.hypot(x, y) * 6371.0


def _rank(sites: list[dict], hubs: list[tuple[float, float, int]]) -> list[dict]:
    """Closest to a search hub first. A named place gets a 5 km credit."""
    for site in sites:
        dist = min(_distance_km(site["lat"], site["lng"], lat, lng) for lat, lng, _ in hubs)
        site["distance_km"] = round(dist, 1)
        site["why"] = (
            f"{'Named' if site.get('named') else 'Mapped'} "
            f"{site['distance_km']} km from the search hub"
        )
    return sorted(
        sites,
        key=lambda s: s["distance_km"] - (5.0 if s.get("named") else 0.0),
    )


def _hubs_for(search_region: str, look: dict | None) -> list[tuple[float, float, int]]:
    if look:
        return [(look["lat"], look["lng"], 28000)]
    return list(REGION_HUBS.get(search_region) or REGION_HUBS["texas_triangle"])


def discover_sites(
    mission: str,
    *,
    search_region: str = "texas_triangle",
    look_query: str = "",
    network: bool = True,
    limit: int = MAX_RESULTS,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> dict:
    """Return POTENTIAL map sites for Find-a-Site.

    ``network=False`` replays cache/fixtures only. That keeps tests and the
    board usable when Overpass is rate-limited.
    """
    mission = (mission or "warehouse").replace(" ", "_").lower()
    look_query = (look_query or "").strip()
    cache_root = cache_dir or CACHE_DIR
    fixture_root = fixture_dir or FIXTURE_DIR
    key = _cache_key(mission, search_region, look_query)
    # Fixtures are curated replay; the cache is opportunistic and may predate
    # the current schema. Fixtures win.
    cached = _read_json(fixture_root / f"{key}.json") or _read_json(cache_root / f"{key}.json")
    if cached and cached.get("candidates"):
        return cached

    look = None
    note = "OpenStreetMap map features. Not listings. Not for sale here."
    source = "openstreetmap"
    if look_query:
        if network:
            look = geocode_look(look_query)
        elif cached and cached.get("look"):
            look = cached["look"]
        else:
            raise DiscoverError("no replay for that city; live map search is off")

    hubs = _hubs_for(search_region, look)
    candidates: list[dict] = []
    if network:
        try:
            ranked = _rank(_dedup(_overpass_search(mission, hubs)), hubs)
            candidates = _rank(_spread(ranked, limit), hubs)
        except DiscoverError as exc:
            if cached and cached.get("candidates"):
                cached = dict(cached)
                cached["note"] = f"{cached.get('note') or note} Overpass missed ({exc}). Using cache."
                return cached
            raise
    elif cached:
        return cached
    else:
        return {
            "mission": mission,
            "search_region": search_region,
            "look": look,
            "candidates": [],
            "source": "none",
            "source_url": OSM_TERMS,
            "note": "No cached map search for this area.",
            "fetched_at": _now(),
        }

    payload = {
        "mission": mission,
        "search_region": search_region,
        "look": look,
        "candidates": candidates,
        "source": source,
        "source_url": OSM_TERMS,
        "note": note,
        "fetched_at": _now(),
        "count": len(candidates),
    }
    # An empty result is worth returning but not persisting: the read path
    # ignores empty payloads, so writing one only plants a junk file.
    if candidates:
        _write_json(cache_root / f"{key}.json", payload)
    return payload
