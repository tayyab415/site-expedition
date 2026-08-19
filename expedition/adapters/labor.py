"""Labor-access context. County employment plus optional shed routes.

Never a claim that workers are available. Never used for Home ranking.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from expedition.adapters.witness import (
    fact_atom,
    load_replay,
    support,
    unknown_atom,
    write_payload,
)
from expedition.evidence import utc_now


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "fixtures" / "labor"
CACHE_DIR = ROOT / "var" / "cache" / "labor"

CENSUS_GEO = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
ACS_YEAR = "2023"
ACS_URL = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
CENSUS_TERMS = "https://www.census.gov/data/developers/about/terms-of-service.html"
TRANSFORM = "labor-access-acs-county-v1"
LODES_NOTE = (
    "County ACS employment context. LODES workplace/residence flows are cited "
    "only when a fixture supplies them. This is not worker availability, wage, "
    "or a hiring forecast. Not endorsed by the U.S. Census Bureau."
)


def labor_access(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
    route_atoms: list | None = None,
) -> tuple[list, dict]:
    cache_root = cache_dir or CACHE_DIR
    fixture_root = fixture_dir or FIXTURE_DIR
    if live:
        payload = _live_labor(lat, lng)
        payload.update({"candidate_id": candidate_id, "lat": lat, "lng": lng, "fetched_at": utc_now()})
        write_payload(candidate_id, cache_root, payload)
    else:
        payload = load_replay(candidate_id, lat, lng, cache_root, fixture_root)

    if not payload or "labor_access" not in payload:
        message = "labor-access unavailable; run a bounded live Census pull to populate replay"
        return [
            unknown_atom(
                candidate_id=candidate_id,
                question_id="labor.access",
                field_id="county_employment_context",
                source=f"ACS {ACS_YEAR}",
                source_url=ACS_URL,
                source_family="CENSUS_ACS",
                lat=lat,
                lng=lng,
                transform=TRANSFORM,
                message=message,
            )
        ], {}

    labor = payload["labor_access"]
    fetched = payload.get("fetched_at") or utc_now()
    geom = support(
        lat,
        lng,
        radius_m=None,
        purpose="",
        extra=f"county:{labor.get('geoid')}:acs:{ACS_YEAR}",
    )
    geom["kind"] = "region"
    geom["radius_purpose"] = "county_employment_context_not_site_staffing"
    atoms = [
        fact_atom(
            candidate_id=candidate_id,
            question_id="labor.access",
            field_id="county_employment_context",
            value=labor,
            unit=None,
            source=f"Census ACS {ACS_YEAR}",
            source_url=CENSUS_TERMS,
            source_family="CENSUS_ACS",
            independence_group="CENSUS_ACS",
            support_geom=geom,
            observed_at=f"{ACS_YEAR} ACS 5-year",
            fetched_at=fetched,
            dataset_vintage=f"ACS {ACS_YEAR}",
            transform=TRANSFORM,
            live=live,
            notes=LODES_NOTE,
            window=f"ACS {ACS_YEAR}",
            kind="PROXY",
            authority="proxy",
            confidence="medium",
        )
    ]
    if route_atoms:
        atoms.extend(route_atoms)
    return atoms, payload


def _live_labor(lat: float, lng: float) -> dict:
    geo = _census_county(lat, lng)
    acs = _acs_county(geo["state"], geo["county"]) if geo else {}
    lodes = None
    return {
        "labor_access": {
            "geoid": geo.get("geoid") if geo else None,
            "county_name": geo.get("name") if geo else None,
            "state_fips": geo.get("state") if geo else None,
            "county_fips": geo.get("county") if geo else None,
            "civilian_labor_force": acs.get("labor_force"),
            "civilian_employed": acs.get("employed"),
            "mean_commute_minutes": acs.get("mean_commute"),
            "lodes": lodes,
            "scale": "county",
            "workers_available": None,
        }
    }


def _census_county(lat: float, lng: float) -> dict | None:
    query = urllib.parse.urlencode({
        "x": f"{lng:.6f}",
        "y": f"{lat:.6f}",
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json",
    })
    req = urllib.request.Request(f"{CENSUS_GEO}?{query}", headers={"User-Agent": "mireye-expedition"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    counties = (
        (((data.get("result") or {}).get("geographies") or {}).get("Counties")) or []
    )
    if not counties:
        return None
    row = counties[0]
    geoid = str(row.get("GEOID") or "")
    return {
        "geoid": geoid,
        "name": row.get("NAME"),
        "state": geoid[:2] if len(geoid) >= 5 else None,
        "county": geoid[2:5] if len(geoid) >= 5 else None,
    }


def _acs_county(state: str | None, county: str | None) -> dict:
    if not state or not county:
        return {}
    query = urllib.parse.urlencode({
        "get": "NAME,B23025_002E,B23025_004E,B08303_001E",
        "for": f"county:{county}",
        "in": f"state:{state}",
    })
    req = urllib.request.Request(f"{ACS_URL}?{query}", headers={"User-Agent": "mireye-expedition"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        rows = json.loads(resp.read().decode())
    if not isinstance(rows, list) or len(rows) < 2:
        return {}
    header, values = rows[0], rows[1]
    mapped = dict(zip(header, values))

    def _int(key):
        raw = mapped.get(key)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    return {
        "labor_force": _int("B23025_002E"),
        "employed": _int("B23025_004E"),
        "mean_commute": _int("B08303_001E"),
    }
