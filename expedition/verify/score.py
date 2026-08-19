"""Compare a finished Expedition packet to held-out gates.

This module is the only runtime that may read gates.json.
"""

from __future__ import annotations

import json
from pathlib import Path

GATES = Path(__file__).resolve().parent / "gates.json"


def load_gates() -> list[dict]:
    return json.loads(GATES.read_text())["gates"]


def score_packet(gate: dict, packet: dict) -> dict:
    verdict = packet["verdict"]["verdict"]
    reasons = packet["verdict"].get("reasons") or []
    gaps = [g.get("missing_authority") or g.get("question_id") for g in packet["verdict"].get("gaps") or []]
    inform = packet["verdict"].get("inform") or {}
    failures = []

    if gate.get("expect_verdict") and verdict != gate["expect_verdict"]:
        failures.append(f"verdict {verdict} != {gate['expect_verdict']}")
    if gate.get("forbid_verdict") and verdict == gate["forbid_verdict"]:
        failures.append(f"verdict was forbidden {verdict}")
    if gate.get("expect_verdict_in") and verdict not in gate["expect_verdict_in"]:
        failures.append(f"verdict {verdict} not in {gate['expect_verdict_in']}")
    if gate.get("must_include_reason") and gate["must_include_reason"] not in reasons:
        failures.append(f"missing reason {gate['must_include_reason']}")
    if gate.get("forbid_reason") and gate["forbid_reason"] in reasons:
        failures.append(f"forbidden reason {gate['forbid_reason']}")
    if gate.get("expect_inform") and not inform.get(gate["expect_inform"]):
        failures.append(f"missing inform {gate['expect_inform']}")
    if gate.get("must_include_gap") and gate["must_include_gap"] not in gaps:
        failures.append(f"missing gap {gate['must_include_gap']}")

    return {
        "id": gate["id"],
        "pass": not failures,
        "failures": failures,
        "got": {"verdict": verdict, "reasons": reasons, "gaps": gaps},
    }


def score_run(results_by_gate_id: dict[str, dict]) -> dict:
    rows = []
    for gate in load_gates():
        packet = results_by_gate_id.get(gate["id"])
        if packet is None:
            rows.append({"id": gate["id"], "pass": False, "failures": ["no packet"]})
        else:
            rows.append(score_packet(gate, packet))
    return {
        "passed": sum(1 for r in rows if r["pass"]),
        "failed": sum(1 for r in rows if not r["pass"]),
        "rows": rows,
    }
