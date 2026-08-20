"""CLI: python3 -m expedition.discovery --mission warehouse --look Houston --budget standard"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="expedition.discovery",
        description="Find POTENTIAL map/facility pins. Not a listing service.",
    )
    parser.add_argument("--mission", default="warehouse")
    parser.add_argument("--look", default="", help="US city or metro")
    parser.add_argument("--region", default="texas_triangle")
    parser.add_argument("--budget", default="standard", choices=("quick", "standard", "deep"))
    parser.add_argument("--network", action="store_true", default=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--paid", action="store_true", help="Enable Places/RentCast when keys exist")
    parser.add_argument("--prefilter", action="store_true", help="Spend Mireye credits on a cheap batch screen")
    parser.add_argument("--narrate", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    from expedition.discovery.harness import run_discovery

    packet = run_discovery(
        args.mission,
        search_region=args.region,
        look_query=args.look,
        scan_budget=args.budget,
        network=not args.offline,
        allow_paid=args.paid,
        prefilter=args.prefilter,
        live_mireye=args.prefilter,
        narrate=args.narrate,
    )
    slim = {
        "mission": packet["mission"],
        "look": packet.get("look"),
        "scan_budget": packet["scan_budget"],
        "plan": packet["plan"],
        "traces": packet["traces"],
        "note": packet["note"],
        "credits_spent": packet["credits_spent"],
        "candidates": [
            {
                "id": row["id"],
                "name": row["name"],
                "label": row["label"],
                "source": row["source"],
                "lat": row["lat"],
                "lng": row["lng"],
            }
            for row in packet["candidates"]
        ],
        "anchors": [
            {"id": row["id"], "name": row["name"], "source": row["source"]}
            for row in packet["anchors"]
        ],
        "narration": packet.get("narration"),
    }
    text = json.dumps(slim, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
