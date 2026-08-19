#!/usr/bin/env python3
"""Consequence composer — fights become deal instructions, not a report."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "out"


def consequence(verdict: dict) -> dict:
    ruling = verdict["ruling"]
    lines = []
    for f in ruling.get("fights") or []:
        if f["fight"] == "TIME":
            n = f["numbers"]
            lines.append(
                {
                    "fight": "TIME",
                    "instruction": (
                        f"Do not treat {n['recorded_permanence_pct']:.0f}% permanence as the "
                        f"water story. The archive is dry until {n['breakpoint_year']}, then "
                        f"{n['observed_2021_pct']:.1f}% of months by 2021. Price the trajectory, "
                        "or walk."
                    ),
                }
            )
        elif f["fight"] == "HEIGHT":
            n = f["numbers"]
            lines.append(
                {
                    "fight": "HEIGHT",
                    "instruction": (
                        f"Do not run flood-depth math on {n['record_m']:.2f} m while FABDEM "
                        f"reads {n['fabdem_m']:.2f} m ({n['gap_m']:.2f} m gap). Survey or walk."
                    ),
                }
            )
    v = ruling["verdict"]
    subject = {
        "KILL": "Withdraw — two witnesses impeach the record",
        "KEEP": "Clear — no material contradiction at this pin",
        "HUMAN": "Hold — one contradiction, need a surveyor",
    }[v]
    closing = {
        "KILL": "Advise the client to withdraw. If they proceed, price the contradiction, not the record.",
        "KEEP": "The skeptic has nothing material. Proceed on the cited record.",
        "HUMAN": "Escalate before earnest money.",
    }[v]
    return {
        "to": "buyer's agent of record",
        "subject": subject,
        "verdict": v,
        "site": verdict["site"]["name"],
        "tagline": (
            "You're buying 2021 dirt at a 1995 feeling."
            if v == "KILL"
            else "No material contradiction."
        ),
        "consequences": lines,
        "closing": closing,
    }


def main():
    OUT.mkdir(exist_ok=True)
    for slug, folder in [
        ("san_leon", ROOT / "data" / "san_leon"),
        ("keep_control", ROOT / "data" / "keep_control"),
    ]:
        v = json.loads((folder / "verdict.json").read_text())
        mail = consequence(v)
        (OUT / f"{slug}.json").write_text(json.dumps(mail, indent=2))
        print(slug, mail["verdict"], mail["subject"])


if __name__ == "__main__":
    main()
