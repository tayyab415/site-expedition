"""Cheap Mireye batch screen on discovered pins. Quote first. Never a verdict."""

from __future__ import annotations

from dataclasses import replace

from expedition import credits
from expedition.adapters import mireye
from expedition.discovery.schema import Seed

PREFILTER_FIELDS = (
    "within_floodplain_polygon",
    "intersects_wetland",
    "slope_degrees",
)


def prefilter_seeds(
    seeds: list[Seed],
    *,
    live: bool,
    expedition_spent: int = 0,
    fetch_batch=None,
    quote=None,
    authorize=None,
) -> tuple[list[Seed], int, str | None]:
    """Attach extra.prefilter. Does not drop pins and does not score."""
    targets = [s for s in seeds if s.role == "candidate"][:25]
    if not targets:
        return seeds, 0, "no candidate pins to prefilter"
    if not live:
        return seeds, 0, "prefilter skipped: live Mireye is off"
    fields = list(PREFILTER_FIELDS)
    n = len(targets)
    quote_fn = quote or mireye.quote_credits
    authorize_fn = authorize or credits.authorize
    estimate = quote_fn(fields, n)
    authorize_fn(
        estimate,
        reason=f"discovery prefilter batch {n}x{len(fields)}f",
        expedition_spent=expedition_spent,
    )
    locations = [{"lat": s.lat, "lng": s.lng} for s in targets]
    request = fetch_batch or (lambda payload: mireye._request("/v1/fetch/batch", payload))
    raw = request({"locations": locations, "fields": fields})
    results = raw.get("results") or []
    by_index = {int(row.get("index", i)): row for i, row in enumerate(results)}
    out: list[Seed] = []
    target_ids = {seed.id for seed in targets}
    for i, seed in enumerate(targets):
        row = by_index.get(i) or {}
        extra = dict(seed.extra)
        extra["prefilter"] = _digest(row)
        out.append(replace(seed, extra=extra))
    out.extend(seed for seed in seeds if seed.id not in target_ids)
    return out, estimate, None


def _digest(row: dict) -> dict:
    if not row.get("ok"):
        err = row.get("error") or {}
        return {"ok": False, "error": err.get("error") or "batch_entry_failed"}
    fields = row.get("fields") or {}
    digest = {"ok": True}
    for name in PREFILTER_FIELDS:
        payload = fields.get(name) or {}
        digest[name] = {
            "value": payload.get("value"),
            "source": payload.get("source"),
            "status": payload.get("status"),
        }
    return digest
