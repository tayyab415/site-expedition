"""Planning-board reconstruction payload. Presentation only — never scores."""

from __future__ import annotations

from expedition.concept import load_footprint, run_concept_test


def build_scene(*, mission: str, witnesses: list[dict]) -> dict:
    concept = run_concept_test() if mission == "warehouse" else None
    return {
        "google_tiles_used": False,
        "parcel_fields_used": False,
        "past": _past(mission, witnesses),
        "assumed_pad": _assumed_pad(mission),
        "future": _future(mission, concept),
        "fit": {
            "claim": "deferred",
            "reason": (
                "No independently licensed parcel or constraint polygon on the default path. "
                "The warehouse pad is an assumption, not FIT."
            ),
        },
    }


def _past(mission: str, witnesses: list[dict]) -> dict:
    flood = next((row for row in witnesses if row.get("kind") == "flood_rewind"), None)
    farm = next((row for row in witnesses if row.get("kind") == "farm_history"), None)
    heat = next((row for row in witnesses if row.get("kind") == "observed_heat"), None)
    if flood and flood.get("series"):
        return {
            "kind": "flood_rewind",
            "scores": False,
            "independence_group": "JRC_GSW",
            "source": flood.get("source") or "JRC/GSW1_4/MonthlyHistory",
            "breakpoint_year": flood.get("breakpoint_year"),
            "baseline_freq_1985_1999": flood.get("baseline_freq_1985_1999"),
            "latest_freq_2021": flood.get("latest_freq_2021"),
            "series": list(flood["series"]),
            "usgs_3dep_m": flood.get("usgs_3dep_m"),
            "nasadem_m": flood.get("nasadem_m"),
            "dem_delta_m": flood.get("dem_delta_m"),
            "note": (
                "JRC water-frequency witness. FEMA present-state still decides mapped SFHA. "
                + (
                    f"USGS 3DEP {flood['usgs_3dep_m']} m vs NASADEM {flood['nasadem_m']} m "
                    f"(Δ {flood['dem_delta_m']} m) — do not pick the favorable DEM."
                    if flood.get("dem_delta_m") is not None
                    else "Elevation-model disagreement is a verification gap, not a second veto."
                )
            ),
        }
    if farm:
        return {
            "kind": "farm_history",
            "scores": False,
            "independence_group": farm.get("independence_group") or "USDA_CDL",
            "source": farm.get("source") or "USDA/NASS/CDL",
            "years_observed": farm.get("years_observed"),
            "pattern": farm.get("pattern"),
            "classes": list(farm.get("classes") or []),
            "annual_mean_mm": farm.get("annual_mean_mm"),
            "series": [],
            "note": (
                "Annual CDL/CHIRPS summary from the bounded witness. "
                "No yearly map is invented when the replay payload has none."
            ),
        }
    if heat:
        return {
            "kind": "observed_heat",
            "scores": False,
            "independence_group": heat.get("independence_group") or "MODIS_LST",
            "source": heat.get("source") or "MODIS/061/MOD11A1",
            "window": heat.get("window"),
            "series": [],
            "note": "Observed summer heat window. Not a climate forecast.",
        }
    return {
        "kind": "none",
        "scores": False,
        "series": [],
        "note": "No temporal witness attached to this packet.",
    }


def _assumed_pad(mission: str) -> dict | None:
    if mission != "warehouse":
        return None
    foot = load_footprint()
    return {
        "claim": "assumption",
        "fit_status": "deferred",
        "length_m": foot["length_m"],
        "width_m": foot["width_m"],
        "height_m": foot["height_m"],
        "setback_m": 10,
        "dock_m": {"length": 24, "width": 12, "height": 1.4},
        "assumptions": list(foot.get("assumptions") or []),
        "note": "Parametric pad and dock. Not a licensed parcel and not FIT.",
    }


def _future(mission: str, concept: dict | None) -> dict:
    if mission != "warehouse":
        return {
            "claim": "deferred",
            "reason": "Warehouse Concept Studio is the only FUTURE visual concept in this MVP.",
        }
    claim = (concept or {}).get("claim") or {}
    if claim.get("FUTURE") != "visual_concept":
        return {
            "claim": "deferred",
            "reason": claim.get("future_note") or "Concept Test did not claim FUTURE.",
        }
    foot = load_footprint()
    return {
        "claim": "visual_concept",
        "asset": "/assets/warehouse.gltf",
        "length_m": foot["length_m"],
        "width_m": foot["width_m"],
        "height_m": foot["height_m"],
        "note": "Parametric warehouse box on an assumed pad. Not a permit. Does not score.",
    }
