#!/usr/bin/env python3
"""Execute the fixed tool plan and write trace.json for UI replay."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness import (
    ROOT,
    SITES,
    TOOL_BY_NAME,
    TOOL_DURATIONS_MS,
    fixed_plan,
)

TRACE_DIR = ROOT / "trace"


def run_site(site_key: str) -> dict:
    if site_key not in SITES:
        raise SystemExit(f"unknown site {site_key!r}; choose from {list(SITES)}")

    site = SITES[site_key]
    ctx = {"site_key": site_key, "site": site}
    plan = fixed_plan(site_key)

    steps = []
    t0_ms = 0

    for i, step in enumerate(plan):
        tool_name = step["tool"]
        tool = TOOL_BY_NAME[tool_name]
        duration_ms = TOOL_DURATIONS_MS.get(tool_name, 200)

        started_ms = t0_ms
        try:
            output = tool["run"](ctx, step["input"])
            status = "ok"
            error = None
        except Exception as exc:  # noqa: BLE001 — trace must capture failures
            output = {}
            status = "error"
            error = str(exc)

        finished_ms = started_ms + duration_ms
        t0_ms = finished_ms + 120  # gap between tool calls

        steps.append({
            "index": i,
            "tool": tool_name,
            "description": tool["description"],
            "input": step["input"],
            "output": output,
            "status": status,
            "error": error,
            "started_ms": started_ms,
            "duration_ms": duration_ms,
            "finished_ms": finished_ms,
        })

    ruling = ctx.get("ruling", {})
    trace = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_key": site_key,
        "site": {k: v for k, v in site.items() if k != "slug"},
        "verdict": ruling.get("verdict"),
        "fights": ruling.get("fights", []),
        "aggravators": ruling.get("aggravators", []),
        "total_duration_ms": t0_ms,
        "steps": steps,
        "replay": {
            "mode": "cached",
            "live_apis": False,
            "note": "Timings simulated; payloads from data/*/cache/",
        },
    }
    return trace


def main():
    ap = argparse.ArgumentParser(description="Run harness plan and write trace.json")
    ap.add_argument(
        "--site",
        choices=list(SITES.keys()),
        help="single site to run",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="run both san_leon and keep_control",
    )
    args = ap.parse_args()

    if args.all:
        sites = list(SITES.keys())
    elif args.site:
        sites = [args.site]
    else:
        sites = list(SITES.keys())

    TRACE_DIR.mkdir(parents=True, exist_ok=True)

    for key in sites:
        trace = run_site(key)
        out = TRACE_DIR / f"{key}.json"
        out.write_text(json.dumps(trace, indent=2))
        print(f"wrote {out}  verdict={trace['verdict']}  steps={len(trace['steps'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
