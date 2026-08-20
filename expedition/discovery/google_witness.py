"""Google Maps pin witnesses. Never mint candidates. Never score.

On the challenge Maps key: Places, Solar, Street View, Aerial, Geocoding,
Elevation, Static Maps. Routes uses ADC (same as expedition.adapters.routes),
not this key. Nearby Search by type and Autocomplete are not inventory.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import replace

from expedition.adapters.aerial import lookup_metadata as aerial_metadata
from expedition.adapters.aerial import maps_key
from expedition.adapters.discover import USER_AGENT
from expedition.discovery.schema import Seed

SOLAR_URL = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
SV_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
ELEVATION_URL = "https://maps.googleapis.com/maps/api/elevation/json"
ROUTES_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROUTES_PROJECT = "gen-lang-client-0261050164"
PREFERRED_GEOCODE = ("street_address", "premise", "subpremise", "route")


def attach_google_witnesses(
    seeds: list[Seed],
    *,
    key: str | None = None,
    dest: dict | None = None,
    streetview_n: int = 6,
    solar_n: int = 4,
    aerial_n: int = 3,
    reverse_n: int = 8,
    elevation_n: int = 8,
    routes_n: int = 6,
) -> tuple[list[Seed], list[dict]]:
    api_key = key if key is not None else maps_key()
    traces: list[dict] = []
    if not api_key:
        return seeds, [{"source": "google_witness", "ok": False, "count": 0, "note": "no Maps key"}]
    out = list(seeds)
    traces.append(_reverse_geocode(out, api_key, reverse_n))
    traces.append(_elevation(out, api_key, elevation_n))
    traces.append(_streetview(out, api_key, streetview_n))
    traces.append(_solar(out, api_key, solar_n))
    traces.append(_aerial(out, api_key, aerial_n))
    traces.append(_routes(out, dest, routes_n))
    return out, traces


def _streetview(seeds: list[Seed], key: str, limit: int) -> dict:
    n = 0
    err = None
    for i, seed in enumerate(seeds[:limit]):
        url = SV_URL + "?" + urllib.parse.urlencode({"location": f"{seed.lat},{seed.lng}", "key": key})
        try:
            data = _get(url)
        except Exception as exc:
            err = type(exc).__name__
            break
        extra = dict(seed.extra)
        extra["streetview"] = {
            "status": data.get("status"),
            "date": data.get("date"),
            "copyright": data.get("copyright"),
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return {"source": "streetview_meta", "ok": err is None, "count": n, "note": err}


def _solar(seeds: list[Seed], key: str, limit: int) -> dict:
    n = 0
    err = None
    for i, seed in enumerate(seeds[:limit]):
        params = urllib.parse.urlencode(
            {
                "location.latitude": f"{seed.lat:.5f}",
                "location.longitude": f"{seed.lng:.5f}",
                "requiredQuality": "BASE",
            }
        )
        url = f"{SOLAR_URL}?{params}"
        try:
            data = _get(url, headers={"X-Goog-Api-Key": key})
        except urllib.error.HTTPError as exc:
            err = f"Solar HTTP {exc.code}"
            break
        except Exception as exc:
            err = type(exc).__name__
            break
        pot = data.get("solarPotential") or {}
        extra = dict(seed.extra)
        extra["solar"] = {
            "max_panels": pot.get("maxArrayPanelsCount"),
            "max_area_m2": pot.get("maxArrayAreaMeters2"),
            "sunshine_hours": pot.get("maxSunshineHoursPerYear"),
            "postal_code": data.get("postalCode"),
            "note": "Google Solar Building Insights on this pin. Not a listing.",
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return {"source": "google_solar", "ok": err is None, "count": n, "note": err}


def _aerial(seeds: list[Seed], key: str, limit: int) -> dict:
    n = 0
    err = None
    tried = 0
    for i, seed in enumerate(seeds):
        if tried >= limit:
            break
        address = seed.address
        if not address:
            continue
        tried += 1
        try:
            data = aerial_metadata(address, key)
        except urllib.error.HTTPError as exc:
            extra = dict(seed.extra)
            extra["aerial"] = {"ok": False, "http": exc.code}
            seeds[i] = replace(seed, extra=extra)
            continue
        except Exception as exc:
            err = type(exc).__name__
            break
        extra = dict(seed.extra)
        extra["aerial"] = {
            "ok": True,
            "video_id": data.get("videoId"),
            "state": data.get("state"),
            "capture": data.get("captureDate"),
            "note": "Aerial metadata only. Do not cache the video.",
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return {"source": "aerial_meta", "ok": err is None, "count": n, "note": err}


def _reverse_geocode(seeds: list[Seed], key: str, limit: int) -> dict:
    n = 0
    err = None
    for i, seed in enumerate(seeds):
        if n >= limit:
            break
        if seed.address:
            continue
        url = GEOCODE_URL + "?" + urllib.parse.urlencode({"latlng": f"{seed.lat},{seed.lng}", "key": key})
        try:
            data = _get(url)
        except Exception as exc:
            err = type(exc).__name__
            break
        if data.get("status") != "OK":
            err = data.get("status") or "geocode_denied"
            break
        address, types = _best_address(data.get("results") or [])
        if not address:
            continue
        extra = dict(seed.extra)
        extra["geocode"] = {"types": types, "note": "Google reverse geocode. Session only."}
        seeds[i] = replace(seed, address=address, extra=extra)
        n += 1
    return {"source": "geocode_reverse", "ok": err is None, "count": n, "note": err}


def _best_address(results: list) -> tuple[str | None, list]:
    picked = None
    for row in results:
        types = tuple(row.get("types") or ())
        if any(t in PREFERRED_GEOCODE for t in types):
            picked = row
            break
    if picked is None and results:
        picked = results[0]
    if not picked:
        return None, []
    return picked.get("formatted_address"), list(picked.get("types") or [])


def _elevation(seeds: list[Seed], key: str, limit: int) -> dict:
    targets = seeds[:limit]
    if not targets:
        return {"source": "elevation", "ok": True, "count": 0, "note": None}
    locs = "|".join(f"{s.lat:.5f},{s.lng:.5f}" for s in targets)
    url = ELEVATION_URL + "?" + urllib.parse.urlencode({"locations": locs, "key": key})
    try:
        data = _get(url)
    except Exception as exc:
        return {"source": "elevation", "ok": False, "count": 0, "note": type(exc).__name__}
    if data.get("status") != "OK":
        return {"source": "elevation", "ok": False, "count": 0, "note": data.get("status")}
    rows = data.get("results") or []
    n = 0
    for i, seed in enumerate(targets):
        if i >= len(rows):
            break
        extra = dict(seed.extra)
        extra["elevation"] = {
            "meters": rows[i].get("elevation"),
            "resolution_m": rows[i].get("resolution"),
            "note": "Google Elevation API. Not USGS 3DEP.",
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return {"source": "elevation", "ok": True, "count": n, "note": None}


def _routes(seeds: list[Seed], dest: dict | None, limit: int) -> dict:
    if not dest or dest.get("lat") is None or limit <= 0:
        return {"source": "routes", "ok": True, "count": 0, "note": "no dest"}
    targets = seeds[:limit]
    if not targets:
        return {"source": "routes", "ok": True, "count": 0, "note": None}
    try:
        from expedition.adapters.routes import _adc_token

        token = _adc_token()
        body = {
            "origins": [
                {
                    "waypoint": {
                        "location": {"latLng": {"latitude": s.lat, "longitude": s.lng}}
                    }
                }
                for s in targets
            ],
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {"latitude": float(dest["lat"]), "longitude": float(dest["lng"])}
                        }
                    }
                }
            ],
            "travelMode": "DRIVE",
        }
        data = _post_routes(body, token)
    except Exception as exc:
        return {"source": "routes", "ok": False, "count": 0, "note": type(exc).__name__}
    rows = data if isinstance(data, list) else [data]
    by_origin = {}
    for row in rows:
        if row.get("originIndex") is None:
            continue
        by_origin[int(row["originIndex"])] = row
    n = 0
    for i, seed in enumerate(targets):
        row = by_origin.get(i)
        if not row:
            continue
        dur = str(row.get("duration") or "0s").rstrip("s")
        extra = dict(seed.extra)
        extra["drive"] = {
            "duration_s": int(dur or 0),
            "distance_m": row.get("distanceMeters"),
            "dest": dest.get("name") or "search origin",
            "note": "Google Routes matrix. Drive time, not a listing.",
        }
        seeds[i] = replace(seed, extra=extra)
        n += 1
    return {"source": "routes", "ok": True, "count": n, "note": None}


def _post_routes(body: dict, token: str):
    request = urllib.request.Request(
        ROUTES_URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status",
            "X-Goog-User-Project": ROUTES_PROJECT,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def _get(url: str, headers: dict | None = None) -> dict:
    merged = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        merged.update(headers)
    request = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode())
