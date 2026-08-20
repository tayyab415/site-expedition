"""Constrained Source Scout. Named authorities for open Verification Gaps.

This is not live source discovery, scraping, or package installation.
"""

from __future__ import annotations

from expedition.adapters.witness import fact_atom, support
from expedition.evidence import utc_now


TRANSFORM = "source-scout-constrained-v1"
CATALOG_URL = "https://www.mireye.com"

# Only these authorities may be proposed. Keys match verdict gap question_ids.
CATALOG: dict[str, dict] = {
    "market_availability": {
        "authority": "licensed listing / broker confirmation",
        "action": "Obtain a current listing identity from a licensed broker or authorized inventory feed. Assessor records and vacant appearance are not Market Availability.",
        "urls": ["https://www.nar.realtor/"],
    },
    "electrical_capacity": {
        "authority": "serving electric utility large-load / will-serve study",
        "action": "Ask the mapped serving utility for a large-load or will-serve study. Substation distance is not deliverable MW.",
        "urls": ["https://www.eia.gov/electricity/data/eia861/"],
    },
    "truck_ingress": {
        "authority": "site civil / local truck-route ordinance",
        "action": "Commission a civil turning-template review and confirm local truck-route and access-control rules. Route time is not ingress.",
        "urls": ["https://ops.fhwa.dot.gov/freight/"],
    },
    "zoning_permission": {
        "authority": "local planning / zoning administrator",
        "action": "Confirm the intended use with the local planning authority. A land-cover class is not entitlement.",
        "urls": ["https://www.planning.org/"],
    },
    "water_right": {
        "authority": "state water-right registry",
        "action": "Look up the legal water right in the state registry. Green pixels and rainfall history cannot grant a right.",
        "urls": ["https://www.tceq.texas.gov/permitting/water_rights"],
    },
    "yield": {
        "authority": "agronomic trial / operator records",
        "action": "Obtain operator yield records or a crop-specific agronomic interpretation. CDL class is not yield.",
        "urls": ["https://www.nass.usda.gov/"],
    },
    "enterprise_fiber_redundancy": {
        "authority": "enterprise fiber quote / diverse-route letter",
        "action": "Request a carrier-diverse enterprise quote. Mass-market broadband availability is not redundant fiber.",
        "urls": ["https://broadbandmap.fcc.gov/"],
    },
    "water_capacity": {
        "authority": "water / wastewater provider commitment",
        "action": "Obtain a will-serve or capacity letter from the water and wastewater providers. Service-area membership is not committed volume.",
        "urls": ["https://www.epa.gov/waterdata"],
    },
    "route_time": {
        "authority": "measured Routes matrix to declared anchors",
        "action": "Re-run Routes to the declared anchors or verify drive time with the operator. Straight-line road distance is a different metric.",
        "urls": ["https://developers.google.com/maps/documentation/routes"],
    },
    "concept_fit": {
        "authority": "licensed survey / civil envelope",
        "action": "Fit the concept to an independently licensed parcel and constraint polygon. The assumed pad is not FIT.",
        "urls": [],
    },
    "environmental_phase_i": {
        "authority": "Phase I Environmental Site Assessment",
        "action": "Commission a current ASTM Phase I ESA. An EPA RMP proximity hit is a lead, not a clean-site conclusion.",
        "urls": ["https://echo.epa.gov/"],
    },
    "hazards.elevation_disagreement": {
        "authority": "licensed survey / USGS 3DEP site control",
        "action": "Do not pick the favorable DEM. Obtain surveyed elevation or an authoritative 3DEP site control check.",
        "urls": ["https://www.usgs.gov/3d-elevation-program"],
    },
}


def source_scout(
    *,
    candidate_id: str,
    lat: float,
    lng: float,
    gaps: list[dict],
    live: bool = False,
) -> tuple[list, dict]:
    recommendations = []
    seen = set()
    for gap in gaps or []:
        question_id = gap.get("question_id")
        if question_id in seen or question_id not in CATALOG:
            continue
        seen.add(question_id)
        entry = CATALOG[question_id]
        recommendations.append({
            "gap_id": gap.get("gap_id") or question_id,
            "question_id": question_id,
            "authority": entry["authority"],
            "action": entry["action"],
            "urls": list(entry["urls"]),
            "blocking": bool(gap.get("blocking")),
        })
    fetched = utc_now()
    payload = {
        "source_scout": {
            "constrained": True,
            "live_discovery": False,
            "recommendations": recommendations,
        }
    }
    geom = support(
        lat,
        lng,
        radius_m=None,
        purpose="",
        extra="source-scout-constrained-catalog",
    )
    atom = fact_atom(
        candidate_id=candidate_id,
        question_id="diligence.source_scout",
        field_id="source_scout_authorities",
        value=payload["source_scout"],
        unit=None,
        source="constrained source catalog",
        source_url=CATALOG_URL,
        source_family="SCOUT_CATALOG",
        independence_group="SCOUT_CATALOG",
        support_geom=geom,
        observed_at=None,
        fetched_at=fetched,
        dataset_vintage=TRANSFORM,
        transform=TRANSFORM,
        live=False,
        notes=(
            "Named responsible authorities for open Verification Gaps. "
            "Constrained catalog only — no live crawl, scrape, or package install."
        ),
        window="",
        kind="PRESENTATION",
        authority="none",
        confidence="high",
        decision_effect="NONE",
    )
    return [atom], payload
