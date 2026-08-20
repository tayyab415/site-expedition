"""Seed, hop, merge. Source choice is the router. Models only narrate."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from expedition.adapters import discover as osm
from expedition.discovery.osm_hop import search_around, search_power_anchors
from expedition.discovery.echo import search_echo
from expedition.discovery.ee_witness import attach_dynamic_world
from expedition.discovery.eia import search_eia_plants
from expedition.discovery.google_witness import attach_google_witnesses
from expedition.discovery.places import places_available, search_places_hubs
from expedition.discovery.prefilter import prefilter_seeds
from expedition.discovery.rentcast import rentcast_key, search_rentcast
from expedition.discovery.router import plan_sources
from expedition.discovery.schema import Seed, SourcePlan
from expedition.discovery.uspvdb import search_uspvdb
from expedition.discovery.uswtdb import search_uswtdb

MAX_CANDIDATES = 16
MAX_ANCHORS = 8


def run_discovery(
    mission: str,
    *,
    search_region: str = "texas_triangle",
    look_query: str = "",
    scan_budget: str = "quick",
    network: bool = True,
    allow_paid: bool = False,
    prefilter: bool = False,
    live_mireye: bool = False,
    narrate: bool = False,
    expedition_spent: int = 0,
    cache_dir: Path | None = None,
    fixture_dir: Path | None = None,
    limit: int = MAX_CANDIDATES,
) -> dict:
    """Return candidates + anchors + the source plan that produced them."""
    plan = plan_sources(
        mission,
        scan_budget,
        allow_paid=allow_paid,
        places_key=places_available(),
        rentcast_key=bool(rentcast_key()),
    )
    osm_payload = {
        "look": None,
        "candidates": [],
        "note": "OpenStreetMap map features. Not listings. Not for sale here.",
    }
    try:
        osm_payload = osm.discover_sites(
            plan.mission,
            search_region=search_region,
            look_query=look_query,
            network=network,
            limit=limit,
            cache_dir=cache_dir,
            fixture_dir=fixture_dir,
        )
        osm_ok = True
        osm_err = None
    except osm.DiscoverError as exc:
        osm_ok = False
        osm_err = str(exc)
        if look_query and network:
            try:
                osm_payload["look"] = osm.geocode_look(look_query)
            except osm.DiscoverError:
                pass

    look = osm_payload.get("look")
    try:
        hubs = osm._hubs_for(search_region, look)
    except Exception:
        hubs = list(osm.REGION_HUBS.get(search_region) or osm.REGION_HUBS["texas_triangle"])
    origin = look or {"lat": hubs[0][0], "lng": hubs[0][1]}

    seeds: list[Seed] = [_seed_from_osm(row) for row in osm_payload.get("candidates") or []]
    traces: list[dict] = [
        {
            "source": "osm",
            "ok": osm_ok,
            "count": len(seeds),
            "note": osm_err or osm_payload.get("note"),
        }
    ]
    skip_notes = [
        f"{row.source}: {row.reason}"
        for row in plan.skipped
        if row.source in {"places", "rentcast"} and row.verdict in {"NO_KEY", "BLOCKED"}
    ]

    extras: list[tuple[str, object]] = []
    if network:
        if "places" in plan.seeds:
            extras.append(
                ("places", lambda: search_places_hubs(plan.mission, hubs, limit=limit))
            )
        if "rentcast" in plan.seeds:
            extras.append(("rentcast", lambda: search_rentcast(origin["lat"], origin["lng"], limit=limit)))
        if "echo" in plan.seeds:
            extras.append(("echo", lambda: search_echo(hubs, limit=limit)))
        if "uspvdb" in plan.hops:
            extras.append(("uspvdb", lambda: search_uspvdb(origin["lat"], origin["lng"])))
        if "uswtdb" in plan.hops:
            extras.append(("uswtdb", lambda: search_uswtdb(origin["lat"], origin["lng"])))
        if "eia" in plan.hops:
            extras.append(("eia", lambda: search_eia_plants(origin["lat"], origin["lng"])))
        if "osm_power" in plan.hops:
            extras.append(("osm_power", lambda: _power_hop(plan.mission, hubs)))

    if extras:
        with ThreadPoolExecutor(max_workers=min(4, len(extras))) as pool:
            futures = {pool.submit(fn): name for name, fn in extras}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    found, err = future.result()
                except osm.DiscoverError as exc:
                    traces.append({"source": name, "ok": False, "count": 0, "note": str(exc)})
                    continue
                except Exception as exc:
                    traces.append(
                        {"source": name, "ok": False, "count": 0, "note": f"{type(exc).__name__}"}
                    )
                    continue
                if err:
                    traces.append({"source": name, "ok": False, "count": 0, "note": err})
                    skip_notes.append(f"{name}: {err}")
                    continue
                seeds.extend(found)
                traces.append({"source": name, "ok": True, "count": len(found), "note": None})

    hop_candidates = [s for s in seeds if s.role == "candidate"]
    anchors_found = [s for s in seeds if s.role == "anchor"]
    hop_needed = bool(anchors_found) and (
        plan.mission in {"data_center", "farm"} or len(hop_candidates) < 8
    )
    if network and hop_needed:
        anchors = [s.to_candidate() for s in seeds if s.role == "anchor"][:4]
        try:
            hopped = search_around(plan.mission, anchors, radius_m=8000, limit=limit)
        except osm.DiscoverError as exc:
            traces.append({"source": "osm_hop", "ok": False, "count": 0, "note": str(exc)})
        else:
            for row in hopped:
                seeds.append(_seed_from_osm(row))
            traces.append({"source": "osm_hop", "ok": True, "count": len(hopped), "note": None})

    spent = 0
    prefilter_note = None
    want_prefilter = prefilter or (plan.mireye_prefilter and live_mireye)
    if want_prefilter:
        seeds, spent, prefilter_note = prefilter_seeds(
            seeds, live=live_mireye, expedition_spent=expedition_spent
        )
        traces.append(
            {
                "source": "mireye_prefilter",
                "ok": prefilter_note is None,
                "count": len([s for s in seeds if s.extra.get("prefilter")]),
                "note": prefilter_note,
                "credits": spent,
            }
        )

    candidates, anchors = _merge(seeds, limit=limit)
    if network and allow_paid and candidates:
        candidates, google_traces = attach_google_witnesses(candidates, dest=origin)
        traces.extend(google_traces)
    if network and scan_budget == "deep" and candidates:
        candidates, ee_trace = attach_dynamic_world(candidates)
        traces.append(ee_trace)
    note = osm_payload.get("note") or "Map and facility features. Not listings unless a licensed source says so."
    if skip_notes:
        note = f"{note} Skipped: {'; '.join(skip_notes[:3])}"
    if prefilter_note:
        note = f"{note} {prefilter_note}"

    narration = None
    if narrate:
        narration = _narrate(plan, traces, candidates)

    return {
        "mission": plan.mission,
        "search_region": search_region,
        "look": look,
        "look_query": look_query,
        "scan_budget": plan.scan_budget,
        "candidates": [s.to_candidate() for s in candidates],
        "anchors": [s.to_candidate() for s in anchors],
        "count": len(candidates),
        "source": "discovery_harness",
        "source_url": osm.OSM_TERMS,
        "note": note,
        "fetched_at": osm._now(),
        "plan": _plan_dict(plan),
        "traces": traces,
        "credits_spent": spent,
        "narration": narration,
    }


def _power_hop(mission: str, hubs: list[tuple[float, float, int]]) -> tuple[list[Seed], str | None]:
    rows = search_power_anchors(hubs, mission=mission)
    return [_seed_from_osm(row, role="anchor", family="infra_anchor") for row in rows], None


def _seed_from_osm(row: dict, role: str | None = None, family: str | None = None) -> Seed:
    return Seed(
        id=row["id"],
        name=row.get("name") or row["id"],
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        address=row.get("address"),
        label=row.get("label") or "POTENTIAL",
        site_form=row.get("site_form") or "either",
        source=row.get("source") or "openstreetmap",
        source_url=row.get("source_url") or osm.OSM_TERMS,
        authorization=row.get("authorization") or osm.OSM_TERMS,
        family=family or row.get("family") or "map_feature",
        role=role or row.get("role") or "candidate",
        captured_at=row.get("captured_at") or osm._now(),
        extra=dict(row.get("extra") or {}),
    )


def _merge(seeds: list[Seed], *, limit: int) -> tuple[list[Seed], list[Seed]]:
    candidates: list[Seed] = []
    anchors: list[Seed] = []
    seen_ids: set[str] = set()
    for seed in seeds:
        if seed.id in seen_ids:
            continue
        bucket = anchors if seed.role == "anchor" else candidates
        if any(
            abs(seed.lat - other.lat) <= osm.DEDUP_DEG and abs(seed.lng - other.lng) <= osm.DEDUP_DEG
            for other in bucket
        ):
            continue
        seen_ids.add(seed.id)
        bucket.append(seed)
    spread = osm._spread([s.to_candidate() for s in candidates], limit)
    by_id = {s.id: s for s in candidates}
    ordered = [by_id[row["id"]] for row in spread if row["id"] in by_id]
    return ordered, anchors[:MAX_ANCHORS]


def _plan_dict(plan: SourcePlan) -> dict:
    return {
        "mission": plan.mission,
        "scan_budget": plan.scan_budget,
        "seeds": list(plan.seeds),
        "hops": list(plan.hops),
        "mireye_prefilter": plan.mireye_prefilter,
        "why": plan.why,
        "skipped": [
            {"source": s.source, "reason": s.reason, "verdict": s.verdict} for s in plan.skipped
        ],
    }


def _narrate(plan: SourcePlan, traces: list[dict], candidates: list[Seed]) -> dict:
    from expedition.adapters.model import complete

    prompt = (
        "You narrate a site-discovery run. You do not decide KEEP/KILL and you "
        "do not call anything a listing unless traces include rentcast LISTED.\n"
        f"Plan: {plan.why}\n"
        f"Traces: {traces}\n"
        f"Candidate count: {len(candidates)}\n"
        "Return one short paragraph."
    )
    result = complete(prompt)
    return {
        "ok": bool(result.get("ok")),
        "text": (result.get("text") or "").strip()[:800],
        "model": result.get("model"),
        "provider": result.get("provider"),
    }
