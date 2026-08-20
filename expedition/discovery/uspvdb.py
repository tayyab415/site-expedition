"""USGS USPVDB large-scale solar facilities. Anchors, not listings.

Public PostgREST: https://energy.usgs.gov/api/uspvdb/v1/projects
Data: https://energy.usgs.gov/uspvdb/data/
These are operating PV plants. Hop from them to nearby industrial land.
They are never Market Availability.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from expedition.adapters.discover import USER_AGENT, _now
from expedition.discovery.schema import Seed, in_us

BASE = "https://energy.usgs.gov/api/uspvdb/v1/projects"
SOURCE_PAGE = "https://energy.usgs.gov/uspvdb/data/"
DEG = 0.28  # ~30 km


def search_uspvdb(
    lat: float,
    lng: float,
    *,
    limit: int = 8,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    # PostgREST repeats ylat/xlong with gte and lte; urlencode would collapse them.
    query = (
        f"ylat=gte.{lat - DEG}&ylat=lte.{lat + DEG}"
        f"&xlong=gte.{lng - DEG}&xlong=lte.{lng + DEG}"
        f"&limit={int(limit)}"
        "&order=p_cap_ac.desc"
    )
    url = f"{BASE}?{query}"
    try:
        rows = http_json(url) if http_json is not None else _get(url)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return [], f"USPVDB failed ({type(exc).__name__})"
    if not isinstance(rows, list):
        return [], "USPVDB returned a non-list"
    seeds: list[Seed] = []
    for row in rows:
        try:
            plat = float(row["ylat"])
            plng = float(row["xlong"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_us(plat, plng):
            continue
        case_id = row.get("case_id")
        name = row.get("p_name") or f"PV {case_id}"
        cap = row.get("p_cap_ac")
        extra = {
            "case_id": case_id,
            "eia_id": row.get("eia_id"),
            "p_cap_ac": cap,
            "p_state": row.get("p_state"),
            "p_type": row.get("p_type"),
            "note": "Operating USGS USPVDB solar facility. Not a listing.",
        }
        seeds.append(
            Seed(
                id=f"uspvdb_{case_id}",
                name=str(name),
                lat=plat,
                lng=plng,
                address=None,
                label="POTENTIAL",
                site_form="existing_asset",
                source="uspvdb",
                source_url=SOURCE_PAGE,
                authorization=SOURCE_PAGE,
                family="infra_anchor",
                role="anchor",
                captured_at=_now(),
                extra=extra,
            )
        )
    return seeds, None


def _get(url: str) -> list:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode())
