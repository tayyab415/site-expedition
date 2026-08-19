"""Planning-board reconstruction payload. Presentation only — never scores."""

from __future__ import annotations

from expedition.concept import (
    INTERIOR_NOTE,
    PERMIT_NOTE,
    default_preset_id,
    list_presets,
    load_preset,
    run_concept_test,
)


def build_scene(*, mission: str, witnesses: list[dict]) -> dict:
    preset = load_preset(default_preset_id(mission), mission=mission)
    concept = run_concept_test() if mission in {"warehouse", "custom"} else None
    return {
        "google_tiles_used": False,
        "parcel_fields_used": False,
        "past": _past(mission, witnesses),
        "assumed_pad": _assumed_pad(preset),
        "future": _future(mission, concept, preset),
        "fit": {
            "claim": "deferred",
            "reason": (
                "No independently licensed parcel or constraint polygon on the default path. "
                "The pad is an assumption, not FIT."
            ),
        },
    }


def _past(mission: str, witnesses: list[dict]) -> dict:
    flood = next((row for row in witnesses if row.get("kind") == "flood_rewind"), None)
    farm = next((row for row in witnesses if row.get("kind") == "farm_history"), None)
    heat = next((row for row in witnesses if row.get("kind") == "observed_heat"), None)
    land = next((row for row in witnesses if row.get("kind") == "land_change"), None)
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
    if land:
        return {
            "kind": "land_change",
            "scores": False,
            "independence_group": land.get("independence_group") or "DYNAMIC_WORLD",
            "source": land.get("source") or "GOOGLE/DYNAMICWORLD/V1",
            "early_built_frac": land.get("early_built_frac"),
            "late_built_frac": land.get("late_built_frac"),
            "early_window": land.get("early_window"),
            "late_window": land.get("late_window"),
            "buffer_m": land.get("buffer_m"),
            "method": land.get("method"),
            "series": [],
            "note": (
                "Dynamic World thresholded top-1 built fraction"
                + (
                    f" in a {land.get('buffer_m')} m buffer. "
                    if land.get("buffer_m")
                    else ". "
                )
                + "INFORM only. Not scored. Not a construction permit or listing proof."
            ),
        }
    return {
        "kind": "none",
        "scores": False,
        "series": [],
        "note": "No temporal witness attached to this packet.",
    }


def _assumed_pad(preset: dict) -> dict:
    dock = preset.get("dock_m")
    return {
        "claim": "assumption",
        "fit_status": "deferred",
        "preset_id": preset["id"],
        "title": preset["title"],
        "length_m": preset["length_m"],
        "width_m": preset["width_m"],
        "height_m": preset["height_m"],
        "setback_m": preset.get("setback_m") or 10,
        "dock_m": dict(dock) if dock else None,
        "cad": preset.get("cad"),
        "assumptions": list(preset.get("assumptions") or []),
        "note": "Parametric pad. Not a licensed parcel and not FIT.",
    }


def _future(mission: str, concept: dict | None, preset: dict) -> dict:
    if mission in {"warehouse", "custom"}:
        claim = (concept or {}).get("claim") or {}
        if claim.get("FUTURE") != "visual_concept":
            return {
                "claim": "deferred",
                "reason": claim.get("future_note") or "Concept Test did not claim FUTURE.",
            }
    return {
        "claim": "visual_concept",
        "preset_id": preset["id"],
        "title": preset["title"],
        "asset": (preset.get("cad") or {}).get("gltf") or preset.get("asset") or "/assets/warehouse.gltf",
        "cad": preset.get("cad"),
        "length_m": preset["length_m"],
        "width_m": preset["width_m"],
        "height_m": preset["height_m"],
        "interior_claim": "schematic_program",
        "interior": list(preset.get("interior") or []),
        "presets": list_presets(mission),
        "note": f"{PERMIT_NOTE} {INTERIOR_NOTE}",
    }
