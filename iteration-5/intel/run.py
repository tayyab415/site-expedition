#!/usr/bin/env python3
"""Load harness packets, run layer-2 intel, write iteration-5/out/*.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from intel.pipeline import run_intel  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "out"

SITES = ("san_leon", "3605_winfield_cove_austin_tx")


def load_packet(slug: str) -> tuple[dict, dict, dict]:
    base = DATA / slug
    verdict = json.loads((base / "verdict.json").read_text())
    witness = json.loads((base / "evidence.json").read_text())
    return verdict["site"], verdict["record"], witness


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in SITES:
        site, record, witness = load_packet(slug)
        result = run_intel(site, record, witness)
        path = OUT / f"{slug}.json"
        path.write_text(json.dumps(result, indent=2))
        fights = len(result["ruling"]["fights"])
        print(f"{slug}: {result['ruling']['verdict']} ({fights} fight(s)) -> {path}")


if __name__ == "__main__":
    main()
