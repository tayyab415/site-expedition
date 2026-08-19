"""Fight selection — the record decides which cross-examinations to stage."""

from __future__ import annotations

COASTAL_THRESHOLD_M = 5000
HEIGHT_ZONES = frozenset({"A", "AE", "VE", "AO", "AH"})
FLOOD_TIME_ZONES = frozenset({"AE", "VE"})
POOR_DRAINAGE_MARKERS = ("poorly drained", "very poorly drained", "somewhat poorly drained")


def _field_value(record: dict, key: str):
    field = record.get(key) or {}
    return field.get("value")


def _is_coastal(record: dict) -> bool:
    coast = _field_value(record, "coast_distance_m")
    return isinstance(coast, (int, float)) and coast < COASTAL_THRESHOLD_M


def _is_poor_drainage(record: dict) -> bool:
    drainage = _field_value(record, "soil_drainage_class")
    if not isinstance(drainage, str):
        return False
    lowered = drainage.lower()
    return any(marker in lowered for marker in POOR_DRAINAGE_MARKERS)


def triage(record: dict) -> dict:
    """Return which fights to stage and human-readable reasons for each decision."""
    zone = _field_value(record, "fema_flood_zone") or "—"
    elev = _field_value(record, "elevation_m")
    coast = _field_value(record, "coast_distance_m")
    permanence = _field_value(record, "surface_water_permanence_pct") or 0.0
    drainage = _field_value(record, "soil_drainage_class") or "—"

    time_triggers: list[str] = []
    if _is_coastal(record):
        time_triggers.append(f"coastal ({coast:.0f} m to shore)")
    if zone in FLOOD_TIME_ZONES:
        time_triggers.append(f"zone {zone}")
    if _is_poor_drainage(record):
        time_triggers.append(f"poor drainage ({drainage})")
    if permanence > 0:
        time_triggers.append(f"water permanence {permanence:g}%")

    stage_time = bool(time_triggers)

    height_triggers: list[str] = []
    if isinstance(elev, (int, float)) and elev < 10:
        height_triggers.append(f"low elevation ({elev:.2f} m)")
    if zone in HEIGHT_ZONES:
        height_triggers.append(f"zone {zone}")

    stage_height = bool(height_triggers)

    staged = []
    skipped = []

    if stage_time:
        staged.append({"fight": "TIME", "because": time_triggers})
    else:
        skipped.append({
            "fight": "TIME",
            "reason": (
                f"TIME skipped: inland ({coast:.0f} m to shore), zone {zone}, "
                f"drainage “{drainage}”, permanence {permanence:g}%"
                if isinstance(coast, (int, float))
                else f"TIME skipped: zone {zone}, drainage “{drainage}”, permanence {permanence:g}%"
            ),
        })

    elev_display = f"{elev:.0f} m" if isinstance(elev, (int, float)) else "—"
    if stage_height:
        staged.append({"fight": "HEIGHT", "because": height_triggers})
    else:
        skipped.append({
            "fight": "HEIGHT",
            "reason": f"HEIGHT skipped: inland, zone {zone}, elev {elev_display}",
        })

    return {
        "staged": staged,
        "skipped": skipped,
        "stage_time": stage_time,
        "stage_height": stage_height,
    }
