"""Live end-to-end probes. Held-out gates are scored after the run."""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from expedition.adapters import routes
from expedition.adapters.earth import flood_rewind
from expedition.adapters.model import complete, skeptic_review
from expedition.credits import snapshot
from expedition.engine import run_site
from expedition.verify.score import load_gates, score_packet


LIVE_GATES = ["F-bad", "F-good-NY", "W-kill", "H-keep"]


def main() -> int:
    report: dict = {"started": time.time(), "steps": [], "credits": snapshot()}
    gates = {g["id"]: g for g in load_gates()}

    # 1) Routes
    t0 = time.time()
    try:
        row = routes.route_matrix(
            {"lat": 29.7604, "lng": -95.3698},
            {"lat": 29.4241, "lng": -98.4936},
        )
        report["steps"].append({
            "id": "routes",
            "ok": isinstance(row.get("duration_s"), int) and row["duration_s"] > 0,
            "s": round(time.time() - t0, 3),
            "duration_s": row.get("duration_s"),
            "distance_m": row.get("distance_m"),
        })
    except Exception as exc:
        report["steps"].append({"id": "routes", "ok": False, "error": type(exc).__name__, "s": round(time.time() - t0, 3)})

    # 2) Vertex
    t0 = time.time()
    model = complete("Reply with the single word OK.")
    report["steps"].append({
        "id": "vertex",
        "ok": bool(model.get("ok") and "OK" in (model.get("text") or "")),
        "s": round(time.time() - t0, 3),
        "provider": model.get("provider"),
        "model": model.get("model"),
    })

    # 3) Live Expedition sites, then score held-out
    for gid in LIVE_GATES:
        gate = gates[gid]
        t0 = time.time()
        try:
            packet = run_site(
                gate["mission"],
                gate["candidate_id"],
                live=True,
                review=False,
                controls=gate.get("controls") or {},
            )
            scored = score_packet(gate, packet)
            report["steps"].append({
                "id": f"live:{gid}",
                "ok": scored["pass"],
                "s": round(time.time() - t0, 3),
                "verdict": packet["verdict"]["verdict"],
                "reasons": packet["verdict"]["reasons"],
                "credits": packet["credits"]["expedition_spent"],
                "failures": scored["failures"],
                "live_label": packet.get("live"),
            })
        except Exception as exc:
            report["steps"].append({
                "id": f"live:{gid}",
                "ok": False,
                "s": round(time.time() - t0, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "trace": traceback.format_exc()[-400:],
            })

    # 4) Live EE rewind on San Leon
    t0 = time.time()
    try:
        atoms, payload = flood_rewind(
            candidate_id="san_leon", lat=29.475732, lng=-94.966533, live=True
        )
        water = (payload.get("water") or {})
        report["steps"].append({
            "id": "ee_rewind_san_leon",
            "ok": water.get("latest_freq_2021") is not None,
            "s": round(time.time() - t0, 3),
            "breakpoint_year": water.get("breakpoint_year"),
            "latest_freq_2021": water.get("latest_freq_2021"),
            "nasadem_m": (payload.get("height") or {}).get("nasadem_m"),
            "atom_kinds": [a.kind for a in atoms],
        })
    except Exception as exc:
        report["steps"].append({
            "id": "ee_rewind_san_leon",
            "ok": False,
            "s": round(time.time() - t0, 3),
            "error": f"{type(exc).__name__}: {exc}",
        })

    # 5) Live Skeptic over replay evidence.  This exercises the model reviewer
    # without spending a second Mireye screen for the same Candidate Site.
    t0 = time.time()
    try:
        packet = run_site("warehouse", "san_leon", live=False, review=False)
        sk = skeptic_review(
            {
                "candidates": [packet["candidate"]["id"]],
                "atoms": packet["atoms"],
                "verdicts": [packet["verdict"]],
                "gaps": packet["verdict"]["gaps"],
            },
            live_model=True,
        )
        report["steps"].append({
            "id": "skeptic",
            "ok": bool(sk.get("ok")),
            "s": round(time.time() - t0, 3),
            "provider": sk.get("provider"),
            "model": sk.get("model"),
            "flags": sk.get("flags"),
            "notes": sk.get("notes"),
            "reviewer_ok": sk.get("ok"),
        })
    except Exception as exc:
        report["steps"].append({"id": "skeptic", "ok": False, "error": type(exc).__name__, "s": round(time.time() - t0, 3)})

    report["finished"] = time.time()
    report["elapsed_s"] = round(report["finished"] - report["started"], 3)
    report["credits_after"] = snapshot()
    report["passed"] = sum(1 for s in report["steps"] if s.get("ok"))
    report["failed"] = sum(1 for s in report["steps"] if not s.get("ok"))
    out = ROOT / "var" / "e2e_live.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({k: report[k] for k in ("passed", "failed", "elapsed_s", "credits_after", "steps")}, indent=2, default=str))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
