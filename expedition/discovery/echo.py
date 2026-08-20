"""EPA ECHO NAICS 493 warehousing facilities. POTENTIAL, never LISTED.

Unfiltered ECHO radius search is construction noise. NAICS 493 is
regulated warehousing. Occupied Amazon boxes and tank terminals are dropped.
Docs: https://echo.epa.gov/tools/web-services
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from expedition.adapters.discover import USER_AGENT, _now
from expedition.adapters.epa import BASE, QCOLUMNS, SOURCE_PAGE
from expedition.discovery.schema import Seed, in_us

NAICS = "493110,493120,493130,493190"
SKIP_IN_NAME = (
    "amazon",
    "walmart",
    "target",
    "kroger",
    "terminal",
    "refinery",
    "splitter",
    "recycling",
    "pipeline",
    "tank",
    "home depot",
    "hd pro",
)


def search_echo(
    hubs: list[tuple[float, float, int]],
    *,
    limit: int = 12,
    http_json=None,
) -> tuple[list[Seed], str | None]:
    seen: set[str] = set()
    seeds: list[Seed] = []
    last_err: str | None = None
    for lat, lng, radius_m in hubs[:4]:
        miles = min(25.0, max(3.0, radius_m / 1609.344))
        try:
            rows = (
                http_json(lat, lng, miles)
                if http_json is not None
                else _get(lat, lng, miles)
            )
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_err = f"ECHO failed ({type(exc).__name__})"
            continue
        for row in rows:
            seed = _row_to_seed(row)
            if seed is None or seed.id in seen:
                continue
            seen.add(seed.id)
            seeds.append(seed)
            if len(seeds) >= limit:
                return seeds, None
    if seeds:
        return seeds, None
    return [], last_err or "no ECHO warehousing facilities"


def _get(lat: float, lng: float, miles: float) -> list:
    params = {
        "output": "JSON",
        "p_lat": round(lat, 5),
        "p_long": round(lng, 5),
        "p_radius": round(miles, 2),
        "p_ncs": NAICS,
        "qcolumns": QCOLUMNS,
    }
    url = f"{BASE}/echo_rest_services.get_facility_info?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        payload = json.loads(response.read().decode())
    facs = (payload.get("Results") or {}).get("Facilities") or []
    return facs if isinstance(facs, list) else [facs]


def _row_to_seed(row: dict) -> Seed | None:
    name = str(row.get("FacName") or "").strip()
    if not name:
        return None
    low = name.lower()
    if any(marker in low for marker in SKIP_IN_NAME):
        return None
    try:
        lat = float(row["FacLat"])
        lng = float(row["FacLong"])
    except (KeyError, TypeError, ValueError):
        return None
    if not in_us(lat, lng):
        return None
    registry = str(row.get("RegistryID") or "").strip()
    if not registry:
        return None
    street = " ".join(part for part in (row.get("FacStreet"), row.get("FacCity"), row.get("FacState")) if part)
    return Seed(
        id=f"echo_{registry}",
        name=name,
        lat=lat,
        lng=lng,
        address=street or None,
        label="POTENTIAL",
        site_form="existing_asset",
        source="epa_echo",
        source_url=SOURCE_PAGE,
        authorization=SOURCE_PAGE,
        family="regulated_facility",
        role="candidate",
        captured_at=_now(),
        extra={
            "registry_id": registry,
            "naics": row.get("FacNAICSCodes"),
            "note": "EPA ECHO NAICS 493 facility. Occupied regulated warehouse, not a listing.",
        },
    )
