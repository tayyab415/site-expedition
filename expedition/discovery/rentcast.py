"""RentCast residential sale listings. Home only. LISTED when id + lastSeenDate exist.

Official scope excludes office, retail, industrial, manufacturing, agricultural.
https://developers.rentcast.io/reference/property-listings
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from expedition.adapters.discover import USER_AGENT, _now
from expedition.discovery.schema import Seed, in_us

BASE = "https://api.rentcast.io/v1/listings/sale"
DOCS = "https://developers.rentcast.io/reference/property-listings"
TYPES = "https://developers.rentcast.io/reference/property-types"


def rentcast_key() -> str:
    return (os.environ.get("RENTCAST_API_KEY") or "").strip()


def search_rentcast(
    lat: float,
    lng: float,
    *,
    radius_miles: float = 12,
    limit: int = 12,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    key = rentcast_key()
    if not key:
        return [], "no RENTCAST_API_KEY"
    params = {
        "latitude": f"{lat:.5f}",
        "longitude": f"{lng:.5f}",
        "radius": str(radius_miles),
        "status": "Active",
        "limit": str(int(limit)),
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    try:
        rows = http_json(url, key) if http_json is not None else _get(url, key)
    except urllib.error.HTTPError as exc:
        return [], f"RentCast HTTP {exc.code}"
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return [], f"RentCast failed ({type(exc).__name__})"
    if not isinstance(rows, list):
        return [], "RentCast returned a non-list"
    seeds: list[Seed] = []
    for row in rows:
        try:
            plat = float(row["latitude"])
            plng = float(row["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_us(plat, plng):
            continue
        listing_id = str(row.get("id") or "").strip()
        last_seen = row.get("lastSeenDate")
        if not listing_id or not last_seen:
            continue
        address = row.get("formattedAddress")
        seeds.append(
            Seed(
                id=f"rentcast_{listing_id}",
                name=address or listing_id,
                lat=plat,
                lng=plng,
                address=address,
                label="LISTED",
                site_form="existing_asset",
                source="rentcast",
                source_url=DOCS,
                authorization=TYPES,
                family="listing",
                role="candidate",
                captured_at=_now(),
                extra={
                    "listing_id": listing_id,
                    "last_seen_at": last_seen,
                    "price": row.get("price"),
                    "property_type": row.get("propertyType"),
                    "status": row.get("status"),
                    "mls_number": row.get("mlsNumber"),
                },
            )
        )
    return seeds, None


def _get(url: str, key: str) -> list:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Api-Key": key,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode())
