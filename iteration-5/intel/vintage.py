"""FEMA map vintage vs water-regime breakpoint — map_aged_out vs map_born_wrong."""

from __future__ import annotations

import re

# Heuristic study-year table keyed by trailing STUDY token in FEMA dataset_vintage.
# FEMA NFHL often exposes county + study ordinal, not an explicit effective date.
STUDY_YEAR_PROXY = {
    "STUDY1": 1995,
    "STUDY2": 2005,
    "STUDY3": 2015,
    "STUDY4": 2020,
}


def _parse_study_token(vintage: str | None) -> str | None:
    if not vintage:
        return None
    match = re.search(r"(STUDY\d+)", vintage.upper())
    return match.group(1) if match else None


def _infer_study_year(vintage: str | None) -> int | None:
    token = _parse_study_token(vintage)
    if not token:
        return None
    return STUDY_YEAR_PROXY.get(token)


def assess_vintage(record: dict, witness: dict, *, default_breakpoint: int = 2001) -> dict:
    """Compare FEMA panel vintage to the water-history breakpoint.

    Rule (documented):
      - Only applies when zone is AE and a water breakpoint exists.
      - ``map_aged_out``: inferred study year *before* the breakpoint — the panel
        froze while the parcel was still dry; wetting since moved water history
        but the static map did not.
      - ``map_born_wrong``: inferred study year *on or after* the breakpoint —
        a restudy happened after wetting began, yet AE still conflicts with
        what the satellite archive shows.
    """
    zone_field = record.get("fema_flood_zone") or {}
    zone = zone_field.get("value")
    vintage = zone_field.get("vintage")
    water = witness.get("water") or {}
    breakpoint_year = water.get("breakpoint_year")

    if zone != "AE" or breakpoint_year is None:
        return {
            "applies": False,
            "label": None,
            "sentence": None,
            "dataset_vintage": vintage,
            "breakpoint_year": breakpoint_year,
            "inferred_study_year": _infer_study_year(vintage),
        }

    inferred = _infer_study_year(vintage)
    if inferred is None:
        return {
            "applies": True,
            "label": "map_aged_out",
            "sentence": (
                f"Zone AE on panel {vintage} with wetting since {breakpoint_year}, "
                "but study year could not be parsed — defaulting to map_aged_out "
                "(static study likely predates observed regime shift)."
            ),
            "dataset_vintage": vintage,
            "breakpoint_year": breakpoint_year,
            "inferred_study_year": None,
        }

    if inferred < breakpoint_year:
        label = "map_aged_out"
        sentence = (
            f"The FEMA panel ({vintage}, ~{inferred} vintage) predates the "
            f"{breakpoint_year} wetting breakpoint — label map_aged_out: water "
            "history moved after a static study froze the AE zone."
        )
    else:
        label = "map_born_wrong"
        sentence = (
            f"The FEMA panel ({vintage}, ~{inferred} vintage) post-dates the "
            f"{breakpoint_year} wetting breakpoint — label map_born_wrong: a "
            "restudy still assigned AE while the satellite archive shows sustained wetting."
        )

    return {
        "applies": True,
        "label": label,
        "sentence": sentence,
        "dataset_vintage": vintage,
        "breakpoint_year": breakpoint_year,
        "inferred_study_year": inferred,
    }
