"""USGS USWTDB wind projects. Anchors, never LISTED.

Public PostgREST: https://energy.usgs.gov/api/uswtdb/v1/turbines
Filter t_state, not p_state. Collapse turbines to one pin per p_name.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from expedition.adapters.discover import USER_AGENT, _now
from expedition.discovery.schema import Seed, in_us

BASE = "https://energy.usgs.gov/api/uswtdb/v1/turbines"
SOURCE_PAGE = "https://energy.usgs.gov/uswtdb/"
DEG = 0.35


def search_uswtdb(
    lat: float,
    lng: float,
    *,
    limit: int = 8,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    query = (
        f"ylat=gte.{lat - DEG}&ylat=lte.{lat + DEG}"
        f"&xlong=gte.{lng - DEG}&xlong=lte.{lng + DEG}"
        f"&select=p_name,t_county,ylat,xlong,p_cap,t_state"
        f"&limit=80"
    )
    url = f"{BASE}?{query}"
    try:
        rows = http_json(url) if http_json is not None else _get(url)
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return [], f"USWTDB failed ({type(exc).__name__})"
    if not isinstance(rows, list):
        return [], "USWTDB returned a non-list"
    seeds: list[Seed] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row.get("p_name") or "").strip()
        if not name or name in seen:
            continue
        try:
            plat = float(row["ylat"])
            plng = float(row["xlong"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_us(plat, plng):
            continue
        seen.add(name)
        slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)[:40]
        seeds.append(
            Seed(
                id=f"uswtdb_{slug}",
                name=name,
                lat=plat,
                lng=plng,
                address=None,
                label="POTENTIAL",
                site_form="existing_asset",
                source="uswtdb",
                source_url=SOURCE_PAGE,
                authorization=SOURCE_PAGE,
                family="infra_anchor",
                role="anchor",
                captured_at=_now(),
                extra={
                    "p_cap": row.get("p_cap"),
                    "t_county": row.get("t_county"),
                    "t_state": row.get("t_state"),
                    "note": "Operating USGS USWTDB wind project. Not a listing.",
                },
            )
        )
        if len(seeds) >= limit:
            break
    return seeds, None


def _get(url: str) -> list:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode())
