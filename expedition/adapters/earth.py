"""Selective Earth Engine witnesses. USGS 3DEP disagreement via NASADEM only."""

from __future__ import annotations

import json
from pathlib import Path

from expedition.evidence import (
    EvidenceAtom,
    cache_identity,
    family_for,
    geometry_hash,
    utc_now,
)

EE_PROJECT = "gen-lang-client-0261050164"
CACHE = Path(__file__).resolve().parent.parent / "var" / "cache" / "earth"
HARNESS_EARTH = Path(__file__).resolve().parents[2] / "harness" / "cache" / "earth"
WATER = "JRC/GSW1_4/MonthlyHistory"
NASADEM = "NASA/NASADEM_HGT/001"
TRANSFORM = "flood-rewind-v1-no-fabdem"


def _legacy_slug(candidate_id: str) -> str | None:
    return {
        "san_leon": "san_leon",
        "austin_winfield": "3605_winfield_cove_austin_tx",
    }.get(candidate_id)


def _from_harness(candidate_id: str) -> dict | None:
    slug = _legacy_slug(candidate_id)
    if not slug:
        return None
    path = HARNESS_EARTH / f"{slug}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def flood_rewind(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    live: bool,
) -> tuple[list[EvidenceAtom], dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE / f"{candidate_id}.json"
    payload = None
    used_live = False
    if cache_path.exists() and not live:
        payload = json.loads(cache_path.read_text())
    elif not live:
        legacy = _from_harness(candidate_id)
        if legacy:
            payload = {
                "water": legacy.get("water"),
                "height": {
                    "nasadem_m": (legacy.get("height") or {}).get("nasadem_m"),
                    "dataset": NASADEM,
                },
                "replayed_from": "harness/cache/earth",
            }
    if payload is None:
        if not live:
            raise FileNotFoundError(f"no EE cache for {candidate_id}")
        payload = _live_rewind(lat, lng)
        used_live = True
        cache_path.write_text(json.dumps(payload, indent=2))

    water = payload.get("water") or {}
    height = payload.get("height") or {}
    fetched = utc_now()
    status = "live" if used_live else "replay"
    live_label = "live" if used_live else "replay"
    support = {
        "kind": "buffer",
        "crs": "EPSG:4326",
        "lat": lat,
        "lng": lng,
        "radius_m": 60,
        "radius_purpose": "jrc_monthly_water_frequency",
        "geometry_hash": geometry_hash(lat, lng, "buffer:60:jrc"),
    }
    fam, group = family_for("jrc_monthly_water_freq")
    atoms = [
        EvidenceAtom(
            atom_id=f"{candidate_id}:jrc_monthly:{live_label}",
            candidate_id=candidate_id,
            question_id="hazards.flood_history",
            field_id="jrc_monthly_water_freq",
            kind="FACT",
            status=status,
            decision_effect="GATE",
            value={
                "baseline_freq_1985_1999": water.get("baseline_freq_1985_1999"),
                "latest_freq_2021": water.get("latest_freq_2021"),
                "breakpoint_year": water.get("breakpoint_year"),
            },
            unit="fraction",
            source=WATER,
            source_url="https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory",
            source_family=fam,
            independence_group=group,
            authority="authoritative",
            support=support,
            observed_at="1985-2021",
            fetched_at=fetched,
            dataset_vintage="GSW1_4",
            ttl=None,
            confidence="medium",
            notes="Same JRC family as Mireye surface_water_permanence_pct. Temporal transform, not independent corroboration.",
            failure=None,
            cost={"credits": 0, "tokens": 0, "unit": "ee"},
            citation={
                "source": WATER,
                "source_url": "https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory",
                "fetched_at": fetched,
                "dataset_vintage": "GSW1_4",
            },
            transform_version=TRANSFORM,
            cache_identity=cache_identity(
                "earth-engine", WATER, "jrc_monthly_water_freq", TRANSFORM,
                support["geometry_hash"], "buffer:60", "1985-2021",
            ),
            live_label=live_label,
        )
    ]
    nasadem = height.get("nasadem_m")
    atoms.append(
        EvidenceAtom(
            atom_id=f"{candidate_id}:nasadem:{live_label}",
            candidate_id=candidate_id,
            question_id="hazards.elevation_disagreement",
            field_id="nasadem_elevation",
            kind="MODEL",
            status=status,
            decision_effect="GATE",
            value=nasadem,
            unit="meters",
            source=NASADEM,
            source_url="https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001",
            source_family="DEM_OTHER",
            independence_group="NASADEM",
            authority="model",
            support={**support, "radius_purpose": "nasadem_point_buffer"},
            observed_at=None,
            fetched_at=fetched,
            dataset_vintage="NASADEM",
            ttl=None,
            confidence="medium",
            notes="Second DEM. Disagreement with 3DEP is a verification gap, not a chosen truth. FABDEM is not used.",
            failure=None,
            cost={"credits": 0, "tokens": 0, "unit": "ee"},
            citation={
                "source": NASADEM,
                "source_url": "https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001",
                "fetched_at": fetched,
                "dataset_vintage": "NASADEM",
            },
            transform_version=TRANSFORM,
            cache_identity=cache_identity(
                "earth-engine", NASADEM, "nasadem_elevation", TRANSFORM,
                support["geometry_hash"], "buffer:60", "",
            ),
            live_label=live_label,
        )
    )
    return atoms, payload


def _import_ee():
    try:
        import ee  # type: ignore
        return ee
    except ImportError:
        venv = Path(__file__).resolve().parents[2] / ".venv-ee" / "lib" / "python3.12" / "site-packages"
        if venv.is_dir():
            import sys
            sys.path.insert(0, str(venv))
            import ee  # type: ignore
            return ee
        raise


def _live_rewind(lat: float, lng: float) -> dict:
    ee = _import_ee()
    ee.Initialize(project=EE_PROJECT)
    pt = ee.Geometry.Point([lng, lat])
    region = pt.buffer(60)
    monthly = ee.ImageCollection(WATER)

    def year_freq(y):
        y = ee.Number(y)
        yr = monthly.filter(ee.Filter.calendarRange(y, y, "year"))
        freq = yr.map(lambda im: im.eq(2).unmask(0)).mean()
        stats = freq.reduceRegion(ee.Reducer.mean(), region, 30, maxPixels=1e8)
        return ee.Feature(None, {"year": y, "water_freq": stats.get("water")})

    rows = ee.FeatureCollection(ee.List.sequence(1985, 2021).map(year_freq)).getInfo()
    timeline = [
        {
            "year": int(r["properties"]["year"]),
            "water_freq": round(r["properties"]["water_freq"] or 0.0, 4),
        }
        for r in rows["features"]
    ]
    base = [t["water_freq"] for t in timeline if t["year"] < 2000]
    baseline = sum(base) / len(base) if base else 0.0
    breakpoint_year = None
    for i, t in enumerate(timeline):
        if t["year"] < 2000 or i < 4:
            continue
        trailing = sum(x["water_freq"] for x in timeline[i - 4 : i + 1]) / 5
        if trailing > max(2 * baseline, baseline + 0.02):
            breakpoint_year = t["year"]
            break
    elev = (
        ee.Image(NASADEM)
        .select("elevation")
        .reduceRegion(ee.Reducer.mean(), region, 30)
        .getInfo()
    )
    return {
        "water": {
            "dataset": WATER,
            "baseline_freq_1985_1999": round(baseline, 4),
            "latest_freq_2021": timeline[-1]["water_freq"] if timeline else None,
            "breakpoint_year": breakpoint_year,
            "timeline": timeline,
        },
        "height": {"nasadem_m": elev.get("elevation"), "dataset": NASADEM},
    }
