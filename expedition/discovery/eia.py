"""EIA US power plants via the public ArcGIS layer. Anchors, never LISTED.

https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Power_Plants_in_the_US/FeatureServer/0
Attribute source is EIA-860 / 860M / 923. Hop from large plants to nearby industrial land.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from expedition.adapters.discover import USER_AGENT, _now
from expedition.discovery.schema import Seed, in_us

LAYER = (
    "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/"
    "Power_Plants_in_the_US/FeatureServer/0/query"
)
SOURCE_PAGE = "https://www.eia.gov/electricity/data/eia860/"
DEG = 0.35
MIN_MW = 50


def search_eia_plants(
    lat: float,
    lng: float,
    *,
    limit: int = 8,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    where = (
        f"Latitude>={lat - DEG} AND Latitude<={lat + DEG} "
        f"AND Longitude>={lng - DEG} AND Longitude<={lng + DEG} "
        f"AND Total_MW>={MIN_MW}"
    )
    params = {
        "where": where,
        "outFields": "Plant_Code,Plant_Name,City,PrimSource,Total_MW,State,Latitude,Longitude,Street_Add",
        "orderByFields": "Total_MW DESC",
        "resultRecordCount": int(limit),
        "f": "json",
    }
    url = f"{LAYER}?{urllib.parse.urlencode(params)}"
    try:
        payload = http_json(url) if http_json is not None else _get(url)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return [], f"EIA plants failed ({type(exc).__name__})"
    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        return [], "EIA plants returned no features"
    seeds: list[Seed] = []
    for feature in features:
        attrs = (feature or {}).get("attributes") or {}
        try:
            plat = float(attrs["Latitude"])
            plng = float(attrs["Longitude"])
            code = attrs["Plant_Code"]
        except (KeyError, TypeError, ValueError):
            continue
        if not in_us(plat, plng):
            continue
        mw = attrs.get("Total_MW")
        name = attrs.get("Plant_Name") or f"Plant {code}"
        street = attrs.get("Street_Add")
        city = attrs.get("City")
        address = ", ".join(part for part in (street, city, attrs.get("State")) if part) or None
        seeds.append(
            Seed(
                id=f"eia_{code}",
                name=str(name),
                lat=plat,
                lng=plng,
                address=address,
                label="POTENTIAL",
                site_form="existing_asset",
                source="eia_plants",
                source_url=SOURCE_PAGE,
                authorization=SOURCE_PAGE,
                family="infra_anchor",
                role="anchor",
                captured_at=_now(),
                extra={
                    "plant_code": code,
                    "prim_source": attrs.get("PrimSource"),
                    "total_mw": mw,
                    "note": "Operating EIA power plant. Anchor, not a listing.",
                },
            )
        )
        if len(seeds) >= limit:
            break
    return seeds, None


def _get(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode())
