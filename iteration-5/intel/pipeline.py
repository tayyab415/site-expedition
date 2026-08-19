"""Single-site intel pipeline — triage → vintage → judge."""

from __future__ import annotations

from .triage import triage
from .vintage import assess_vintage
from .judge import judge


def run_intel(site: dict, record: dict, witness: dict) -> dict:
    triage_result = triage(record)
    vintage_result = assess_vintage(record, witness)
    ruling = judge(record, witness, triage_result)

    docket = []
    for idx, staged in enumerate(triage_result["staged"], start=1):
        docket.append({
            "number": idx,
            "fight": staged["fight"],
            "staged": True,
            "because": staged["because"],
        })
    for skipped in triage_result["skipped"]:
        docket.append({
            "number": None,
            "fight": skipped["fight"],
            "staged": False,
            "because": [skipped["reason"]],
        })

    return {
        "site": site,
        "layer": 2,
        "triage": triage_result,
        "vintage": vintage_result,
        "ruling": ruling,
        "docket": docket,
        "record": record,
        "witness_summary": {
            "water": {k: v for k, v in witness["water"].items() if k != "timeline"},
            "height": witness["height"],
        },
    }
