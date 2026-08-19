"""Adjudication — apply fight rules only for triaged fights; count → verdict."""

from __future__ import annotations


def _evaluate_time(record: dict, witness: dict) -> dict | None:
    w = witness["water"]
    recorded_pct = (record.get("surface_water_permanence_pct") or {}).get("value") or 0.0
    observed_pct = w["latest_freq_2021"] * 100
    baseline = w["baseline_freq_1985_1999"]
    if (
        w["breakpoint_year"] is not None
        and w["latest_freq_2021"] >= max(3 * baseline, baseline + 0.05)
        and observed_pct >= 1.5 * recorded_pct
    ):
        return {
            "fight": "TIME",
            "claim": f"record says water {recorded_pct:.0f}% of the time",
            "witness": (
                f"JRC monthly history: dry {1985}-{w['breakpoint_year'] - 1} "
                f"(baseline {baseline * 100:.2f}% of months), wetting since "
                f"{w['breakpoint_year']}, {observed_pct:.1f}% of months by 2021"
            ),
            "numbers": {
                "recorded_permanence_pct": recorded_pct,
                "observed_2021_pct": round(observed_pct, 1),
                "baseline_pct": round(baseline * 100, 2),
                "breakpoint_year": w["breakpoint_year"],
            },
        }
    return None


def _evaluate_height(record: dict, witness: dict) -> dict | None:
    h = witness["height"]
    rec_elev = (record.get("elevation_m") or {}).get("value")
    if rec_elev is None:
        return None
    gap = abs(h["fabdem_m"] - rec_elev)
    if gap < 1.0:
        return None

    zone = (record.get("fema_flood_zone") or {}).get("value")
    coast = (record.get("coast_distance_m") or {}).get("value")
    where = (
        f"this close to the shore ({coast:.0f} m)"
        if isinstance(coast, (int, float)) and coast < 5000
        else f"in flood zone {zone}"
    )
    direction = "lower" if h["fabdem_m"] < rec_elev else "higher"
    return {
        "fight": "HEIGHT",
        "claim": (
            f"record says ground at {rec_elev:.2f} m "
            f"({record['elevation_m']['source']})"
        ),
        "witness": (
            f"FABDEM says {h['fabdem_m']:.2f} m — {gap:.2f} m {direction}; "
            f"NASADEM says {h['nasadem_m']:.2f} m. Flood-depth math flips "
            f"on a {gap:.1f} m disagreement {where}."
        ),
        "numbers": {
            "record_m": rec_elev,
            "fabdem_m": round(h["fabdem_m"], 2),
            "nasadem_m": round(h["nasadem_m"], 2),
            "gap_m": round(gap, 2),
            "height_gated": True,
        },
    }


def _aggravators(record: dict) -> list[str]:
    zone = (record.get("fema_flood_zone") or {}).get("value")
    wetland = (record.get("intersects_wetland") or {}).get("value")
    vintage = (record.get("fema_flood_zone") or {}).get("vintage")
    items: list[str] = []
    if zone in ("A", "AE", "VE") and wetland:
        items.append(
            f"already zone {zone} ({vintage}) and intersects a mapped wetland"
        )
    return items


def judge(record: dict, witness: dict, triage_result: dict) -> dict:
    """Stage fights only when triage included them; map count to KEEP/HUMAN/KILL."""
    fights: list[dict] = []
    not_fought: list[dict] = []

    if triage_result["stage_time"]:
        time_fight = _evaluate_time(record, witness)
        if time_fight:
            fights.append(time_fight)
        else:
            not_fought.append({
                "fight": "TIME",
                "reason": "TIME staged but witness did not clear the contradiction threshold.",
            })
    else:
        not_fought.append({
            "fight": "TIME",
            "reason": next(
                (s["reason"] for s in triage_result["skipped"] if s["fight"] == "TIME"),
                "TIME not staged.",
            ),
        })

    if triage_result["stage_height"]:
        height_fight = _evaluate_height(record, witness)
        if height_fight:
            fights.append(height_fight)
        else:
            not_fought.append({
                "fight": "HEIGHT",
                "reason": "HEIGHT staged but FABDEM gap < 1.0 m — no material dissent.",
            })
    else:
        not_fought.append({
            "fight": "HEIGHT",
            "reason": next(
                (s["reason"] for s in triage_result["skipped"] if s["fight"] == "HEIGHT"),
                "HEIGHT not staged.",
            ),
        })

    count = len(fights)
    verdict = "KILL" if count >= 2 else ("HUMAN" if count == 1 else "KEEP")

    keep_explanation = None
    if verdict == "KEEP":
        keep_explanation = "No fights cleared adjudication. " + " ".join(
            f"{item['reason']}." for item in not_fought
        )

    return {
        "verdict": verdict,
        "fights": fights,
        "not_fought": not_fought,
        "aggravators": _aggravators(record),
        "keep_explanation": keep_explanation,
    }
