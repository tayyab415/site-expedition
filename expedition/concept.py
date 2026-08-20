"""Concept Studio. Parametric presets and schematic interiors.

FUTURE is a labeled visual concept. Interiors are schematic programs, not
surveys. FIT stays deferred. Conceptual DXF/IFC is for coordination. It is
not stamped, not permit-ready, and not an existing-building reconstruction.
"""

from __future__ import annotations

import json
from pathlib import Path

ASSET = Path(__file__).resolve().parent / "assets" / "warehouse.gltf"

INTERIOR_NOTE = (
    "Schematic interior program. Not a survey, not existing-building "
    "reconstruction from drawings, and not a permit."
)
PERMIT_NOTE = (
    "Parametric massing. Conceptual CAD is for coordination. "
    "Not stamped, not permit-ready, and not FIT."
)


def _cad(studio_id: str) -> dict:
    from expedition.studio import get_preset

    row = get_preset(studio_id)
    foot = row["footprint_m"]
    return {
        "studio_id": studio_id,
        "dxf": f"/assets/presets/{studio_id}.dxf",
        "ifc": f"/assets/presets/{studio_id}.ifc",
        "gltf": f"/assets/presets/{studio_id}.gltf",
        "gltf_interiors": f"/assets/presets/{studio_id}-interiors.gltf",
        "native_length_m": float(foot["length"]),
        "native_width_m": float(foot["width"]),
        "native_height_m": float(foot["height"]),
        "claim": "conceptual_not_permit_ready",
    }


def _room(room_id: str, label: str, x: float, y: float, w: float, h: float) -> dict:
    return {"id": room_id, "label": label, "x": x, "y": y, "w": w, "h": h}


PRESETS: dict[str, dict] = {
    "warehouse-cross-dock": {
        "id": "warehouse-cross-dock",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Cross-dock warehouse",
        "length_m": 80.0,
        "width_m": 40.0,
        "height_m": 10.0,
        "setback_m": 10.0,
        "dock_m": {"length": 24.0, "width": 12.0, "height": 1.4},
        "bays": 6,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("cross_dock"),
        "interior": [
            _room("docks", "Dock bays", 0.04, 0.78, 0.92, 0.18),
            _room("aisles", "Rack aisles", 0.08, 0.18, 0.60, 0.56),
            _room("staging", "Staging", 0.70, 0.18, 0.22, 0.56),
            _room("office", "Office", 0.72, 0.04, 0.22, 0.12),
            _room("restroom", "Restrooms", 0.56, 0.04, 0.14, 0.12),
        ],
        "assumptions": [
            "no setbacks from ordinance",
            "dock/yard schematic, not civil design",
            "interior is a program diagram",
            "not permit-ready",
        ],
    },
    "warehouse-bulk": {
        "id": "warehouse-bulk",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Bulk storage",
        "length_m": 120.0,
        "width_m": 60.0,
        "height_m": 12.0,
        "setback_m": 12.0,
        "dock_m": {"length": 18.0, "width": 10.0, "height": 1.4},
        "bays": 4,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("bulk_storage"),
        "interior": [
            _room("docks", "Limited docks", 0.30, 0.82, 0.40, 0.14),
            _room("bulk", "Bulk floor", 0.08, 0.16, 0.84, 0.64),
            _room("office", "Office", 0.74, 0.04, 0.18, 0.10),
        ],
        "assumptions": [
            "deeper floor, fewer docks than cross-dock",
            "interior is a program diagram",
            "not permit-ready",
        ],
    },
    "warehouse-last-mile": {
        "id": "warehouse-last-mile",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Last-mile 60×30",
        "length_m": 60.0,
        "width_m": 30.0,
        "height_m": 8.0,
        "setback_m": 8.0,
        "dock_m": {"length": 18.0, "width": 10.0, "height": 1.2},
        "bays": 6,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("last_mile"),
        "interior": [
            _room("office", "Dispatch", 0.04, 0.04, 0.36, 0.22),
            _room("van", "Van docks", 0.44, 0.04, 0.52, 0.22),
            _room("sort", "Sort", 0.06, 0.30, 0.88, 0.36),
            _room("outbound", "Outbound", 0.06, 0.70, 0.88, 0.26),
        ],
        "assumptions": [
            "van courts are not a truck court",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "warehouse-cold": {
        "id": "warehouse-cold",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Cold storage 80×50",
        "length_m": 80.0,
        "width_m": 50.0,
        "height_m": 12.0,
        "setback_m": 10.0,
        "dock_m": {"length": 24.0, "width": 12.0, "height": 1.4},
        "bays": 6,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("cold_storage"),
        "interior": [
            _room("office", "Office", 0.04, 0.04, 0.22, 0.16),
            _room("dock", "Tempered docks", 0.30, 0.04, 0.66, 0.16),
            _room("cooler", "Cooler", 0.06, 0.24, 0.42, 0.56),
            _room("freezer", "Freezer", 0.52, 0.24, 0.42, 0.56),
            _room("plant", "Machine room", 0.78, 0.82, 0.18, 0.14),
        ],
        "assumptions": [
            "temperatures are program labels, not engineered",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "warehouse-flex": {
        "id": "warehouse-flex",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Light industrial flex 70×40",
        "length_m": 70.0,
        "width_m": 40.0,
        "height_m": 8.0,
        "setback_m": 8.0,
        "dock_m": {"length": 18.0, "width": 10.0, "height": 1.2},
        "bays": 4,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("light_flex"),
        "interior": [
            _room("office", "Front office", 0.06, 0.04, 0.88, 0.24),
            _room("shop", "Shop / flex", 0.06, 0.32, 0.88, 0.36),
            _room("warehouse", "Warehouse", 0.06, 0.72, 0.88, 0.24),
        ],
        "assumptions": [
            "office bar is one story",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "warehouse-fulfillment": {
        "id": "warehouse-fulfillment",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "High-cube fulfillment 100×60",
        "length_m": 100.0,
        "width_m": 60.0,
        "height_m": 14.0,
        "setback_m": 12.0,
        "dock_m": {"length": 28.0, "width": 14.0, "height": 1.4},
        "bays": 12,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("high_cube_fulfillment"),
        "interior": [
            _room("office", "Offices", 0.04, 0.04, 0.18, 0.14),
            _room("inbound", "Inbound", 0.26, 0.04, 0.70, 0.14),
            _room("pick", "Pick modules", 0.06, 0.22, 0.88, 0.46),
            _room("pack", "Pack", 0.06, 0.70, 0.88, 0.14),
            _room("outbound", "Outbound", 0.06, 0.86, 0.88, 0.10),
        ],
        "assumptions": [
            "mezzanine is not structural design",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "warehouse-terminal": {
        "id": "warehouse-terminal",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Truck terminal 90×45",
        "length_m": 90.0,
        "width_m": 45.0,
        "height_m": 8.0,
        "setback_m": 10.0,
        "dock_m": {"length": 30.0, "width": 14.0, "height": 1.4},
        "bays": 16,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("truck_terminal"),
        "interior": [
            _room("yard_office", "Yard office", 0.04, 0.04, 0.22, 0.16),
            _room("docks", "Cross-dock floor", 0.06, 0.24, 0.88, 0.56),
            _room("service", "Service bay", 0.74, 0.82, 0.22, 0.14),
        ],
        "assumptions": [
            "turning templates are not simulated",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "warehouse-hybrid": {
        "id": "warehouse-hybrid",
        "mission": "warehouse",
        "family": "warehouse",
        "title": "Office / warehouse hybrid 50×36",
        "length_m": 50.0,
        "width_m": 36.0,
        "height_m": 8.0,
        "setback_m": 8.0,
        "dock_m": {"length": 16.0, "width": 10.0, "height": 1.2},
        "bays": 3,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("office_warehouse_hybrid"),
        "interior": [
            _room("lobby", "Lobby", 0.04, 0.04, 0.28, 0.22),
            _room("office", "Office bar", 0.36, 0.04, 0.60, 0.22),
            _room("warehouse", "Warehouse", 0.06, 0.30, 0.88, 0.66),
        ],
        "assumptions": [
            "second office story is not modeled",
            "interior is a program diagram",
            "conceptual CAD, not stamped",
        ],
    },
    "farm-packing": {
        "id": "farm-packing",
        "mission": "farm",
        "family": "farm",
        "title": "Packing shed",
        "length_m": 48.0,
        "width_m": 24.0,
        "height_m": 7.0,
        "setback_m": 8.0,
        "dock_m": {"length": 12.0, "width": 8.0, "height": 1.2},
        "bays": 2,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("packing_shed"),
        "interior": [
            _room("receiving", "Receiving", 0.06, 0.70, 0.88, 0.24),
            _room("line", "Packing line", 0.06, 0.22, 0.58, 0.44),
            _room("cold", "Cold room", 0.68, 0.22, 0.26, 0.44),
            _room("office", "Shed office", 0.68, 0.06, 0.26, 0.12),
        ],
        "assumptions": [
            "shed massing on an assumed pad",
            "interior is a program diagram",
            "not a barn survey or a permit",
        ],
    },
    "home-massing": {
        "id": "home-massing",
        "mission": "home",
        "family": "home",
        "title": "House massing",
        "length_m": 16.0,
        "width_m": 12.0,
        "height_m": 6.0,
        "setback_m": 6.0,
        "dock_m": None,
        "bays": 0,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("home_massing"),
        "interior": [
            _room("living", "Living", 0.08, 0.52, 0.54, 0.40),
            _room("kitchen", "Kitchen", 0.64, 0.52, 0.28, 0.40),
            _room("bed-a", "Bedroom", 0.08, 0.08, 0.40, 0.38),
            _room("bed-b", "Bedroom", 0.52, 0.08, 0.40, 0.38),
        ],
        "assumptions": [
            "simple residential massing",
            "interior is a program diagram, not a floor plan from drawings",
            "not permit-ready",
        ],
    },
    "dc-hall": {
        "id": "dc-hall",
        "mission": "data_center",
        "family": "data_center",
        "title": "Hall and office",
        "length_m": 48.0,
        "width_m": 32.0,
        "height_m": 8.0,
        "setback_m": 12.0,
        "dock_m": {"length": 16.0, "width": 10.0, "height": 1.4},
        "bays": 2,
        "asset": "/assets/warehouse.gltf",
        "cad": _cad("data_hall_shell"),
        "interior": [
            _room("hall", "White space", 0.08, 0.18, 0.62, 0.70),
            _room("electrical", "Electrical", 0.72, 0.18, 0.20, 0.34),
            _room("office", "Office", 0.72, 0.56, 0.20, 0.32),
            _room("entry", "Entry", 0.08, 0.04, 0.28, 0.12),
        ],
        "assumptions": [
            "hall massing, not a cooling design",
            "interior is a program diagram",
            "not permit-ready and not a MW claim",
        ],
    },
}

DEFAULT_PRESET = {
    "warehouse": "warehouse-cross-dock",
    "farm": "farm-packing",
    "home": "home-massing",
    "data_center": "dc-hall",
    "custom": "warehouse-cross-dock",
}


def list_presets(mission: str | None = None) -> list[dict]:
    rows = [dict(row) for row in PRESETS.values()]
    if mission:
        key = "warehouse" if mission == "custom" else mission
        rows = [row for row in rows if row["mission"] == key]
    return rows


def default_preset_id(mission: str) -> str:
    return DEFAULT_PRESET.get(mission, "warehouse-cross-dock")


def load_preset(preset_id: str | None = None, *, mission: str = "warehouse") -> dict:
    chosen = preset_id or default_preset_id(mission)
    if chosen not in PRESETS:
        raise KeyError(chosen)
    row = dict(PRESETS[chosen])
    expected = "warehouse" if mission == "custom" else mission
    if row["mission"] != expected:
        raise KeyError(f"preset {chosen} is not for mission {mission}")
    if chosen == "warehouse-cross-dock":
        foot = load_footprint()
        row["length_m"] = foot["length_m"]
        row["width_m"] = foot["width_m"]
        row["height_m"] = foot["height_m"]
        row["rights"] = foot.get("rights")
    row["interior_claim"] = "schematic_program"
    row["interior_note"] = INTERIOR_NOTE
    row["permit_note"] = PERMIT_NOTE
    if row.get("cad"):
        row["asset"] = row["cad"]["gltf"]
    return row


def load_footprint() -> dict:
    gltf = json.loads(ASSET.read_text())
    extras = gltf.get("extras") or {}
    foot = extras.get("footprint_m") or {}
    return {
        "length_m": float(foot["length"]),
        "width_m": float(foot["width"]),
        "height_m": float(foot["height"]),
        "assumptions": list(extras.get("assumptions") or []),
        "rights": extras.get("rights"),
        "asset": "assets/warehouse.gltf",
    }


def _rotated_extent(length_m: float, width_m: float, heading_deg: float) -> tuple[float, float]:
    import math

    rad = math.radians(heading_deg)
    c, s = abs(math.cos(rad)), abs(math.sin(rad))
    return (length_m * c + width_m * s, length_m * s + width_m * c)


def place(footprint: dict, envelope: dict, *, heading_deg: float = 0.0, setback_m: float = 10.0) -> dict:
    """Axis-aligned envelope in local meters. Returns fit / conflict / ambiguous."""
    quality = envelope.get("quality") or "ok"
    ew = envelope.get("width_m")
    el = envelope.get("length_m")
    if quality == "low" or ew in (None, 0) or el in (None, 0):
        return {
            "result": "ambiguous",
            "reason": "boundary_low_quality",
            "envelope": envelope,
        }
    need_w, need_l = _rotated_extent(footprint["width_m"], footprint["length_m"], heading_deg)
    usable_w = float(ew) - 2 * setback_m
    usable_l = float(el) - 2 * setback_m
    if usable_w <= 0 or usable_l <= 0:
        return {
            "result": "conflict",
            "reason": "setback_consumes_envelope",
            "need_m": [need_w, need_l],
            "usable_m": [usable_w, usable_l],
            "envelope": envelope,
        }
    fits = need_w <= usable_w and need_l <= usable_l
    return {
        "result": "fit" if fits else "conflict",
        "reason": "fits_assumed_setback" if fits else "footprint_exceeds_envelope",
        "need_m": [round(need_w, 3), round(need_l, 3)],
        "usable_m": [round(usable_w, 3), round(usable_l, 3)],
        "heading_deg": heading_deg,
        "setback_m": setback_m,
        "envelope": envelope,
    }


CASES = [
    {
        "id": "positive",
        "expect": "fit",
        "heading_deg": 0,
        "envelope": {
            "id": "synthetic_pad_large",
            "width_m": 120,
            "length_m": 200,
            "quality": "ok",
            "source": "in_repo_synthetic_not_a_parcel",
        },
    },
    {
        "id": "known_conflict",
        "expect": "conflict",
        "heading_deg": 0,
        "envelope": {
            "id": "synthetic_pad_small",
            "width_m": 30,
            "length_m": 50,
            "quality": "ok",
            "source": "in_repo_synthetic_not_a_parcel",
        },
    },
    {
        "id": "ambiguous",
        "expect": "ambiguous",
        "heading_deg": 0,
        "envelope": {
            "id": "synthetic_pad_unknown",
            "width_m": None,
            "length_m": None,
            "quality": "low",
            "source": "in_repo_synthetic_not_a_parcel",
        },
    },
]


def run_concept_test() -> dict:
    foot = load_footprint()
    rows = []
    for case in CASES:
        got = place(foot, case["envelope"], heading_deg=case["heading_deg"])
        rows.append({
            "id": case["id"],
            "expect": case["expect"],
            "got": got["result"],
            "pass": got["result"] == case["expect"],
            "detail": got,
        })
    passed = all(r["pass"] for r in rows)
    return {
        "pass": passed,
        "google_tiles_used": False,
        "parcel_fields_used": False,
        "footprint": foot,
        "presets": list_presets(),
        "cases": rows,
        "claim": {
            "FUTURE": "visual_concept" if passed else "deferred",
            "FIT": "deferred",
            "INTERIOR": "schematic_program",
            "fit_reason": "No independently licensed parcel or constraint polygon on the default path.",
            "future_note": (
                "Parametric presets may be shown as labeled visual concepts, "
                "including schematic interiors and conceptual CAD. Not a permit."
                if passed
                else "Do not show FUTURE."
            ),
        },
    }
