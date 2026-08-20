"""Overpass hops used only by the standalone discovery harness.

Does not modify expedition.adapters.discover. Same public Overpass endpoints,
same POTENTIAL labeling.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse

from expedition.adapters import discover as osm

POWER_FILTERS = (
    'nwr["power"="substation"]',
    'nwr["power"="plant"]',
)


def _query(filters: tuple[str, ...], hubs: list[tuple[float, float, int]]) -> str:
    clauses = []
    for lat, lng, radius in hubs:
        for selector in filters:
            clauses.append(f"  {selector}(around:{int(radius)},{lat:.5f},{lng:.5f});")
    joined = "\n".join(clauses)
    return (
        "[out:json][timeout:20];\n"
        "(\n"
        f"{joined}\n"
        ");\n"
        "out center 48;"
    )


def _search(
    filters: tuple[str, ...],
    hubs: list[tuple[float, float, int]],
    *,
    mission: str,
    role: str,
) -> list[dict]:
    payload = urllib.parse.urlencode({"data": _query(filters, hubs)}).encode()
    last_error: Exception | None = None
    data: dict | None = None
    for url in osm.OVERPASS_URLS:
        try:
            raw = osm._http_json(url, data=payload, timeout=22)
            if isinstance(raw, dict):
                data = raw
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
    if data is None:
        raise osm.DiscoverError(
            f"OpenStreetMap search failed ({type(last_error).__name__ if last_error else 'empty'})"
        )
    out = []
    for element in data.get("elements") or []:
        parsed = osm._element_to_site(mission, element)
        if not parsed:
            continue
        parsed["role"] = role
        if role == "anchor":
            tags = element.get("tags") or {}
            parsed["family"] = "infra_anchor"
            parsed["name"] = tags.get("name") or tags.get("power") or parsed["name"]
            parsed["extra"] = {"osm_power": tags.get("power"), "voltage": tags.get("voltage")}
        out.append(parsed)
    return out


def search_power_anchors(hubs: list[tuple[float, float, int]], *, mission: str) -> list[dict]:
    return _search(POWER_FILTERS, hubs, mission=mission, role="anchor")


def search_around(
    mission: str,
    points: list[dict],
    *,
    radius_m: int = 8000,
    limit: int = 12,
) -> list[dict]:
    hubs = []
    for point in points:
        try:
            hubs.append((float(point["lat"]), float(point["lng"]), int(radius_m)))
        except (KeyError, TypeError, ValueError):
            continue
    if not hubs:
        return []
    hop_mission = "warehouse" if mission in {"data_center", "custom"} else mission
    filters = osm.MISSION_FILTERS.get(hop_mission) or osm.MISSION_FILTERS["warehouse"]
    return osm._spread(osm._dedup(_search(filters, hubs, mission=hop_mission, role="candidate")), limit)
