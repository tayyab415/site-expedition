"""Concept Studio: architectural presets, interiors, and conceptual CAD.

These are coordination artifacts for FUTURE. They are not stamped drawings,
not an existing-building survey, and not a licensed-parcel FIT test.
"""

from __future__ import annotations

import base64
import json
import struct
from functools import lru_cache


# Local meters. Origin at footprint center. +X = width, +Y = up, +Z = length.
# Matches expedition/assets/warehouse.gltf for the default cross-dock.

def _room(room_id, name, x, z, w, d, h, color):
    return {
        "id": room_id,
        "name": name,
        "x": x,
        "z": z,
        "w": w,
        "d": d,
        "h": h,
        "color": color,
    }


PRESETS: tuple[dict, ...] = (
    {
        "id": "cross_dock",
        "name": "Cross-dock 80×40",
        "program": "warehouse",
        "footprint_m": {"length": 80, "width": 40, "height": 10},
        "setback_m": 10,
        "dock": {"count": 8, "side": "long", "length_m": 24, "width_m": 12, "height_m": 1.4},
        "rooms": (
            _room("office", "Office", -14, -34, 10, 10, 3.6, [0.22, 0.48, 0.78, 0.92]),
            _room("dock_n", "North docks", 0, -34, 36, 8, 4.2, [0.15, 0.15, 0.16, 0.9]),
            _room("dock_s", "South docks", 0, 34, 36, 8, 4.2, [0.15, 0.15, 0.16, 0.9]),
            _room("staging", "Staging", 0, 0, 36, 20, 6.0, [0.92, 0.62, 0.18, 0.88]),
            _room("storage", "Storage", 0, 16, 36, 20, 8.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "no ordinance setbacks applied",
            "dock/yard geometry is a program assumption",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "bulk_storage",
        "name": "Bulk storage 120×60",
        "program": "warehouse",
        "footprint_m": {"length": 120, "width": 60, "height": 12},
        "setback_m": 12,
        "dock": {"count": 4, "side": "short", "length_m": 28, "width_m": 14, "height_m": 1.4},
        "rooms": (
            _room("office", "Office", -24, -54, 12, 10, 3.6, [0.22, 0.48, 0.78, 0.92]),
            _room("dock", "Docks", 0, -54, 40, 10, 4.5, [0.15, 0.15, 0.16, 0.9]),
            _room("aisle", "Aisle", 0, 0, 12, 96, 8.0, [0.92, 0.62, 0.18, 0.88]),
            _room("storage_w", "West storage", -18, 0, 24, 96, 11.0, [0.85, 0.38, 0.08, 0.88]),
            _room("storage_e", "East storage", 18, 0, 24, 96, 11.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "rack layout not engineered",
            "fire walls and ESFR not modeled",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "last_mile",
        "name": "Last-mile 60×30",
        "program": "warehouse",
        "footprint_m": {"length": 60, "width": 30, "height": 8},
        "setback_m": 8,
        "dock": {"count": 6, "side": "long", "length_m": 18, "width_m": 10, "height_m": 1.2},
        "rooms": (
            _room("office", "Dispatch office", -9, -24, 12, 10, 3.4, [0.22, 0.48, 0.78, 0.92]),
            _room("van", "Van docks", 8, -24, 12, 10, 3.8, [0.15, 0.15, 0.16, 0.9]),
            _room("sort", "Sort", 0, -4, 26, 22, 5.0, [0.92, 0.62, 0.18, 0.88]),
            _room("outbound", "Outbound", 0, 20, 26, 16, 5.5, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "van courts not a truck court",
            "sort equipment not specified",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "cold_storage",
        "name": "Cold storage 80×50",
        "program": "warehouse",
        "footprint_m": {"length": 80, "width": 50, "height": 12},
        "setback_m": 10,
        "dock": {"count": 6, "side": "short", "length_m": 24, "width_m": 12, "height_m": 1.4},
        "rooms": (
            _room("office", "Office", -19, -34, 10, 10, 3.6, [0.22, 0.48, 0.78, 0.92]),
            _room("dock", "Tempered docks", 6, -34, 30, 10, 4.5, [0.15, 0.15, 0.16, 0.9]),
            _room("cooler", "Cooler", -12, 0, 22, 44, 8.0, [0.35, 0.72, 0.86, 0.9]),
            _room("freezer", "Freezer", 12, 0, 22, 44, 8.0, [0.55, 0.82, 0.95, 0.9]),
            _room("plant", "Machine room", 19, 32, 10, 12, 4.0, [0.55, 0.55, 0.2, 0.92]),
        ),
        "assumptions": [
            "insulation and refrigeration are program labels, not engineered",
            "temperature setpoints are not claimed",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "light_flex",
        "name": "Light industrial flex 70×40",
        "program": "warehouse",
        "footprint_m": {"length": 70, "width": 40, "height": 8},
        "setback_m": 8,
        "dock": {"count": 4, "side": "long", "length_m": 18, "width_m": 10, "height_m": 1.2},
        "rooms": (
            _room("office", "Front office", 0, -28, 36, 12, 3.6, [0.22, 0.48, 0.78, 0.92]),
            _room("shop", "Shop / flex", 0, 0, 36, 28, 6.0, [0.92, 0.62, 0.18, 0.88]),
            _room("warehouse", "Warehouse", 0, 26, 36, 16, 7.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "office bar is one story",
            "use split is a program assumption",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "high_cube_fulfillment",
        "name": "High-cube fulfillment 100×60",
        "program": "warehouse",
        "footprint_m": {"length": 100, "width": 60, "height": 14},
        "setback_m": 12,
        "dock": {"count": 12, "side": "long", "length_m": 28, "width_m": 14, "height_m": 1.4},
        "rooms": (
            _room("office", "Offices", -24, -44, 12, 10, 3.6, [0.22, 0.48, 0.78, 0.92]),
            _room("inbound", "Inbound", 0, -44, 48, 10, 6.0, [0.15, 0.15, 0.16, 0.9]),
            _room("pick", "Pick modules", 0, -8, 52, 50, 10.0, [0.92, 0.62, 0.18, 0.88]),
            _room("pack", "Pack", 0, 28, 52, 16, 6.0, [0.75, 0.45, 0.12, 0.9]),
            _room("outbound", "Outbound", 0, 44, 52, 10, 6.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "mezzanine and automation are not modeled as structure",
            "clear height is a program target",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "truck_terminal",
        "name": "Truck terminal 90×45",
        "program": "warehouse",
        "footprint_m": {"length": 90, "width": 45, "height": 8},
        "setback_m": 10,
        "dock": {"count": 16, "side": "long", "length_m": 30, "width_m": 14, "height_m": 1.4},
        "rooms": (
            _room("yard_office", "Yard office", -16, -39, 12, 10, 3.4, [0.22, 0.48, 0.78, 0.92]),
            _room("docks", "Cross-dock floor", 0, 0, 41, 70, 6.5, [0.92, 0.62, 0.18, 0.88]),
            _room("service", "Service bay", 16, 39, 12, 10, 5.0, [0.55, 0.55, 0.2, 0.92]),
        ),
        "assumptions": [
            "truck court and turning templates are not simulated",
            "door count is a program label",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "data_hall_shell",
        "name": "Data-hall shell 48×32",
        "program": "data_center",
        "footprint_m": {"length": 48, "width": 32, "height": 8},
        "setback_m": 8,
        "dock": {"count": 2, "side": "short", "length_m": 12, "width_m": 8, "height_m": 1.2},
        "rooms": (
            _room("office", "NOC / office", -12, -20, 8, 8, 3.4, [0.22, 0.48, 0.78, 0.92]),
            _room("mmr", "Meet-me", 12, -20, 8, 8, 3.4, [0.45, 0.35, 0.7, 0.92]),
            _room("hall", "White space", 0, 0, 28, 24, 6.0, [0.85, 0.88, 0.92, 0.9]),
            _room("electrical", "Electrical", -12, 18, 8, 10, 4.5, [0.55, 0.55, 0.2, 0.92]),
            _room("cooling", "Cooling", 12, 18, 8, 10, 4.5, [0.35, 0.72, 0.86, 0.9]),
        ),
        "assumptions": [
            "white space is a shell, not a fitted hall",
            "MW, PUE, and redundant plant are not claimed",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "farm_shop",
        "name": "Farm shop 40×24",
        "program": "farm",
        "footprint_m": {"length": 40, "width": 24, "height": 7},
        "setback_m": 6,
        "dock": {"count": 2, "side": "short", "length_m": 10, "width_m": 8, "height_m": 0.2},
        "rooms": (
            _room("office", "Farm office", -8, -16, 8, 8, 3.2, [0.22, 0.48, 0.78, 0.92]),
            _room("parts", "Parts", 8, -16, 8, 8, 3.2, [0.55, 0.55, 0.2, 0.92]),
            _room("shop", "Shop", 0, 2, 20, 16, 5.5, [0.92, 0.62, 0.18, 0.88]),
            _room("bay", "Equipment bay", 0, 16, 20, 8, 6.0, [0.15, 0.15, 0.16, 0.9]),
        ),
        "assumptions": [
            "not a barn as-built reconstruction",
            "equipment clearances are program labels",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "office_warehouse_hybrid",
        "name": "Office / warehouse hybrid 50×36",
        "program": "warehouse",
        "footprint_m": {"length": 50, "width": 36, "height": 8},
        "setback_m": 8,
        "dock": {"count": 3, "side": "short", "length_m": 16, "width_m": 10, "height_m": 1.2},
        "rooms": (
            _room("lobby", "Lobby", -12, -21, 10, 8, 3.4, [0.75, 0.78, 0.82, 0.92]),
            _room("office", "Office bar", 6, -21, 22, 8, 3.4, [0.22, 0.48, 0.78, 0.92]),
            _room("warehouse", "Warehouse", 0, 6, 32, 34, 7.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "second office story is not modeled",
            "hybrid split is a program assumption",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "packing_shed",
        "name": "Packing shed 48×24",
        "program": "farm",
        "footprint_m": {"length": 48, "width": 24, "height": 7},
        "setback_m": 8,
        "dock": {"count": 2, "side": "short", "length_m": 12, "width_m": 8, "height_m": 1.2},
        "rooms": (
            _room("receiving", "Receiving", 0.0, 15.4, 21.1, 11.5, 4.5, [0.15, 0.15, 0.16, 0.9]),
            _room("line", "Packing line", -3.6, -2.9, 13.9, 21.1, 5.0, [0.92, 0.62, 0.18, 0.88]),
            _room("cold", "Cold room", 7.4, -2.9, 6.2, 21.1, 4.0, [0.35, 0.72, 0.86, 0.9]),
            _room("office", "Shed office", 7.4, -18.2, 6.2, 5.8, 3.2, [0.22, 0.48, 0.78, 0.92]),
        ),
        "assumptions": [
            "shed massing on an assumed pad",
            "not a barn as-built reconstruction",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
    {
        "id": "home_massing",
        "name": "House massing 16×12",
        "program": "home",
        "footprint_m": {"length": 16, "width": 12, "height": 6},
        "setback_m": 6,
        "dock": {"count": 0, "side": "none", "length_m": 0, "width_m": 0, "height_m": 0},
        "rooms": (
            _room("living", "Living", -1.8, 3.5, 6.5, 6.4, 3.2, [0.22, 0.48, 0.78, 0.92]),
            _room("kitchen", "Kitchen", 3.4, 3.5, 3.4, 6.4, 3.2, [0.92, 0.62, 0.18, 0.88]),
            _room("bed_a", "Bedroom", -2.6, -3.7, 4.8, 6.1, 3.0, [0.75, 0.45, 0.12, 0.9]),
            _room("bed_b", "Bedroom", 2.6, -3.7, 4.8, 6.1, 3.0, [0.85, 0.38, 0.08, 0.88]),
        ),
        "assumptions": [
            "simple residential massing",
            "interior is a program diagram, not a floor plan from drawings",
            "conceptual CAD, not stamped, not permit-ready",
        ],
    },
)

DEFAULT_PRESET_ID = "cross_dock"
PRESET_BY_ID = {row["id"]: row for row in PRESETS}
SHELL_ORANGE = [1.0, 0.36, 0.08, 1.0]
SHELL_CUTAWAY = [1.0, 0.36, 0.08, 0.28]


def list_presets() -> list[dict]:
    return [public_preset(row["id"]) for row in PRESETS]


def get_preset(preset_id: str | None) -> dict:
    if not preset_id:
        return PRESET_BY_ID[DEFAULT_PRESET_ID]
    if preset_id not in PRESET_BY_ID:
        raise KeyError(preset_id)
    return PRESET_BY_ID[preset_id]


def public_preset(preset_id: str | None = None) -> dict:
    row = get_preset(preset_id)
    foot = row["footprint_m"]
    return {
        "id": row["id"],
        "name": row["name"],
        "program": row["program"],
        "length_m": foot["length"],
        "width_m": foot["width"],
        "height_m": foot["height"],
        "setback_m": row["setback_m"],
        "dock": dict(row["dock"]),
        "rooms": [
            {"id": room["id"], "name": room["name"], "w": room["w"], "d": room["d"], "h": room["h"]}
            for room in row["rooms"]
        ],
        "gltf": f"/assets/presets/{row['id']}.gltf",
        "gltf_interiors": f"/assets/presets/{row['id']}-interiors.gltf",
        "dxf": f"/assets/presets/{row['id']}.dxf",
        "ifc": f"/assets/presets/{row['id']}.ifc",
        "assumptions": list(row["assumptions"]),
        "rights": "original parametric concept, CC0",
        "claim": "visual_concept",
        "cad_claim": "conceptual_not_permit_ready",
    }


def footprint(preset_id: str | None = None) -> dict:
    row = get_preset(preset_id)
    foot = row["footprint_m"]
    return {
        "length_m": float(foot["length"]),
        "width_m": float(foot["width"]),
        "height_m": float(foot["height"]),
        "assumptions": list(row["assumptions"]),
        "rights": "original parametric concept, CC0",
        "asset": f"assets/presets/{row['id']}.gltf",
        "preset_id": row["id"],
    }


def gltf_bytes(preset_id: str | None = None, *, interiors: bool = False) -> bytes:
    return _gltf_text(preset_id or DEFAULT_PRESET_ID, interiors).encode()


def dxf_bytes(preset_id: str | None = None) -> bytes:
    return _dxf_text(preset_id or DEFAULT_PRESET_ID).encode()


def ifc_bytes(preset_id: str | None = None) -> bytes:
    return _ifc_text(preset_id or DEFAULT_PRESET_ID).encode()


@lru_cache(maxsize=32)
def _gltf_text(preset_id: str, interiors: bool) -> str:
    row = get_preset(preset_id)
    foot = row["footprint_m"]
    length, width, height = foot["length"], foot["width"], foot["height"]
    positions: list[float] = []
    normals: list[float] = []
    colors: list[float] = []
    indices: list[int] = []

    shell_color = SHELL_CUTAWAY if interiors else SHELL_ORANGE
    _box(
        positions,
        normals,
        colors,
        indices,
        0.0,
        height / 2.0,
        0.0,
        width / 2.0,
        height / 2.0,
        length / 2.0,
        shell_color,
        skip_top=interiors,
    )
    if interiors:
        for room in row["rooms"]:
            _box(
                positions,
                normals,
                colors,
                indices,
                room["x"],
                room["h"] / 2.0,
                room["z"],
                room["w"] / 2.0,
                room["h"] / 2.0,
                room["d"] / 2.0,
                room["color"],
                skip_top=False,
            )

    bin_blob = _pack_geometry(positions, normals, colors, indices)
    n_verts = len(positions) // 3
    pos_bytes = n_verts * 12
    color_off = pos_bytes * 2
    index_off = color_off + n_verts * 16
    xs = positions[0::3]
    ys = positions[1::3]
    zs = positions[2::3]
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "mireye-expedition-concept-studio",
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": row["id"], "mesh": 0}],
        "meshes": [{
            "name": row["id"],
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2},
                "indices": 3,
                "material": 0,
            }],
        }],
        "materials": [{
            "name": "concept_studio",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "metallicFactor": 0.05,
                "roughnessFactor": 0.72,
            },
            "alphaMode": "BLEND" if interiors else "OPAQUE",
            "doubleSided": True,
        }],
        "buffers": [{
            "uri": "data:application/octet-stream;base64," + base64.b64encode(bin_blob).decode("ascii"),
            "byteLength": len(bin_blob),
        }],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_bytes, "target": 34962},
            {"buffer": 0, "byteOffset": pos_bytes, "byteLength": pos_bytes, "target": 34962},
            {"buffer": 0, "byteOffset": color_off, "byteLength": n_verts * 16, "target": 34962},
            {"buffer": 0, "byteOffset": index_off, "byteLength": len(indices) * 2, "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": n_verts,
                "type": "VEC3",
                "max": [max(xs), max(ys), max(zs)],
                "min": [min(xs), min(ys), min(zs)],
            },
            {"bufferView": 1, "componentType": 5126, "count": n_verts, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": n_verts, "type": "VEC4"},
            {
                "bufferView": 3,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
                "max": [max(indices)],
                "min": [0],
            },
        ],
        "extras": {
            "rights": "original parametric concept, CC0",
            "preset_id": row["id"],
            "interiors": interiors,
            "cad_claim": "conceptual_not_permit_ready",
            "footprint_m": dict(foot),
            "assumptions": list(row["assumptions"]),
            "rooms": [dict(room) for room in row["rooms"]],
        },
    }
    return json.dumps(gltf, indent=2)


def _box(positions, normals, colors, indices, cx, cy, cz, hx, hy, hz, color, *, skip_top):
    faces = (
        ((1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 0, 0)),
        ((-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 0, 0)),
        ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1), (0, 1, 0)),
        ((-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1), (0, -1, 0)),
        ((-1, 1, 1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (0, 0, 1)),
        ((1, 1, -1), (1, -1, -1), (-1, -1, -1), (-1, 1, -1), (0, 0, -1)),
    )
    for i, face in enumerate(faces):
        if skip_top and i == 2:
            continue
        *corners, normal = face
        start = len(positions) // 3
        for sx, sy, sz in corners:
            positions.extend([cx + sx * hx, cy + sy * hy, cz + sz * hz])
            normals.extend(normal)
            colors.extend(color)
        indices.extend([start, start + 1, start + 2, start, start + 2, start + 3])


def _pack_geometry(positions, normals, colors, indices) -> bytes:
    pos = struct.pack(f"<{len(positions)}f", *positions)
    nor = struct.pack(f"<{len(normals)}f", *normals)
    col = struct.pack(f"<{len(colors)}f", *colors)
    idx = struct.pack(f"<{len(indices)}H", *indices)
    return pos + nor + col + idx


def _dxf_text(preset_id: str) -> str:
    row = get_preset(preset_id)
    foot = row["footprint_m"]
    half_w, half_l = foot["width"] / 2.0, foot["length"] / 2.0
    lines = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1014",
        "9", "$INSUNITS", "70", "6",
        "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES",
        "0", "TABLE", "2", "LAYER", "70", "5",
        *_layer("SHELL", 30),
        *_layer("INTERIOR", 50),
        *_layer("DOCK", 8),
        *_layer("NOTE", 7),
        "0", "ENDTAB", "0", "ENDSEC",
        "0", "SECTION", "2", "ENTITIES",
    ]
    lines.extend(_lwpoly("SHELL", [
        (-half_w, -half_l), (half_w, -half_l), (half_w, half_l), (-half_w, half_l),
    ]))
    for room in row["rooms"]:
        hx, hz = room["w"] / 2.0, room["d"] / 2.0
        cx, cz = room["x"], room["z"]
        lines.extend(_lwpoly("INTERIOR", [
            (cx - hx, cz - hz), (cx + hx, cz - hz), (cx + hx, cz + hz), (cx - hx, cz + hz),
        ]))
        lines.extend(_text("NOTE", cx, cz, room["name"]))
    lines.extend(_text("NOTE", 0, half_l + 4, f"{row['name']} — CONCEPTUAL CAD, NOT FOR PERMIT"))
    lines.extend(_text("NOTE", 0, -half_l - 4, "Not stamped. Not an existing-building survey. Not FIT."))
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(str(item) for item in lines) + "\n"


def _layer(name: str, color: int) -> list:
    return ["0", "LAYER", "2", name, "70", "0", "62", str(color), "6", "CONTINUOUS"]


def _lwpoly(layer: str, pts: list[tuple[float, float]]) -> list:
    out = ["0", "LWPOLYLINE", "8", layer, "90", str(len(pts)), "70", "1"]
    for x, y in pts:
        out.extend(["10", f"{x:.3f}", "20", f"{y:.3f}"])
    return out


def _text(layer: str, x: float, y: float, value: str) -> list:
    return [
        "0", "TEXT", "8", layer, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0",
        "40", "1.6", "1", value, "72", "1", "11", f"{x:.3f}", "21", f"{y:.3f}", "31", "0",
    ]


def _gid(tag: str) -> str:
    raw = "".join(ch for ch in tag if ch.isalnum())
    return (raw + "0" * 22)[:22]


def _ifc_text(preset_id: str) -> str:
    row = get_preset(preset_id)
    name = row["name"].replace("'", "")
    entities = [
        "#1=IFCORGANIZATION($,'Site Expedition',$,$,$);",
        "#2=IFCAPPLICATION(#1,'1.0','Concept Studio','expedition/studio.py');",
        "#3=IFCPERSON($,'Concept','Studio',$,$,$,$,$);",
        "#4=IFCPERSONANDORGANIZATION(#3,#1,$);",
        "#5=IFCOWNERHISTORY(#4,#2,$,.ADDED.,$,$,$,0);",
        "#6=IFCDIRECTION((1.,0.,0.));",
        "#7=IFCDIRECTION((0.,0.,1.));",
        "#8=IFCCARTESIANPOINT((0.,0.,0.));",
        "#9=IFCAXIS2PLACEMENT3D(#8,#7,#6);",
        "#10=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,$);",
        "#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);",
        "#12=IFCUNITASSIGNMENT((#11));",
        (
            f"#13=IFCPROJECT('{_gid('project')}',#5,'Concept Studio',"
            "'Conceptual coordination model. Not stamped. Not for permit.',$,$,$,(#10),#12);"
        ),
        "#14=IFCLOCALPLACEMENT($,#9);",
        (
            f"#15=IFCSITE('{_gid('site')}',#5,'Assumed pad',"
            "'Assumed pad. Not a licensed parcel.',$,#14,$,$,.ELEMENT.,$,$,$,$,$);"
        ),
        (
            f"#16=IFCBUILDING('{_gid('bldg')}',#5,'{name}',"
            "'Conceptual building mass. Not permit-ready.',$,#14,$,$,.ELEMENT.,$,$,$);"
        ),
        (
            f"#17=IFCBUILDINGSTOREY('{_gid('storey')}',#5,'Level 0',"
            "'Finish floor. Conceptual.',$,#14,$,$,.ELEMENT.,0.);"
        ),
        f"#18=IFCRELAGGREGATES('{_gid('rel1')}',#5,$,$,#13,(#15));",
        f"#19=IFCRELAGGREGATES('{_gid('rel2')}',#5,$,$,#15,(#16));",
        f"#20=IFCRELAGGREGATES('{_gid('rel3')}',#5,$,$,#16,(#17));",
    ]
    space_ids = []
    n = 21
    for room in row["rooms"]:
        sid = f"#{n}"
        entities.append(
            f"{sid}=IFCSPACE('{_gid(room['id'])}',#5,'{room['id']}',"
            f"'{room['name']}. Conceptual interior, not an as-built survey.',"
            "$,#14,$,$,.ELEMENT.,.INTERNAL.,$);"
        )
        space_ids.append(sid)
        n += 1
        entities.append(
            f"#{n}=IFCQUANTITYAREA('NetFloorArea','conceptual m2',$,{room['w'] * room['d']:.2f});"
        )
        n += 1
    contained = ",".join(space_ids)
    entities.append(
        f"#{n}=IFCRELCONTAINEDINSPATIALSTRUCTURE('{_gid('relspc')}',#5,$,$,({contained}),#17);"
    )
    n += 1
    p_permit, p_claim, pset = n, n + 1, n + 2
    entities.append(f"#{p_permit}=IFCPROPERTYSINGLEVALUE('PermitReady',$,IFCBOOLEAN(.F.),$);")
    entities.append(
        f"#{p_claim}=IFCPROPERTYSINGLEVALUE('CadClaim',$,IFCLABEL('conceptual_not_permit_ready'),$);"
    )
    entities.append(
        f"#{pset}=IFCPROPERTYSET('{_gid('pset')}',#5,'Pset_ConceptStudio',$,(#{p_permit},#{p_claim}));"
    )
    entities.append(
        f"#{pset + 1}=IFCRELDEFINESBYPROPERTIES('{_gid('relpset')}',#5,$,$,(#16),#{pset});"
    )
    header = [
        "ISO-10303-21;",
        "HEADER;",
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]','CONCEPTUAL NOT FOR PERMIT'),'2;1');",
        (
            f"FILE_NAME('{row['id']}.ifc','2026-08-19T00:00:00',('Site Expedition'),"
            "('Concept Studio'),'expedition/studio.py','Site Expedition Concept Studio',"
            "'conceptual coordination');"
        ),
        "FILE_SCHEMA(('IFC2X3'));",
        "ENDSEC;",
        "DATA;",
    ]
    return "\n".join(header + entities + ["ENDSEC;", "END-ISO-10303-21;"]) + "\n"
