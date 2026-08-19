"""Tool harness — first-class tools the UI replays.

Each tool is a dict: name, input_schema, run(ctx) -> dict.
No LLM. Fixed plan in runner.py reads cached packets only.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

SITES = {
    "san_leon": {
        "name": "San Leon, TX (Galveston Bay shore)",
        "lat": 29.475732,
        "lng": -94.966533,
        "slug": "san_leon",
    },
    "keep_control": {
        "name": "3605 Winfield Cove, Austin TX",
        "lat": 30.2363775,
        "lng": -97.7807633,
        "slug": "3605_winfield_cove_austin_tx",
    },
}

# Simulated wall-clock for replay (ms). No live I/O.
TOOL_DURATIONS_MS = {
    "mireye.fetch": 420,
    "ee.water_rewind": 2800,
    "ee.height_check": 1100,
    "intel.triage": 180,
    "judge.verdict": 95,
    "act.write_packet": 240,
}


def _site_dir(site_key: str) -> Path:
    return DATA / site_key


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _mireye_record(raw: dict) -> dict:
    f = raw["fields"]

    def field(name):
        v = f.get(name) or {}
        return {
            "value": v.get("value"),
            "unit": v.get("unit"),
            "source": v.get("source"),
            "source_url": v.get("source_url"),
            "confidence": v.get("confidence"),
            "vintage": v.get("dataset_vintage"),
            "fetched_at": v.get("fetched_at"),
        }

    return {
        "elevation_m": field("elevation"),
        "fema_flood_zone": field("fema_flood_zone"),
        "intersects_wetland": field("intersects_wetland"),
        "surface_water_permanence_pct": field("surface_water_permanence_pct"),
        "coast_distance_m": field("coast_distance_m"),
        "soil_drainage_class": field("soil_drainage_class"),
        "fetched_at": raw.get("fetched_at"),
    }


def judge(record: dict, witness: dict) -> dict:
    """Deterministic verdict rules (same as harness/vet.py)."""
    fights = []

    w = witness["water"]
    recorded_pct = record["surface_water_permanence_pct"]["value"] or 0.0
    observed_pct = w["latest_freq_2021"] * 100
    baseline = w["baseline_freq_1985_1999"]
    if (
        w["breakpoint_year"] is not None
        and w["latest_freq_2021"] >= max(3 * baseline, baseline + 0.05)
        and observed_pct >= 1.5 * recorded_pct
    ):
        fights.append({
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
        })

    h = witness["height"]
    rec_elev = record["elevation_m"]["value"]
    gap = abs(h["fabdem_m"] - rec_elev)
    zone = record["fema_flood_zone"]["value"]
    coast = (record.get("coast_distance_m") or {}).get("value")
    height_counts = rec_elev is not None and (
        rec_elev < 10 or zone in ("A", "AE", "VE", "AO", "AH")
    )
    if gap >= 1.0 and height_counts:
        where = (
            f"this close to the shore ({coast:.0f} m)"
            if isinstance(coast, (int, float)) and coast < 5000
            else f"in flood zone {zone}"
        )
        direction = "lower" if h["fabdem_m"] < rec_elev else "higher"
        fights.append({
            "fight": "HEIGHT",
            "claim": f"record says ground at {rec_elev:.2f} m ({record['elevation_m']['source']})",
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
        })

    aggravators = []
    if zone in ("A", "AE", "VE") and record["intersects_wetland"]["value"]:
        aggravators.append(
            f"already zone {zone} ({record['fema_flood_zone']['vintage']}) "
            "and intersects a mapped wetland"
        )

    verdict = "KILL" if len(fights) >= 2 else ("HUMAN" if fights else "KEEP")
    return {"verdict": verdict, "fights": fights, "aggravators": aggravators}


def triage(record: dict) -> dict:
    """Record-driven docket: which witnesses to stage."""
    zone = record["fema_flood_zone"]["value"]
    coast = (record.get("coast_distance_m") or {}).get("value")
    drainage = (record.get("soil_drainage_class") or {}).get("value") or ""
    water_pct = record["surface_water_permanence_pct"]["value"] or 0.0

    reasons = []
    schedule = []

    coastal = isinstance(coast, (int, float)) and coast < 5000
    flood_risk = zone in ("A", "AE", "VE", "AO", "AH")
    poor_drain = "poor" in drainage.lower()

    if coastal or water_pct > 0 or flood_risk:
        schedule.append("ee.water_rewind")
        if coastal:
            reasons.append(f"coast {coast:.0f} m — time witness mandatory")
        elif water_pct > 0:
            reasons.append(f"record claims {water_pct:.0f}% surface water")
        else:
            reasons.append(f"flood zone {zone} — wetting history relevant")

    if flood_risk or coastal or (record["elevation_m"]["value"] or 999) < 10:
        schedule.append("ee.height_check")
        if coastal:
            reasons.append("coastal pin — bare-earth elevation dissent matters")
        elif flood_risk:
            reasons.append(f"zone {zone} — elevation gap gates flood math")
        else:
            reasons.append("low elevation — height cross-check")

    if poor_drain and "ee.water_rewind" not in schedule:
        schedule.append("ee.water_rewind")
        reasons.append(f"soil '{drainage}' — drainage corroboration")

    if not schedule:
        schedule = ["ee.water_rewind", "ee.height_check"]
        reasons.append("default docket — baseline witnesses")

    return {
        "scheduled_tools": schedule,
        "reasons": reasons,
        "signals": {
            "flood_zone": zone,
            "coast_m": coast,
            "water_permanence_pct": water_pct,
            "drainage": drainage,
        },
    }


def sparkline_svg(timeline: list, breakpoint_year) -> str:
    w, h, pad = 740, 120, 4
    n = len(timeline)
    bw = (w - 2 * pad) / n
    top = max(t["water_freq"] for t in timeline) or 1
    bars = []
    for i, t in enumerate(timeline):
        bh = (t["water_freq"] / top) * (h - 30)
        x = pad + i * bw
        red = breakpoint_year and t["year"] >= breakpoint_year
        bars.append(
            f'<rect x="{x:.1f}" y="{h - 20 - bh:.1f}" width="{bw - 1.5:.1f}" '
            f'height="{max(bh, 0.5):.1f}" fill="{"#c0392b" if red else "#7f8c8d"}"/>'
        )
        if t["year"] % 5 == 0:
            bars.append(
                f'<text x="{x:.1f}" y="{h - 6}" font-size="9" fill="#555">{t["year"]}</text>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<text x="{pad}" y="12" font-size="11" fill="#333">share of observed months with standing water '
        f'(JRC GSW monthly history, 60 m buffer)</text>{"".join(bars)}</svg>'
    )


def _run_mireye_fetch(ctx: dict, inp: dict) -> dict:
    site = ctx["site"]
    slug = site["slug"]
    raw_path = _site_dir(ctx["site_key"]) / "cache" / "mireye" / f"{slug}.json"
    raw = _load_json(raw_path)
    record = _mireye_record(raw)
    ctx["record"] = record
    ctx["mireye_raw"] = raw
    return {
        "cache_hit": True,
        "path": str(raw_path.relative_to(ROOT)),
        "record_summary": {
            "elevation_m": record["elevation_m"]["value"],
            "fema_flood_zone": record["fema_flood_zone"]["value"],
            "surface_water_permanence_pct": record["surface_water_permanence_pct"]["value"],
            "intersects_wetland": record["intersects_wetland"]["value"],
        },
        "fields_returned": list(raw.get("fields", {}).keys()),
    }


def _run_ee_water_rewind(ctx: dict, inp: dict) -> dict:
    site = ctx["site"]
    slug = site["slug"]
    path = _site_dir(ctx["site_key"]) / "cache" / "earth" / f"{slug}.json"
    witness = _load_json(path)
    water = witness["water"]
    ctx.setdefault("witness", {})["water"] = water
    return {
        "cache_hit": True,
        "path": str(path.relative_to(ROOT)),
        "dataset": water["dataset"],
        "baseline_freq_1985_1999": water["baseline_freq_1985_1999"],
        "latest_freq_2021": water["latest_freq_2021"],
        "breakpoint_year": water["breakpoint_year"],
        "timeline_years": len(water["timeline"]),
    }


def _run_ee_height_check(ctx: dict, inp: dict) -> dict:
    site = ctx["site"]
    slug = site["slug"]
    path = _site_dir(ctx["site_key"]) / "cache" / "earth" / f"{slug}.json"
    witness = _load_json(path)
    height = witness["height"]
    ctx.setdefault("witness", {})["height"] = height
    record_elev = ctx["record"]["elevation_m"]["value"]
    gap = abs(height["fabdem_m"] - record_elev) if record_elev is not None else None
    return {
        "cache_hit": True,
        "path": str(path.relative_to(ROOT)),
        "fabdem_m": height["fabdem_m"],
        "nasadem_m": height["nasadem_m"],
        "record_elevation_m": record_elev,
        "gap_m": round(gap, 2) if gap is not None else None,
        "datasets": height["datasets"],
    }


def _run_intel_triage(ctx: dict, inp: dict) -> dict:
    docket = triage(ctx["record"])
    ctx["docket"] = docket
    return docket


def _run_judge_verdict(ctx: dict, inp: dict) -> dict:
    witness = ctx.get("witness") or _load_json(
        _site_dir(ctx["site_key"]) / "cache" / "earth" / f"{ctx['site']['slug']}.json"
    )
    ruling = judge(ctx["record"], witness)
    ctx["ruling"] = ruling
    ctx["witness"] = witness
    return ruling


def _run_act_write_packet(ctx: dict, inp: dict) -> dict:
    site_key = ctx["site_key"]
    site = ctx["site"]
    record = ctx["record"]
    witness = ctx["witness"]
    ruling = ctx["ruling"]
    out = _site_dir(site_key)

    verdict_payload = {
        "site": {k: v for k, v in site.items() if k != "slug"},
        "ruling": ruling,
        "record": record,
        "witness_summary": {
            "water": {k: v for k, v in witness["water"].items() if k != "timeline"},
            "height": witness["height"],
        },
    }
    (out / "verdict.json").write_text(json.dumps(verdict_payload, indent=2))
    (out / "evidence.json").write_text(json.dumps(witness, indent=2))
    (out / "water_timeline.svg").write_text(
        sparkline_svg(witness["water"]["timeline"], witness["water"]["breakpoint_year"])
    )

    r, v = record, ruling
    lines = [
        f"# Due-diligence advisory — {site['name']}",
        f"**Verdict: {v['verdict']}**  ·  {date.today().isoformat()}  ·  "
        f"pin {site['lat']:.6f}, {site['lng']:.6f}",
        "",
        "Prepared for the buyer's agent of record. This advisory cross-examines the "
        "official cited record against independent public satellite evidence.",
        "",
        "## The record (as cited)",
        "| Fact | Value | Source |",
        "|---|---|---|",
    ]
    for label, key in [
        ("Ground elevation", "elevation_m"),
        ("FEMA flood zone", "fema_flood_zone"),
        ("Intersects wetland", "intersects_wetland"),
        ("Surface-water permanence", "surface_water_permanence_pct"),
    ]:
        f = r[key]
        val = f["value"]
        if isinstance(val, float):
            val = f"{val:.2f}"
        lines.append(f"| {label} | {val} | {f['source']} |")

    for i, f in enumerate(v["fights"], 1):
        lines += [
            "",
            f"### Fight {i}: {f['fight']}",
            f"- **Record:** {f['claim']}",
            f"- **Witness:** {f['witness']}",
        ]

    md_name = "kill_letter.md" if v["verdict"] == "KILL" else "advisory.md"
    (out / md_name).write_text("\n".join(lines))

    return {
        "output_dir": str(out.relative_to(ROOT)),
        "files": ["verdict.json", "evidence.json", "water_timeline.svg", md_name],
        "verdict": ruling["verdict"],
        "fight_count": len(ruling["fights"]),
    }


TOOLS = [
    {
        "name": "mireye.fetch",
        "description": "Load the cited federal record for a pin (cache-only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "preset": {"type": "string", "enum": ["terrain", "flood_risk"]},
            },
            "required": ["lat", "lng"],
        },
        "run": _run_mireye_fetch,
    },
    {
        "name": "ee.water_rewind",
        "description": "JRC Global Surface Water monthly history at 60 m buffer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "years": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["lat", "lng"],
        },
        "run": _run_ee_water_rewind,
    },
    {
        "name": "ee.height_check",
        "description": "FABDEM vs NASADEM vs cited elevation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lng": {"type": "number"},
                "buffer_m": {"type": "number", "default": 60},
            },
            "required": ["lat", "lng"],
        },
        "run": _run_ee_height_check,
    },
    {
        "name": "intel.triage",
        "description": "Record-driven docket — which witnesses to stage.",
        "input_schema": {
            "type": "object",
            "properties": {"record_ref": {"type": "string"}},
        },
        "run": _run_intel_triage,
    },
    {
        "name": "judge.verdict",
        "description": "Deterministic KEEP / KILL / HUMAN from fights.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_ref": {"type": "string"},
                "witness_ref": {"type": "string"},
            },
        },
        "run": _run_judge_verdict,
    },
    {
        "name": "act.write_packet",
        "description": "Write verdict.json, evidence, timeline SVG, letter.",
        "input_schema": {
            "type": "object",
            "properties": {"site_key": {"type": "string"}},
        },
        "run": _run_act_write_packet,
    },
]

TOOL_BY_NAME = {t["name"]: t for t in TOOLS}


def fixed_plan(site_key: str) -> list[dict]:
    """The robot's scripted tool loop — no LLM."""
    site = SITES[site_key]
    base = {"lat": site["lat"], "lng": site["lng"]}
    return [
        {"tool": "mireye.fetch", "input": {**base, "preset": "terrain"}},
        {"tool": "ee.water_rewind", "input": {**base, "years": list(range(1985, 2022))}},
        {"tool": "ee.height_check", "input": {**base, "buffer_m": 60}},
        {"tool": "intel.triage", "input": {"record_ref": "ctx.record"}},
        {"tool": "judge.verdict", "input": {"record_ref": "ctx.record", "witness_ref": "ctx.witness"}},
        {"tool": "act.write_packet", "input": {"site_key": site_key}},
    ]
