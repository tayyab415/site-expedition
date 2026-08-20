"""Deterministic source router. Models may narrate this plan. They do not pick sources."""

from __future__ import annotations

from expedition.discovery.schema import SourcePlan, SourceSkip

SEED_BY_MISSION = {
    "warehouse": ("osm",),
    "custom": ("osm",),
    "farm": ("osm",),
    "home": ("osm",),
    "data_center": ("osm",),
}

HOP_BY_MISSION = {
    "warehouse": ("osm_power", "eia"),
    "custom": ("osm_power", "eia"),
    "data_center": ("osm_power", "uspvdb", "eia", "uswtdb"),
    "farm": ("uspvdb", "uswtdb"),
    "home": (),
}

PLACES_MISSIONS = frozenset({"warehouse", "farm", "data_center", "custom"})
RENTCAST_MISSIONS = frozenset({"home"})


def plan_sources(
    mission: str,
    scan_budget: str = "quick",
    *,
    allow_paid: bool = False,
    places_key: bool = False,
    rentcast_key: bool = False,
) -> SourcePlan:
    mission = (mission or "warehouse").replace(" ", "_").lower()
    scan_budget = (scan_budget or "quick").lower()
    if scan_budget not in {"quick", "standard", "deep"}:
        scan_budget = "quick"

    seeds = list(SEED_BY_MISSION.get(mission) or ("osm",))
    hops: list[str] = []
    skipped: list[SourceSkip] = []

    if scan_budget in {"standard", "deep"}:
        hops.extend(HOP_BY_MISSION.get(mission) or ())
        if mission in {"warehouse", "custom"}:
            seeds.append("echo")

    if mission in PLACES_MISSIONS:
        if allow_paid and places_key:
            seeds.append("places")
        else:
            reason = (
                "No Places-capable key in GOOGLE_PLACES_API_KEY or the Maps env file."
                if allow_paid
                else "Places is a paid Maps SKU; omitted unless --paid is on."
            )
            skipped.append(
                SourceSkip(
                    source="places",
                    reason=reason,
                    verdict="NO_KEY" if not places_key else "BLOCKED",
                )
            )

    if mission in RENTCAST_MISSIONS:
        if allow_paid and rentcast_key:
            seeds.append("rentcast")
        else:
            skipped.append(
                SourceSkip(
                    source="rentcast",
                    reason="No RENTCAST_API_KEY. Home LISTED inventory stays deferred.",
                    verdict="NO_KEY",
                )
            )

    skipped.extend(
        [
            SourceSkip(
                source="costar_crexi_loopnet",
                reason="No licensed commercial listing feed on this build.",
                verdict="PARTNER",
            ),
            SourceSkip(
                source="earth_engine_grid",
                reason="Dynamic World is a built/water sample on a known pin. It does not search a region for warehouses.",
                verdict="WITNESS_ONLY",
            ),
            SourceSkip(
                source="ask_google_earth",
                reason="Ask Google Earth is a browser chat. No export API, results cannot leave Earth.",
                verdict="BLOCKED",
            ),
            SourceSkip(
                source="google_tiles_extract",
                reason="Map Tiles / Photorealistic 3D forbid geodata extraction.",
                verdict="BLOCKED",
            ),
            SourceSkip(
                source="mireye_region_search",
                reason="Mireye has lookup/fetch/batch/proximity. It does not search a region for sites.",
                verdict="WITNESS_ONLY",
            ),
        ]
    )

    why = (
        f"{mission} {scan_budget}: seed {', '.join(seeds) or 'none'}; "
        f"hop {', '.join(hops) or 'none'}. "
        "OSM and USGS are map/facility features, not listings."
    )
    return SourcePlan(
        mission=mission,
        scan_budget=scan_budget,
        seeds=tuple(seeds),
        hops=tuple(hops),
        skipped=tuple(skipped),
        mireye_prefilter=scan_budget == "deep",
        why=why,
    )
