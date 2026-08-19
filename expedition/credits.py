"""Quote-before-fetch and the 20k / 25k Mireye ceilings."""

from __future__ import annotations

import json
from pathlib import Path

SOFT_CAP = 20_000
HARD_CAP = 25_000
DEFAULT_EXPEDITION_CAP = 150

LEDGER = Path(__file__).resolve().parent / "var" / "credit_ledger.json"


class CreditCeiling(RuntimeError):
    pass


def _load() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"used_this_build": 0, "events": []}


def _save(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, indent=2))


def used() -> int:
    return int(_load().get("used_this_build") or 0)


def remaining_soft() -> int:
    return max(0, SOFT_CAP - used())


def remaining_hard() -> int:
    return max(0, HARD_CAP - used())


def authorize(credits: int, *, reason: str, expedition_spent: int = 0) -> None:
    credits = int(credits)
    if credits <= 0:
        return
    if used() + credits > HARD_CAP:
        raise CreditCeiling(
            f"hard stop {HARD_CAP}: used={used()} requested={credits}"
        )
    if used() + credits > SOFT_CAP:
        raise CreditCeiling(
            f"soft cap {SOFT_CAP}: used={used()} requested={credits}. "
            "Ask before crossing the soft cap."
        )
    if expedition_spent + credits > DEFAULT_EXPEDITION_CAP:
        raise CreditCeiling(
            f"expedition cap {DEFAULT_EXPEDITION_CAP}: "
            f"spent={expedition_spent} requested={credits}"
        )
    data = _load()
    data["used_this_build"] = used() + credits
    data.setdefault("events", []).append({"credits": credits, "reason": reason})
    _save(data)


def snapshot() -> dict:
    return {
        "used_this_build": used(),
        "soft_cap": SOFT_CAP,
        "hard_cap": HARD_CAP,
        "soft_remaining": remaining_soft(),
        "hard_remaining": remaining_hard(),
        "expedition_cap": DEFAULT_EXPEDITION_CAP,
    }
