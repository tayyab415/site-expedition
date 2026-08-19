"""Expedition runtime. Does not import verify.gates."""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from expedition.adapters import aerial, earth, epa, mireye, routes, temporal
from expedition.adapters.model import skeptic_review
from expedition.candidates import (
    CandidatePool,
    SearchBand,
    SearchRegion,
    normalize_inline_candidate,
)
from expedition.credits import snapshot
from expedition.evidence import (
    EvidenceAtom,
    atom_from_mireye_field,
    detect_contradictions,
    dump_atoms,
)
from expedition.orchestration import (
    ActivationDecision,
    Workstream,
    WorkstreamOutcome,
    run_workstreams,
)
from expedition.plan import MissionPlan, compile_plan
from expedition.scene import build_scene
from expedition.verdict import judge

ROOT = Path(__file__).resolve().parent
CANDIDATES = json.loads((ROOT / "data" / "candidates.json").read_text())
HARNESS_MIREYE = ROOT.parent / "harness" / "cache" / "mireye"

# Questions the Expedition Rail must show. Skill ids stay on the packet for tests.
WORKSTREAM_QUESTIONS = {
    "identity": "Where is this Candidate Site, exactly?",
    "screen-site-core": "Does present-state evidence veto this site?",
    "environmental-record": "Is there a nearby hazardous-facility record that needs Phase I?",
    "route-reality": "Can this operation reach its declared destinations on real roads?",
    "flood-rewind": "Has flood behavior changed, and do elevation models disagree?",
    "farm-history": "Has this land been cultivated, and what is the crop and rain history?",
    "observed-heat": "How hot has this site actually been in observed summers?",
    "today-scene": "What does the site look like from the air?",
    "skeptic-review": "What would disqualify the apparent finalist?",
}
WORKSTREAM_PHASE = {
    "identity": "screen",
    "screen-site-core": "screen",
    "core-gate": "screen",
    "environmental-record": "deepen",
    "route-reality": "deepen",
    "flood-rewind": "deepen",
    "farm-history": "deepen",
    "observed-heat": "deepen",
    "today-scene": "context",
    "skeptic-review": "skeptic",
}


def annotate_workstream(row: dict) -> dict:
    workstream_id = row.get("id") or row.get("workstream_id")
    out = dict(row)
    out["id"] = workstream_id
    out["question"] = WORKSTREAM_QUESTIONS.get(workstream_id) or out.get("question") or workstream_id
    out["phase"] = WORKSTREAM_PHASE.get(workstream_id) or out.get("phase") or "deepen"
    return out


def load_candidate(candidate_id: str) -> dict:
    for row in CANDIDATES["candidates"]:
        if row["id"] == candidate_id:
            return row
    raise KeyError(candidate_id)


def _warehouse_candidate_band(search_region: str, candidate_id: str) -> str | None:
    """Reviewed geography bands for the frozen Warehouse candidate pool."""
    mappings = {
        "texas_triangle": {
            "san_leon": "selected", "san_marcos_tx": "selected",
            "alliance_tx": "selected", "port_houston": "selected",
        },
        "houston_metro": {
            "san_leon": "selected", "port_houston": "selected",
            "san_marcos_tx": "adjacent", "alliance_tx": "statewide",
        },
        "austin_san_antonio": {
            "san_marcos_tx": "selected", "san_leon": "adjacent",
            "port_houston": "adjacent", "alliance_tx": "statewide",
        },
        "dallas_fort_worth": {
            "alliance_tx": "selected", "san_marcos_tx": "adjacent",
            "san_leon": "statewide", "port_houston": "statewide",
        },
    }
    return mappings.get(search_region, {}).get(candidate_id)


def _effects(plan: MissionPlan) -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    for field_id in plan.fields:
        if field_id in {"fema_flood_zone", "within_floodplain_polygon"}:
            out[field_id] = ("FACT", "VETO" if plan.flood_intolerant else "GATE", "authoritative")
        elif field_id == "is_cultivated":
            out[field_id] = ("FACT", "VETO" if plan.require_cultivated else "INFORM", "authoritative")
        elif field_id == "within_water_service_area" and plan.require_water_service:
            out[field_id] = ("FACT", "VETO", "authoritative")
        elif field_id == "within_sewer_service_area" and plan.require_sewer_service:
            out[field_id] = ("FACT", "VETO", "authoritative")
        elif field_id == "fiber_broadband_available" and plan.require_fiber_service:
            out[field_id] = ("FACT", "VETO", "authoritative")
        elif field_id in {
            "nearest_major_road_distance_m",
            "nearest_major_road_class",
            "nearest_long_haul_rail_corridor_distance_m",
            "nearest_substation_distance_m",
            "nearest_substation_max_voltage_kv",
            "substations_within_radius_count",
            "max_transmission_line_voltage_kv_within_radius",
            "fiber_broadband_available",
            "fiber_provider_count",
            "within_water_service_area",
            "within_sewer_service_area",
            "electric_utility_service_territory",
            "nearest_hazardous_facility_distance_m",
            "nearest_superfund_distance_m",
        }:
            out[field_id] = ("PROXY", "INFORM", "proxy")
        else:
            out[field_id] = ("FACT", "INFORM", "authoritative")
    return out


def _seed_harness_cache(candidate_id: str) -> None:
    mapping = {
        "san_leon": "san_leon",
        "austin_winfield": "3605_winfield_cove_austin_tx",
    }
    slug = mapping.get(candidate_id)
    if not slug:
        return
    src = HARNESS_MIREYE / f"{slug}.json"
    dest = ROOT / "var" / "cache" / "mireye" / f"{candidate_id}.json"
    if src.exists() and not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text())


def run_site(
    mission: str,
    candidate_id: str,
    *,
    live: bool = False,
    review: bool = False,
    controls: dict | None = None,
    candidate: dict | None = None,
    trusted_candidate: bool = False,
    on_progress=None,
) -> dict:
    controls = controls or {}
    plan = compile_plan(
        mission,
        flood_intolerant=controls.get("flood_intolerant"),
        require_cultivated=controls.get("require_cultivated"),
        route_anchors=controls.get("route_anchors"),
        scan_budget=controls.get("scan_budget") or "standard",
        site_form=controls.get("site_form") or "either",
        manifest_id=controls.get("manifest_id"),
        search_region=controls.get("search_region") or "texas_triangle",
        geography_band=controls.get("geography_band") or "selected_region",
        size_band=controls.get("size_band") or "flexible",
        budget_band=controls.get("budget_band") or "flexible",
        preferences=controls.get("preferences") or [],
        optional_investigations=(
            controls.get("optional_investigations")
            if "optional_investigations" in controls
            else None
        ),
        require_water_service=bool(controls.get("require_water_service")),
        require_sewer_service=bool(controls.get("require_sewer_service")),
        require_fiber_service=bool(controls.get("require_fiber_service")),
    )
    mission = plan.mission
    investigations_specified = "optional_investigations" in controls and mission != "custom"
    selected_investigations = set(controls.get("optional_investigations") or [])
    inline_candidate = candidate is not None and not trusted_candidate
    if candidate and trusted_candidate:
        site = dict(candidate)
    elif candidate:
        site = normalize_inline_candidate(candidate, candidate_id=candidate_id)
    else:
        site = load_candidate(candidate_id)
    _seed_harness_cache(candidate_id)
    atoms: list[EvidenceAtom] = []
    spent = 0
    workstreams = []

    workstreams.append(annotate_workstream({"id": "identity", "status": "done", "note": "coordinate pin"}))

    def failed_core_atoms(exc: Exception) -> list[EvidenceAtom]:
        http_status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        if isinstance(exc, FileNotFoundError):
            message = "No replay cache exists for this Candidate Site."
            retryable = False
        elif isinstance(exc, TimeoutError):
            message = "Mireye timed out before the core screen completed."
            retryable = True
        elif isinstance(exc, PermissionError) or http_status in {401, 403}:
            message = "Mireye authentication or authorization blocked the core screen."
            retryable = False
        elif http_status == 402:
            message = "Mireye credits blocked the core screen."
            retryable = False
        elif http_status == 429:
            message = "Mireye rate limiting blocked the core screen."
            retryable = True
        else:
            message = f"Mireye core screen failed ({type(exc).__name__})."
            retryable = isinstance(exc, (ConnectionError, OSError))
        effects = _effects(plan)
        return [
            atom_from_mireye_field(
                candidate_id=candidate_id,
                question_id="screen.core",
                field_id=field_id,
                raw={
                    "status": "failed",
                    "error": {"message_public": message},
                    "http_status": http_status,
                    "retryable": retryable,
                    "source": "mireye",
                },
                lat=site["lat"],
                lng=site["lng"],
                live=False,
                effect=effects[field_id][1],
                kind=effects[field_id][0],
                authority=effects[field_id][2],
                credits=0,
            )
            for field_id in plan.fields
        ]

    def run_core(_ctx):
        try:
            screen_atoms, used, _raw = mireye.fetch_fields(
                candidate_id=candidate_id,
                lat=site["lat"],
                lng=site["lng"],
                fields=plan.fields,
                live=live,
                question_id="screen.core",
                effects=_effects(plan),
                expedition_spent=0,
            )
            return WorkstreamOutcome.success({
                "atoms": screen_atoms,
                "spent": used,
                "display": {"id": "screen-site-core", "status": "done", "credits": used},
            })
        except Exception as exc:
            return WorkstreamOutcome.success({
                "atoms": failed_core_atoms(exc),
                "spent": 0,
                "replay_cache_miss": inline_candidate and isinstance(exc, FileNotFoundError),
                "display": {
                    "id": "screen-site-core",
                    "status": "failed",
                    "note": type(exc).__name__,
                    "credits": 0,
                },
            })

    def run_core_gate(ctx):
        outcome = ctx.snapshot.outcome("screen-site-core")
        payload = outcome.payload if outcome and isinstance(outcome.payload, dict) else {}
        provisional = judge(
            plan,
            candidate_id,
            payload.get("atoms") or [],
            candidate=site,
        )
        return WorkstreamOutcome.success(
            {"verdict": provisional["verdict"]},
            reliable_veto=provisional["verdict"] == "reject",
        )

    specs = [
        Workstream(
            workstream_id="screen-site-core",
            question_id="screen.core",
            run=run_core,
            cancel_on_veto=False,
        ),
        Workstream(
            workstream_id="core-gate",
            question_id="screen.core.verdict",
            run=run_core_gate,
            depends_on=("screen-site-core",),
            cancel_on_veto=False,
        )
    ]

    if "environmental-record" in plan.skills and (
        not investigations_specified
        or "environmental_record" in selected_investigations
    ):
        def environmental_hit(snapshot):
            outcome = snapshot.outcome("screen-site-core")
            payload = outcome.payload if outcome and isinstance(outcome.payload, dict) else {}
            for atom in payload.get("atoms") or []:
                if atom.field_id != "nearest_hazardous_facility_distance_m":
                    continue
                if atom.kind not in {"FACT", "PROXY"} or atom.status not in {"live", "replay"}:
                    continue
                if isinstance(atom.value, (int, float)) and 0 <= atom.value <= 8_000:
                    return atom
            return None

        def run_environmental(ctx):
            hit = environmental_hit(ctx.snapshot)
            if hit is None:
                return WorkstreamOutcome.failure("environmental proximity hit unavailable")
            record_atoms, payload = epa.rmp_record(
                candidate_id=candidate_id,
                lat=site["lat"],
                lng=site["lng"],
                hit_distance_m=float(hit.value),
                live=live,
            )
            record = record_atoms[0]
            facility = (payload.get("facility") or {}) if payload else {}
            note = (
                f"{facility.get('name')} · {facility.get('distance_m')} m"
                if facility
                else (
                    (record.failure or {}).get("message_public")
                    or "no matching EPA ECHO RMP record"
                )
            )
            return WorkstreamOutcome.success({
                "atoms": record_atoms,
                "display": {
                    "id": "environmental-record",
                    "status": (
                        "done"
                        if record.kind == "FACT"
                        else "absent"
                        if record.kind == "ABSENT"
                        else "failed"
                    ),
                    "mode": record.live_label,
                    "note": note,
                },
            })

        specs.append(Workstream(
            workstream_id="environmental-record",
            question_id="environmental.record",
            run=run_environmental,
            depends_on=("screen-site-core",),
            cancel_on_veto=False,
            activate_when=lambda snapshot: (
                ActivationDecision.skip(
                    f"{plan.scan_budget} Scan Budget excludes environmental record drill-down"
                )
                if plan.scan_budget == "quick"
                else ActivationDecision.run()
                if environmental_hit(snapshot) is not None
                else ActivationDecision.skip("no material Mireye environmental proximity hit")
            ),
        ))

    if "route-reality" in plan.skills and (
        not investigations_specified or "route_reality" in selected_investigations
    ):
        def run_routes(_ctx):
            anchors = [a for a in plan.route_anchors if a.get("id") != candidate_id]
            route_atoms = [routes.route_atom(candidate_id, site, anchor, live) for anchor in anchors]
            facts = sum(atom.kind == "FACT" for atom in route_atoms)
            return WorkstreamOutcome.success({
                "atoms": route_atoms,
                "display": {
                    "id": "route-reality",
                    "status": "done" if facts == len(route_atoms) else "partial",
                    "mode": "live" if live else "replay",
                    "anchors": len(route_atoms),
                    "facts": facts,
                    "note": None if facts == len(route_atoms) else "one or more route times UNKNOWN",
                },
            })

        specs.append(Workstream(
            workstream_id="route-reality",
            question_id="logistics.route_time",
            run=run_routes,
            depends_on=("core-gate",),
            activate_when=lambda _snapshot: (
                ActivationDecision.run()
                if plan.scan_budget in {"standard", "deep"}
                else ActivationDecision.skip(f"{plan.scan_budget} Scan Budget excludes route matrix")
            ),
        ))

    if "flood-rewind" in plan.skills and (
        not investigations_specified or "flood_rewind" in selected_investigations
    ):
        def run_flood(ctx):
            try:
                ee_atoms, payload = earth.flood_rewind(
                    candidate_id=candidate_id,
                    lat=site["lat"],
                    lng=site["lng"],
                    live=live and candidate_id == "san_leon",
                )
                water = payload.get("water") or {}
                height = payload.get("height") or {}
                nasadem = height.get("nasadem_m")
                core_outcome = ctx.snapshot.outcome("screen-site-core")
                core_payload = (
                    core_outcome.payload
                    if core_outcome and isinstance(core_outcome.payload, dict)
                    else {}
                )
                elev = next(
                    (
                        atom.value
                        for atom in core_payload.get("atoms") or []
                        if getattr(atom, "field_id", None) == "elevation"
                        and isinstance(atom.value, (int, float))
                    ),
                    None,
                )
                disagree = (
                    abs(float(elev) - float(nasadem))
                    if isinstance(elev, (int, float)) and isinstance(nasadem, (int, float))
                    else None
                )
                dem_note = (
                    f"USGS 3DEP {float(elev):.1f} m vs NASADEM {float(nasadem):.1f} m "
                    f"(Δ {disagree:.1f} m). Disagreement is a gap, not a chosen truth."
                    if disagree is not None
                    else "NASADEM attached as a second DEM. Disagreement with USGS 3DEP is a gap, not a chosen truth."
                )
                return WorkstreamOutcome.success({
                    "atoms": ee_atoms,
                    "witness": {
                        "kind": "flood_rewind",
                        "source": water.get("dataset") or earth.WATER,
                        "breakpoint_year": water.get("breakpoint_year"),
                        "baseline_freq_1985_1999": water.get("baseline_freq_1985_1999"),
                        "latest_freq_2021": water.get("latest_freq_2021"),
                        "series": list(water.get("timeline") or []),
                        "usgs_3dep_m": elev,
                        "nasadem_m": nasadem,
                        "dem_delta_m": None if disagree is None else round(disagree, 2),
                    },
                    "display": {
                        "id": "flood-rewind",
                        "status": "done",
                        "mode": "live" if live else "replay",
                        "note": dem_note,
                    },
                })
            except FileNotFoundError:
                return WorkstreamOutcome.failure("no cache", {"display": {"id": "flood-rewind", "status": "skipped", "note": "no cache"}})
            except Exception as exc:
                return WorkstreamOutcome.failure(type(exc).__name__, {"display": {"id": "flood-rewind", "status": "failed", "note": type(exc).__name__}})

        specs.append(Workstream(
            workstream_id="flood-rewind",
            question_id="hazards.flood_history",
            run=run_flood,
            depends_on=("core-gate",),
            cancel_on_veto=False,
            activate_when=lambda _snapshot: (
                ActivationDecision.run()
                if live or candidate_id in {"san_leon", "austin_winfield"}
                else ActivationDecision.skip("no material replay witness")
            ),
        ))

    temporal_kind = (
        "farm"
        if mission == "farm" and (not investigations_specified or "farm_history" in selected_investigations)
        else "heat"
        if mission == "data_center" and (not investigations_specified or "observed_heat" in selected_investigations)
        else None
    )
    if temporal_kind:
        def run_temporal(_ctx):
            fn = temporal.farm_history if temporal_kind == "farm" else temporal.observed_heat
            witness_atoms, payload = fn(candidate_id=candidate_id, lat=site["lat"], lng=site["lng"], live=live)
            facts = sum(atom.kind == "FACT" for atom in witness_atoms)
            stream_id = "farm-history" if temporal_kind == "farm" else "observed-heat"
            farm = payload.get("farm_history") or {}
            heat = payload.get("observed_heat") or payload.get("heat") or {}
            cdl = farm.get("cdl") or {}
            chirps = farm.get("chirps") or {}
            witness = (
                {
                    "kind": "farm_history",
                    "source": temporal.CDL,
                    "independence_group": "USDA_CDL",
                    "years_observed": cdl.get("years_observed"),
                    "pattern": cdl.get("pattern"),
                    "classes": list(cdl.get("observed_classes") or []),
                    "annual_mean_mm": chirps.get("annual_mean_mm"),
                }
                if temporal_kind == "farm"
                else {
                    "kind": "observed_heat",
                    "source": temporal.MODIS_LST,
                    "independence_group": "MODIS_LST",
                    "window": heat.get("window") or temporal.HEAT_WINDOW,
                }
            )
            return WorkstreamOutcome.success({
                "atoms": witness_atoms,
                "witness": witness,
                "display": {
                    "id": stream_id,
                    "status": "done" if facts == len(witness_atoms) else "partial",
                    "mode": "live" if live else "replay",
                    "facts": facts,
                    "note": None if facts == len(witness_atoms) else "temporal witness remains UNKNOWN",
                },
            })

        specs.append(Workstream(
            workstream_id="farm-history" if temporal_kind == "farm" else "observed-heat",
            question_id="farm.temporal_history" if temporal_kind == "farm" else "data_center.observed_heat",
            run=run_temporal,
            depends_on=("core-gate",),
            activate_when=lambda _snapshot: (
                ActivationDecision.run()
                if plan.scan_budget in {"standard", "deep"}
                else ActivationDecision.skip(f"{plan.scan_budget} Scan Budget excludes temporal witness")
            ),
        ))

    def _emit_transition(transition, _snapshot) -> None:
        if on_progress is None or transition.workstream_id == "core-gate":
            return
        on_progress({
            "event": "workstream",
            "candidate_id": candidate_id,
            "workstream_id": transition.workstream_id,
            "question": WORKSTREAM_QUESTIONS.get(transition.workstream_id),
            "phase": WORKSTREAM_PHASE.get(transition.workstream_id),
            "status": transition.to_status.value,
            "reason": transition.reason,
        })

    witnesses: list[dict] = []
    orchestration = run_workstreams(
        specs,
        max_workers=3,
        budget_limit=8,
        on_transition=_emit_transition,
    )
    for record in orchestration.workstreams:
        if record.workstream_id == "core-gate":
            continue
        payload = record.outcome.payload if record.outcome and isinstance(record.outcome.payload, dict) else {}
        atoms.extend(payload.get("atoms") or [])
        spent += int(payload.get("spent") or 0)
        if isinstance(payload.get("witness"), dict):
            witnesses.append(payload["witness"])
        display = payload.get("display")
        if display:
            workstreams.append(annotate_workstream(display))
        else:
            workstreams.append(annotate_workstream({
                "id": record.workstream_id,
                "status": record.status.value,
                "note": record.reason,
            }))

    core_record = orchestration.record("screen-site-core")
    core_payload = (
        core_record.outcome.payload
        if core_record.outcome and isinstance(core_record.outcome.payload, dict)
        else {}
    )
    if core_payload.get("replay_cache_miss"):
        raise FileNotFoundError("no replay cache for this USER SITE; enable Live Mireye")

    verdict = judge(plan, candidate_id, atoms, candidate=site)
    epa_record = next(
        (
            atom
            for atom in atoms
            if atom.field_id == "epa_rmp_facility_record" and atom.kind == "FACT"
        ),
        None,
    )
    if epa_record is not None:
        verdict["gaps"].append({
            "gap_id": f"{candidate_id}:environmental_phase_i",
            "candidate_id": candidate_id,
            "question_id": "environmental_phase_i",
            "missing_authority": "Phase I Environmental Site Assessment",
            "blocking": True,
            "atom_ids": [epa_record.atom_id],
            "action": (
                "Commission a current Phase I ESA and review the linked EPA facility record; "
                "nearby RMP registration is a lead, not a clean-site conclusion."
            ),
        })
    contradictions = detect_contradictions(atoms)
    visual_atoms, today_scene = aerial.aerial_atoms(candidate_id, site, live)
    atoms.extend(visual_atoms)
    workstreams.append(annotate_workstream({
        "id": "today-scene",
        "status": "done" if today_scene["state"] in {"ACTIVE", "NOT_FOUND"} else "partial",
        "note": today_scene.get("note") or "ACTIVE Aerial View orbit · presentation only",
    }))
    packet = {
        "mission": plan.mission,
        "plan": plan.to_dict(),
        "candidate": dict(site),
        "atoms": dump_atoms(atoms),
        "verdict": verdict,
        "workstreams": workstreams,
        "credits": {"expedition_spent": spent, "ledger": snapshot()},
        "live": live,
        "today_scene": today_scene,
        "contradictions": [item.to_dict() for item in contradictions],
        "orchestration": {
            "workstreams": [
                {"id": row.workstream_id, "question_id": row.question_id, "status": row.status.value, "attempt_count": len(row.attempts), "reason": row.reason}
                for row in orchestration.workstreams
            ],
            "transitions": [row.to_dict() for row in orchestration.transitions],
            "budget": orchestration.to_dict()["budget"],
            "reliable_vetoes": list(orchestration.reliable_vetoes),
        },
    }
    if review:
        packet["skeptic"] = skeptic_review(
            {
                "candidates": [site["id"]],
                "atoms": packet["atoms"],
                "verdicts": [verdict],
                "gaps": verdict["gaps"],
            },
            live_model=live,
        )
        packet["workstreams"].append(annotate_workstream({
            "id": "skeptic-review",
            "status": "done",
            "note": packet["skeptic"]["stamp"],
        }))
    packet["coverage"] = coverage(atoms, plan)
    packet["scorecard"] = scorecard(plan, verdict, atoms)
    packet["brief"] = _brief(packet)
    packet["scene"] = build_scene(mission=plan.mission, witnesses=witnesses)
    return packet


def run_mission(
    mission: str,
    candidate_ids: list[str],
    *,
    live: bool = False,
    review: bool = False,
    controls: dict | None = None,
    on_progress=None,
) -> dict:
    mission = mission.replace(" ", "_").lower()
    controls = controls or {}
    candidate_changes: list[dict] = []
    candidate_lookup: dict[str, dict] = {}
    run_ids = list(candidate_ids)
    pool = None
    requested_form = controls.get("site_form") or "either"
    if requested_form != "either":
        compatible_ids: list[str] = []
        for candidate_id in run_ids:
            record = load_candidate(candidate_id)
            observed_form = record.get("site_form") or "either"
            if observed_form not in {"either", requested_form}:
                candidate_changes.append({
                    "status": "excluded",
                    "candidate_id": candidate_id,
                    "reason": (
                        f"Candidate Site form {observed_form} does not match "
                        f"the confirmed {requested_form} Mission Plan."
                    ),
                })
                continue
            compatible_ids.append(candidate_id)
        run_ids = compatible_ids
        candidate_ids = compatible_ids
    # The expanded Find-a-Site surface starts with four reviewed candidates,
    # then lets a reliable Reject change the real candidate set. Legacy CLI
    # calls without Search Region controls retain their exact requested list.
    if mission in {"warehouse", "custom"} and controls.get("search_region") and len(candidate_ids) > 4:
        stop_band = {
            "selected_region": "selected",
            "adjacent_regions": "adjacent",
            "statewide": "statewide",
        }.get(controls.get("geography_band"), "selected")
        band_order = {"selected": 0, "adjacent": 1, "statewide": 2}
        band_by_candidate_id = {
            cid: band
            for cid in candidate_ids
            if (band := _warehouse_candidate_band(str(controls["search_region"]), cid)) is not None
            and band_order[band] <= band_order[stop_band]
        }
        records = [load_candidate(cid) for cid in candidate_ids if cid in band_by_candidate_id]
        if not records:
            return {
                "mission": mission,
                "results": [],
                "comparison": [],
                "credits": snapshot(),
                "candidate_changes": [{
                    "status": "exhausted",
                    "reason": "No lawful reviewed candidates in the selected Search Region.",
                    "active_band_id": "selected",
                }],
            }
        search_region = SearchRegion(
            region_id=str(controls["search_region"]),
            label=str(controls["search_region"]).replace("_", " ").title(),
            bands=(
                SearchBand("selected", "Selected region"),
                SearchBand("adjacent", "Adjacent regions"),
                SearchBand("statewide", "Statewide"),
            ),
            widening_allowed=controls.get("geography_band") != "selected_region",
            stop_after_band_id=stop_band,
        )
        # The frozen challenge pool is already curated as one reviewed set.
        # Later licensed adapters can place additional records in wider bands.
        pool = CandidatePool.from_records(
            search_region=search_region,
            records=records,
            band_by_candidate_id=band_by_candidate_id,
        )
        initial = pool.acquire_initial(max(1, len(pool.canonical_entries) - 1))
        run_ids = [entry.candidate_id for entry in initial.candidates]
        candidate_lookup = {
            entry.candidate_id: entry.to_candidate_dict()
            for entry in pool.canonical_entries
        }
        candidate_changes.append({
            "status": "initial",
            "active_band_id": initial.active_band_id,
            "candidates": run_ids,
            "identity_issues": list(initial.identity_issues),
        })
        held = [
            entry.candidate_id
            for entry in pool.canonical_entries
            if entry.candidate_id not in run_ids
        ]
        if on_progress is not None:
            on_progress({
                "event": "pool",
                "active": list(run_ids),
                "held": held,
                "active_band_id": initial.active_band_id,
            })

    results = []
    index = 0
    while index < len(run_ids):
        cid = run_ids[index]
        if on_progress is not None:
            on_progress({"event": "site_start", "candidate_id": cid})
        result = run_site(
            mission,
            cid,
            live=live,
            review=False,
            controls=controls,
            candidate=candidate_lookup.get(cid),
            trusted_candidate=cid in candidate_lookup,
            on_progress=on_progress,
        )
        results.append(result)
        if on_progress is not None:
            on_progress({"event": "site_packet", "candidate_id": cid, "packet": result})
        if pool is not None and result["verdict"]["verdict"] == "reject":
            decision = pool.reject_and_replace(cid)
            change = decision.to_dict()
            candidate_changes.append(change)
            if on_progress is not None:
                on_progress({"event": "candidate_change", **change})
            if decision.candidate is not None:
                run_ids.append(decision.candidate.candidate_id)
                candidate_lookup[decision.candidate.candidate_id] = decision.candidate.to_candidate_dict()
        index += 1
    review_targets = [
        result
        for result in results
        if review or result["verdict"]["verdict"] != "reject"
    ]
    if review_targets:
        graph = {
            "candidates": [result["candidate"]["id"] for result in review_targets],
            "atoms": [
                atom
                for result in review_targets
                for atom in result["atoms"]
            ],
            "verdicts": [result["verdict"] for result in review_targets],
            "gaps": [
                gap
                for result in review_targets
                for gap in result["verdict"]["gaps"]
            ],
        }
        skeptic = skeptic_review(graph, live_model=live)
        for result in review_targets:
            result["skeptic"] = {
                **skeptic,
                "scope": [candidate["candidate"]["id"] for candidate in review_targets],
            }
            result["workstreams"].append(annotate_workstream({
                "id": "skeptic-review",
                "status": "done",
                "note": skeptic["stamp"],
            }))
    comparison = [_comparison_row(result, controls or {}) for result in results]
    comparison.sort(key=_comparison_sort_key)
    return {
        "mission": mission,
        "results": results,
        "comparison": comparison,
        "credits": snapshot(),
        "candidate_changes": candidate_changes,
    }


ROAD_CLASS_RANK = {
    "motorway": 0,
    "trunk": 1,
    "primary": 2,
    "secondary": 3,
    "tertiary": 4,
    "residential": 5,
    "service": 6,
}


def _comparison_row(packet: dict, controls: dict) -> dict:
    gaps = packet["verdict"].get("gaps") or []
    blocking_gap_count = sum(bool(gap.get("blocking")) for gap in gaps)
    atoms = packet.get("atoms") or []
    road = next(
        (
            atom.get("value")
            for atom in atoms
            if atom.get("field_id") == "nearest_major_road_class"
            and atom.get("kind") in {"FACT", "PROXY"}
        ),
        None,
    )
    route_times = _route_times(packet)
    fact_routes = [
        route["duration_s"]
        for route in route_times
        if route["status"] == "FACT" and route["duration_s"] is not None
    ]
    average_route_s = (
        round(sum(fact_routes) / len(fact_routes)) if fact_routes else None
    )
    declared = [
        row for row in (controls.get("preferences") or [])
        if isinstance(row, dict) and row.get("weight") in {"useful", "important", "priority"}
    ]
    weight_rank = {"priority": 0, "important": 1, "useful": 2}
    declared = sorted(
        enumerate(declared),
        key=lambda pair: (weight_rank[pair[1]["weight"]], pair[0]),
    )
    preference_sort = [
        _preference_metric(row["id"], atoms, average_route_s, road)
        for _, row in declared
    ]
    preference_basis = [
        f"{row['id']} ({row['weight']})" for _, row in declared
    ] or [
        "declared road class",
        "mean FACT route time to declared anchors",
    ]
    return {
        "candidate_id": packet["candidate"]["id"],
        "name": packet["candidate"]["name"],
        "label": packet["candidate"]["label"],
        "verdict": packet["verdict"]["verdict"],
        "reasons": packet["verdict"]["reasons"],
        "gap_count": blocking_gap_count,
        "route_times": route_times,
        "road_class": road,
        "average_route_s": average_route_s,
        "preference_basis": ["fewer blocking Verification Gaps", *preference_basis],
        "preference_sort": preference_sort,
        "counterfactual": _counterfactual(packet),
    }


def _comparison_sort_key(row: dict) -> tuple:
    reject_last = 1 if row["verdict"] == "reject" else 0
    road_rank = ROAD_CLASS_RANK.get(str(row.get("road_class") or "").lower(), 99)
    route_rank = row["average_route_s"] if row["average_route_s"] is not None else float("inf")
    declared = tuple(row.get("preference_sort") or ())
    fallback = () if declared else (road_rank, route_rank)
    return (
        reject_last,
        row["gap_count"],
        *declared,
        *fallback,
        row["candidate_id"],
    )


def _preference_metric(preference_id: str, atoms: list[dict], average_route_s, road_class) -> float:
    by_field = {
        atom.get("field_id"): atom.get("value")
        for atom in atoms
        if atom.get("kind") in {"FACT", "PROXY"}
    }
    if preference_id == "major_road_access":
        return float(ROAD_CLASS_RANK.get(str(road_class or "").lower(), 99))
    if preference_id == "route_time":
        return float(average_route_s) if average_route_s is not None else 1e30
    field, higher_is_better = {
        "rail_access": ("nearest_long_haul_rail_corridor_distance_m", False),
        "grid_proximity": ("nearest_substation_distance_m", False),
        "soil_water_capacity": ("soil_available_water_capacity", True),
        "drought_context": ("drought_category", False),
        "road_access": ("nearest_major_road_distance_m", False),
        "hospital_access": ("nearest_hospital_distance_m", False),
        "lower_slope": ("slope_degrees", False),
        "lower_wildfire": ("wildfire_annual_frequency", False),
        "fiber_context": ("fiber_provider_count", True),
        "lower_heat": ("days_above_32c_annual_count", False),
    }.get(preference_id, (None, False))
    value = by_field.get(field) if field else None
    if preference_id == "drought_context" and isinstance(value, str):
        digits = "".join(character for character in value if character.isdigit())
        return float(digits or 99)
    if isinstance(value, bool):
        value = 1 if value else 0
    if not isinstance(value, (int, float)):
        return 1e30
    return -float(value) if higher_is_better else float(value)


def _counterfactual(packet: dict) -> str:
    if packet["verdict"]["verdict"] == "reject":
        reason = (packet["verdict"].get("reasons") or ["mandatory constraint"])[0]
        return f"Would avoid Reject if authoritative evidence cleared {reason}."
    plan = packet.get("plan") or {}
    if plan.get("flood_intolerant"):
        return "Would Reject if authoritative FEMA evidence placed the site in Zone AE."
    if plan.get("require_cultivated"):
        return "Would Reject if authoritative USDA evidence showed the site is not cultivated."
    return "Would Reject if reliable evidence contradicted a confirmed mandatory condition."


def coverage(atoms: list[EvidenceAtom], plan: MissionPlan) -> dict:
    relevant = [a for a in atoms if a.decision_effect in {"VETO", "GATE", "INFORM"}]
    usable = [a for a in relevant if a.kind in {"FACT", "ABSENT"} and a.status in {"live", "replay", "absent"}]
    n = len(relevant) or 1
    return {
        "relevant": len(relevant),
        "usable": len(usable),
        "ratio": round(len(usable) / n, 3),
        "note": "Coverage is not Mission fit. Presentation and failed atoms do not count.",
    }


def scorecard(plan: MissionPlan, verdict: dict, atoms: list[EvidenceAtom]) -> list[dict]:
    """Constraint status bars. Not a composite score."""
    reasons = set(verdict.get("reasons") or [])
    by_field = {a.field_id: a for a in atoms}

    def status_for(fail_reason: str, field_id: str) -> str:
        if fail_reason in reasons:
            return "fail"
        atom = by_field.get(field_id)
        if atom is None or atom.kind in {"FAILED", "UNKNOWN"} or atom.status in {"failed", "blocked"}:
            return "unknown"
        return "pass"

    rows = [
        _meter_row(
            "flood",
            "Mapped floodplain",
            status_for("mapped_sfha", "fema_flood_zone") if plan.flood_intolerant else "inform",
        ),
        _meter_row("identity", "Site identity", "pass"),
        _meter_row("availability", "Market availability", "unknown"),
    ]
    if plan.require_cultivated:
        rows.insert(1, _meter_row(
            "cultivated",
            "Cultivated land",
            status_for("not_cultivated", "is_cultivated"),
        ))
    if plan.mission in {"warehouse", "data_center"}:
        rows.append(_meter_row("capacity", "Electrical capacity", "unknown"))
        rows.append(_meter_row("ingress", "Truck ingress", "unknown"))
    environmental = by_field.get("epa_rmp_facility_record")
    if environmental is not None:
        facility = (
            ((environmental.value or {}).get("facility") or {})
            if isinstance(environmental.value, dict)
            else {}
        )
        rows.append(_meter_row(
            "environmental-record",
            "EPA RMP facility record",
            "inform" if environmental.kind == "FACT" else "unknown",
            value=(
                f"{facility.get('name')} · {facility.get('distance_m')} m"
                if facility
                else "No usable direct record"
            ),
        ))
    for index, atom in enumerate(a for a in atoms if a.field_id == "route_duration_s"):
        destination = (atom.support or {}).get("destination_name") or "declared anchor"
        rows.append(_meter_row(
            f"route-{index}",
            f"Route to {destination}",
            "pass" if atom.kind == "FACT" else "unknown",
            value=_format_duration(atom.value) if atom.kind == "FACT" else "UNKNOWN",
        ))
    if plan.mission == "farm":
        rows.append(_meter_row("water_right", "Water right", "unknown"))
    return rows


def _meter_row(row_id: str, label: str, status: str, value: str | None = None) -> dict:
    meter, tone = {
        "fail": (100, "fail"),
        "pass": (100, "pass"),
        "inform": (55, "inform"),
        "unknown": (35, "unknown"),
    }.get(status, (35, "unknown"))
    row = {"id": row_id, "label": label, "status": status, "meter": meter, "tone": tone}
    if value is not None:
        row["value"] = value
    return row


def _format_duration(value) -> str:
    if not isinstance(value, (int, float)):
        return "UNKNOWN"
    minutes = int(round(value / 60))
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"


def _route_times(packet: dict) -> list[dict]:
    return [
        {
            "anchor_id": (atom.get("support") or {}).get("destination_id"),
            "anchor": (atom.get("support") or {}).get("destination_name"),
            "status": "FACT" if atom.get("kind") == "FACT" else "UNKNOWN",
            "duration_s": atom.get("value") if atom.get("kind") == "FACT" else None,
            "display": _format_duration(atom.get("value")) if atom.get("kind") == "FACT" else "UNKNOWN",
        }
        for atom in packet.get("atoms", [])
        if atom.get("field_id") == "route_duration_s"
    ]


def _brief(packet: dict) -> dict:
    v = packet["verdict"]
    site = packet["candidate"]
    actions = [g["action"] for g in v["gaps"] if g.get("blocking")][:6]
    cited_atoms = [
        atom
        for atom in packet["atoms"]
        if atom.get("kind") in {"FACT", "PROXY", "MODEL"}
    ]
    cited_atoms.sort(
        key=lambda atom: (
            0 if atom.get("field_id") == "epa_rmp_facility_record" else 1,
            atom.get("atom_id") or "",
        )
    )
    return {
        "title": f"{site['name']}: {v['verdict'].replace('_', ' ')}",
        "reasons": v["reasons"],
        "actions": actions or ["No blocking verification action beyond labeled gaps."],
        "citations": [
            {
                **a["citation"],
                "authority": a.get("authority"),
                "source_family": a.get("source_family"),
                "live_label": a.get("live_label"),
            }
            for a in cited_atoms
        ][:12],
    }
