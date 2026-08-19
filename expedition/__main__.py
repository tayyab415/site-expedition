"""CLI: python -m expedition run|verify|serve"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="expedition")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--mission", required=True)
    run.add_argument("--candidate", action="append", required=True)
    run.add_argument("--live", action="store_true")
    run.add_argument("--review", action="store_true")
    run.add_argument("--out", type=Path)

    ver = sub.add_parser("verify")
    ver.add_argument("--live", action="store_true")
    ver.add_argument("--out", type=Path, default=ROOT / "var" / "verify_last.json")

    sub.add_parser("serve")

    args = p.parse_args(argv)
    if args.cmd == "run":
        from expedition.engine import run_mission

        packet = run_mission(
            args.mission, args.candidate, live=args.live, review=args.review
        )
        text = json.dumps(packet, indent=2, default=str)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text)
        print(text)
        return 0
    if args.cmd == "verify":
        from expedition.engine import run_site
        from expedition.verify.score import load_gates, score_run

        results = {}
        for gate in load_gates():
            packet = run_site(
                gate["mission"],
                gate["candidate_id"],
                live=args.live,
                review=False,
                controls=gate.get("controls") or {},
            )
            results[gate["id"]] = packet
        scored = score_run(results)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"score": scored, "results": {k: v["verdict"] for k, v in results.items()}}, indent=2))
        print(json.dumps(scored, indent=2))
        return 0 if scored["failed"] == 0 else 1
    if args.cmd == "serve":
        from expedition.ui.serve import main as serve_main

        serve_main()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
