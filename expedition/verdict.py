"""Deterministic Strong Fit / Reject / Conditional. No composite score."""

from __future__ import annotations

from expedition.evidence import EvidenceAtom, VerificationGap, detect_contradictions
from expedition.plan import SFHA_ZONES, MissionPlan


def _field(atoms: list[EvidenceAtom], field_id: str) -> EvidenceAtom | None:
    for atom in atoms:
        if atom.field_id == field_id:
            return atom
    return None


def _route_time_complete(plan: MissionPlan, candidate_id: str, atoms: list[EvidenceAtom]) -> bool:
    expected = [
        anchor
        for anchor in plan.route_anchors
        if anchor.get("id") != candidate_id
    ]
    if not expected:
        return True
    facts = {
        (atom.support or {}).get("destination_id")
        for atom in atoms
        if atom.field_id == "route_duration_s" and atom.kind == "FACT"
    }
    return all(anchor.get("id") in facts for anchor in expected)


def _sfha(atoms: list[EvidenceAtom]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    zone = _field(atoms, "fema_flood_zone")
    poly = _field(atoms, "within_floodplain_polygon")
    hit = False
    if zone and zone.kind == "FACT" and zone.status in {"live", "replay"}:
        if str(zone.value).upper() in SFHA_ZONES:
            hit = True
            reasons.append("mapped_sfha")
    if poly and poly.kind == "FACT" and poly.status in {"live", "replay"}:
        if poly.value is True:
            hit = True
            if "mapped_sfha" not in reasons:
                reasons.append("mapped_sfha")
    return hit, reasons


def judge(
    plan: MissionPlan,
    candidate_id: str,
    atoms: list[EvidenceAtom],
    *,
    candidate: dict | None = None,
) -> dict:
    reasons: list[str] = []
    gaps: list[VerificationGap] = []
    blocking_unknown = False
    candidate = candidate or {}

    if plan.site_form != "either":
        observed_form = candidate.get("site_form")
        if observed_form in {"existing_asset", "developable_land"}:
            if observed_form != plan.site_form:
                reasons.append("site_form_mismatch")
        else:
            blocking_unknown = True
            gaps.append(
                VerificationGap(
                    gap_id=f"{candidate_id}:site_form",
                    candidate_id=candidate_id,
                    question_id="site_form",
                    missing_authority="candidate_site_form",
                    blocking=True,
                    atom_ids=[],
                    action="Confirm whether the candidate is an existing asset or developable land.",
                )
            )

    for configured, candidate_key, question_id, action in (
        (
            plan.size_band,
            "size_band",
            "site_size",
            f"Verify the candidate against the declared size band {plan.size_band}.",
        ),
        (
            plan.budget_band,
            "budget_band",
            "acquisition_budget",
            f"Obtain authorized price evidence for the declared budget band {plan.budget_band}.",
        ),
    ):
        if configured == "flexible":
            continue
        if candidate.get(candidate_key) != configured:
            blocking_unknown = True
            gaps.append(
                VerificationGap(
                    gap_id=f"{candidate_id}:{question_id}",
                    candidate_id=candidate_id,
                    question_id=question_id,
                    missing_authority=question_id,
                    blocking=True,
                    atom_ids=[],
                    action=action,
                )
            )

    required_failed = [
        a
        for a in atoms
        if a.decision_effect in {"VETO", "GATE"}
        and (
            a.kind in {"FAILED", "UNKNOWN"}
            or a.status in {"failed", "blocked", "stale", "partial"}
        )
    ]
    if required_failed:
        blocking_unknown = True
        for a in required_failed:
            gaps.append(
                VerificationGap(
                    gap_id=f"{candidate_id}:{a.field_id}:failed",
                    candidate_id=candidate_id,
                    question_id=a.question_id,
                    missing_authority=a.source,
                    blocking=True,
                    atom_ids=[a.atom_id],
                    action=f"Retry or obtain {a.field_id} from {a.source}.",
                )
            )

    if plan.flood_intolerant:
        zone = _field(atoms, "fema_flood_zone")
        poly = _field(atoms, "within_floodplain_polygon")
        if (zone and zone.kind == "FAILED") or (poly and poly.kind == "FAILED"):
            blocking_unknown = True
        hit, sfha_reasons = _sfha(atoms)
        if hit:
            reasons.extend(sfha_reasons)

    if plan.require_cultivated:
        cult = _field(atoms, "is_cultivated")
        if cult is None or cult.kind in {"FAILED", "UNKNOWN", "ABSENT"} or cult.status not in {"live", "replay"}:
            blocking_unknown = True
            gaps.append(
                VerificationGap(
                    gap_id=f"{candidate_id}:cultivated:unknown",
                    candidate_id=candidate_id,
                    question_id="farm.cultivated",
                    missing_authority="USDA_CDL",
                    blocking=True,
                    atom_ids=[cult.atom_id] if cult else [],
                    action="Confirm cultivation with a current CDL or field visit.",
                )
            )
        elif cult.kind == "FACT" and cult.value is False:
            reasons.append("not_cultivated")

    for required, field_id, reason, authority, action in (
        (plan.require_water_service, "within_water_service_area", "outside_mapped_water_service", "water_service_map", "Confirm current service-area coverage and capacity with the provider."),
        (plan.require_sewer_service, "within_sewer_service_area", "outside_mapped_sewer_service", "sewer_service_map", "Confirm current service-area coverage and capacity with the provider."),
        (plan.require_fiber_service, "fiber_broadband_available", "fiber_not_observed", "broadband_provider", "Obtain a carrier availability letter; mapped broadband is not enterprise redundancy."),
    ):
        if not required:
            continue
        atom = _field(atoms, field_id)
        if atom is None or not atom.usable_as_pass:
            blocking_unknown = True
            gaps.append(VerificationGap(
                gap_id=f"{candidate_id}:{field_id}:unknown",
                candidate_id=candidate_id,
                question_id=field_id,
                missing_authority=authority,
                blocking=True,
                atom_ids=[atom.atom_id] if atom else [],
                action=action,
            ))
        elif atom.value is not True:
            reasons.append(reason)

    route_atoms = {
        (atom.support or {}).get("destination_id"): atom
        for atom in atoms
        if atom.field_id == "route_duration_s"
        and atom.kind == "FACT"
        and atom.status in {"live", "replay"}
    }
    for anchor in plan.route_anchors:
        maximum = anchor.get("max_minutes")
        if maximum is None:
            continue
        route = route_atoms.get(anchor.get("id"))
        if route is not None and isinstance(route.value, (int, float)):
            if float(route.value) > float(maximum) * 60:
                reasons.append(f"route_time_exceeds_max:{anchor['id']}")

    elev = _field(atoms, "elevation")
    nasa = _field(atoms, "nasadem_elevation")
    if (
        elev
        and nasa
        and isinstance(elev.value, (int, float))
        and isinstance(nasa.value, (int, float))
        and abs(float(elev.value) - float(nasa.value)) >= 1.0
    ):
        gaps.append(
            VerificationGap(
                gap_id=f"{candidate_id}:dem_disagreement",
                candidate_id=candidate_id,
                question_id="hazards.elevation_disagreement",
                missing_authority="licensed_survey",
                blocking=False,
                atom_ids=[elev.atom_id, nasa.atom_id],
                action="Commission a survey. Do not pick the favorable DEM.",
            )
        )

    jrc = _field(atoms, "jrc_monthly_water_freq")
    if jrc and isinstance(jrc.value, dict):
        latest = jrc.value.get("latest_freq_2021") or 0
        base = jrc.value.get("baseline_freq_1985_1999") or 0
        if jrc.value.get("breakpoint_year") and latest >= max(3 * base, base + 0.05):
            # Same JRC family as Mireye permanence — inform / deepen, not a second veto.
            if "mapped_sfha" not in reasons and plan.flood_intolerant:
                gaps.append(
                    VerificationGap(
                        gap_id=f"{candidate_id}:jrc_wetting",
                        candidate_id=candidate_id,
                        question_id="hazards.flood_history",
                        missing_authority="floodplain_administrator",
                        blocking=False,
                        atom_ids=[jrc.atom_id],
                        action="Ask the floodplain administrator about observed wetting since the JRC breakpoint.",
                    )
                )

    atom_by_id = {atom.atom_id: atom for atom in atoms}
    for contradiction in detect_contradictions(atoms):
        if contradiction.resolution != "verification_gap":
            continue
        mandatory = any(
            atom_by_id[atom_id].decision_effect in {"VETO", "GATE"}
            for atom_id in contradiction.atom_ids
            if atom_id in atom_by_id
        )
        blocking_unknown = blocking_unknown or mandatory
        gaps.append(VerificationGap(
            gap_id=f"{candidate_id}:{contradiction.contradiction_id}",
            candidate_id=candidate_id,
            question_id=contradiction.question_id,
            missing_authority="contradiction_resolution",
            blocking=mandatory,
            atom_ids=contradiction.atom_ids,
            action="Reconcile the conflicting authoritative values without selecting the favorable answer.",
        ))

    for gap_name in plan.gaps_always:
        if gap_name == "route_time" and _route_time_complete(plan, candidate_id, atoms):
            continue
        gaps.append(
            VerificationGap(
                gap_id=f"{candidate_id}:{gap_name}",
                candidate_id=candidate_id,
                question_id=gap_name,
                missing_authority=gap_name,
                blocking=True,
                atom_ids=[],
                action=_action_for(gap_name),
            )
        )

    if reasons:
        verdict = "reject"
    elif blocking_unknown or any(g.blocking for g in gaps):
        verdict = "conditional"
    else:
        verdict = "strong_fit"

    # Strong Fit is almost never honest without availability / capacity artifacts.
    if verdict == "strong_fit" and any(g.blocking for g in gaps):
        verdict = "conditional"

    return {
        "candidate_id": candidate_id,
        "verdict": verdict,
        "reasons": reasons,
        "gaps": [g.to_dict() for g in gaps],
        "inform": _inform(atoms),
    }


def _inform(atoms: list[EvidenceAtom]) -> dict:
    out = {}
    for atom in atoms:
        if atom.decision_effect == "INFORM" and atom.kind in {"FACT", "PROXY"}:
            out[atom.field_id] = atom.value
        if atom.field_id == "is_cultivated" and atom.value is True:
            out["cultivated"] = True
        if atom.field_id == "dominant_crop_5y" and atom.value:
            out["dominant_crop_5y"] = atom.value
    return out


def _action_for(gap: str) -> str:
    return {
        "market_availability": "Confirm sale or lease with the owner or a licensed broker. This pin is not a listing.",
        "electrical_capacity": "Request a utility or ISO deliverable-MW letter. Substation distance is not capacity.",
        "truck_ingress": "Have a civil/traffic review confirm driveway, turn radius, and legal truck route.",
        "zoning_permission": "Read the current local ordinance and overlays with counsel. A label is not approval.",
        "water_right": "Obtain the state water-right or irrigation-district artifact.",
        "yield": "Yield is not inferred from CDL or rainfall.",
        "enterprise_fiber_redundancy": "Request a carrier diversity letter. Provider count is not redundancy.",
        "water_capacity": "Request a provider will-serve for process water.",
        "route_time": "Re-run Routes to the confirmed customer or port anchors.",
        "site_size": "Verify candidate size using authorized site or building geometry.",
        "acquisition_budget": "Obtain authorized sale or lease price evidence.",
        "concept_fit": (
            "FIT stays a Verification Gap: no independently licensed parcel envelope. "
            "The warehouse mass is a visual concept, not a fit test."
        ),
    }.get(gap, f"Obtain an authoritative artifact for {gap}.")
