"""Warehouse Concept Test. Local meters only. No Google tiles. No parcel fetch."""

from __future__ import annotations

import json
from pathlib import Path

ASSET = Path(__file__).resolve().parent / "assets" / "warehouse.gltf"


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
        "cases": rows,
        "claim": {
            "FUTURE": "visual_concept" if passed else "deferred",
            "FIT": "deferred",
            "fit_reason": "No independently licensed parcel or constraint polygon on the default path.",
            "future_note": (
                "Parametric box may be shown as a labeled visual concept after this test."
                if passed
                else "Do not show FUTURE."
            ),
        },
    }
