"""Region Expedition: aggregate probe facts and rank metros.

Mireye has no region search. Every catalog field is a point. This module is
the aggregation job that sits in front of site screening:

- inventory is the 11 atomic metros in ``data/region_catalog.json``
  (``texas_triangle`` is a search envelope, not a comparable metro)
- evidence is replayed probe facts plus county ACS-style employment
- hard gates: geography allowlist, and Home + flood-intolerant + mapped
  SFHA share >= 0.5
- ranking is lexicographic on flood share (when intolerant) then declared
  preference bands, the same rule as site comparison
- labor is INFORM only, never a sort key, and is omitted for Home
- no composite suitability number

Probe failures do not become zeros. A metric with no known probes is UNKNOWN
and sorts last.
"""

from __future__ import annotations

import json
from pathlib import Path
from expedition.evidence import utc_now
from expedition.plan import SEARCH_REGIONS


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "data" / "region_catalog.json"
REPLAY_PATH = ROOT / "data" / "fixtures" / "regions" / "replay.json"

ROAD_CLASS_RANK = {
    "motorway": 0,
    "trunk": 1,
    "primary": 2,
    "secondary": 3,
    "tertiary": 4,
    "residential": 5,
    "service": 6,
}
DROUGHT_RANK = {"None": 0, "D0": 1, "D1": 2, "D2": 3, "D3": 4, "D4": 5}
HOME_FLOOD_VETO_SHARE = 0.5
WEIGHT_RANK = {"priority": 0, "important": 1, "useful": 2}

# Higher raw values are better; the sort key negates them.
HIGHER_BETTER = frozenset({"soil_awc", "fiber_provider_count"})

PREFERENCE_METRIC = {
    "major_road_access": "road_class_rank",
    "road_access": "road_class_rank",
    "rail_access": "rail_distance_m",
    "grid_proximity": "grid_distance_m",
    "route_time": "route_time_s",
    "soil_water_capacity": "soil_awc",
    "drought_context": "drought_rank",
    "hospital_access": "hospital_distance_m",
    "lower_slope": "slope_degrees",
    "lower_wildfire": "wildfire_frequency",
    "fiber_context": "fiber_provider_count",
    "lower_heat": "heat_days_above_32c",
}

LABOR_FIELD = "civilian_employed"


def load_catalog(path: Path | None = None) -> dict:
    return json.loads((path or CATALOG_PATH).read_text(encoding="utf-8"))


def load_replay(path: Path | None = None) -> dict:
    return json.loads((path or REPLAY_PATH).read_text(encoding="utf-8"))


def locate_inventory(catalog: dict | None = None) -> list[str]:
    data = catalog or load_catalog()
    return list(data["locate_inventory"])


def region_record(region_id: str, catalog: dict | None = None) -> dict:
    data = catalog or load_catalog()
    row = (data.get("regions") or {}).get(region_id)
    if not row:
        raise KeyError(f"unknown region {region_id}")
    return row


def expand_allowlist(
    seeds: list[str] | None,
    *,
    geography_band: str = "selected_region",
    catalog: dict | None = None,
) -> list[str]:
    """Return the metros that may be ranked.

    ``None`` or empty seeds means the full locate inventory. Adjacent /
    statewide only expand inside the same state as the seeds.
    """
    data = catalog or load_catalog()
    inventory = list(data["locate_inventory"])
    if not seeds:
        return inventory
    wanted = []
    seen: set[str] = set()
    for seed in seeds:
        if seed == "texas_triangle":
            extra = list(data["state_regions"]["TX"])
        elif seed in data["regions"]:
            extra = [seed]
        else:
            continue
        for region_id in extra:
            if region_id in seen or region_id not in inventory:
                continue
            seen.add(region_id)
            wanted.append(region_id)
    if geography_band == "selected_region" or not wanted:
        return wanted or inventory
    expanded = list(wanted)
    if geography_band in {"adjacent_regions", "statewide"}:
        for region_id in list(wanted):
            row = data["regions"][region_id]
            if geography_band == "adjacent_regions":
                neighbors = row.get("adjacent") or []
            else:
                neighbors = data["state_regions"].get(row["state"]) or []
            for neighbor in neighbors:
                if neighbor in seen or neighbor not in inventory:
                    continue
                seen.add(neighbor)
                expanded.append(neighbor)
    return expanded


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _share(flags: list[bool]) -> float | None:
    return (sum(1 for flag in flags if flag) / len(flags)) if flags else None


def _min(values: list[float]) -> float | None:
    return min(values) if values else None


def _max(values: list[float]) -> float | None:
    return max(values) if values else None


def _metric(value, *, method: str, unit: str | None, known: int, total: int) -> dict:
    kind = "UNKNOWN" if value is None else "PROXY"
    return {
        "value": value,
        "unit": unit,
        "method": method,
        "kind": kind,
        "known_probes": known,
        "probe_count": total,
    }


def aggregate_region(
    region_id: str,
    *,
    catalog: dict | None = None,
    replay: dict | None = None,
    mission: str = "warehouse",
) -> dict:
    """Fold probe facts into region metrics with explicit methods."""
    data = catalog or load_catalog()
    evidence = replay or load_replay()
    row = region_record(region_id, data)
    probes = list(row["probes"])
    probe_facts = evidence.get("probes") or {}
    county_facts = evidence.get("counties") or {}
    total = len(probes)

    def collect(field: str) -> list:
        out = []
        for probe in probes:
            fact = probe_facts.get(probe["id"]) or {}
            if field not in fact:
                continue
            value = fact[field]
            if value is None:
                continue
            out.append(value)
        return out

    sfha_flags = [bool(v) for v in collect("mapped_sfha")]
    road_ranks = [
        ROAD_CLASS_RANK[str(v).lower()]
        for v in collect("nearest_major_road_class")
        if str(v).lower() in ROAD_CLASS_RANK
    ]
    droughts = [
        DROUGHT_RANK[str(v)]
        for v in collect("drought_category")
        if str(v) in DROUGHT_RANK
    ]
    metrics = {
        "mapped_sfha_share": _metric(
            _share(sfha_flags), method="share", unit="1", known=len(sfha_flags), total=total
        ),
        "coast_distance_m": _metric(
            _min([float(v) for v in collect("coast_distance_m")]),
            method="min",
            unit="m",
            known=len(collect("coast_distance_m")),
            total=total,
        ),
        "road_class_rank": _metric(
            _min([float(v) for v in road_ranks]),
            method="min",
            unit=None,
            known=len(road_ranks),
            total=total,
        ),
        "rail_distance_m": _metric(
            _min([float(v) for v in collect("nearest_long_haul_rail_corridor_distance_m")]),
            method="min",
            unit="m",
            known=len(collect("nearest_long_haul_rail_corridor_distance_m")),
            total=total,
        ),
        "grid_distance_m": _metric(
            _min([float(v) for v in collect("nearest_substation_distance_m")]),
            method="min",
            unit="m",
            known=len(collect("nearest_substation_distance_m")),
            total=total,
        ),
        "heat_days_above_32c": _metric(
            _mean([float(v) for v in collect("days_above_32c_annual_count")]),
            method="mean",
            unit="days",
            known=len(collect("days_above_32c_annual_count")),
            total=total,
        ),
        "wildfire_frequency": _metric(
            _max([float(v) for v in collect("wildfire_annual_frequency")]),
            method="max",
            unit="1/year",
            known=len(collect("wildfire_annual_frequency")),
            total=total,
        ),
        "slope_degrees": _metric(
            _mean([float(v) for v in collect("slope_degrees")]),
            method="mean",
            unit="deg",
            known=len(collect("slope_degrees")),
            total=total,
        ),
        "cultivated_share": _metric(
            _share([bool(v) for v in collect("is_cultivated")]),
            method="share",
            unit="1",
            known=len(collect("is_cultivated")),
            total=total,
        ),
        "drought_rank": _metric(
            _max([float(v) for v in droughts]) if droughts else None,
            method="max",
            unit=None,
            known=len(droughts),
            total=total,
        ),
        "soil_awc": _metric(
            _mean([float(v) for v in collect("soil_available_water_capacity")]),
            method="mean",
            unit=None,
            known=len(collect("soil_available_water_capacity")),
            total=total,
        ),
        "fiber_provider_count": _metric(
            _mean([float(v) for v in collect("fiber_provider_count")]),
            method="mean",
            unit=None,
            known=len(collect("fiber_provider_count")),
            total=total,
        ),
        "hospital_distance_m": _metric(
            _min([float(v) for v in collect("nearest_hospital_distance_m")]),
            method="min",
            unit="m",
            known=len(collect("nearest_hospital_distance_m")),
            total=total,
        ),
        "route_time_s": _metric(None, method="none", unit="s", known=0, total=total),
    }

    counties = []
    employed = 0
    labor_force = 0
    known_counties = 0
    for county in row.get("counties") or []:
        fact = county_facts.get(county["geoid"]) or {}
        employed_n = fact.get("civilian_employed")
        force_n = fact.get("civilian_labor_force")
        if isinstance(employed_n, int):
            employed += employed_n
            known_counties += 1
        if isinstance(force_n, int):
            labor_force += force_n
        counties.append(
            {
                "geoid": county["geoid"],
                "name": fact.get("name") or county["name"],
                "civilian_employed": employed_n,
                "civilian_labor_force": force_n,
                "mean_commute_minutes": fact.get("mean_commute_minutes"),
                "workers_available": None,
            }
        )
    labor = {
        "value": employed if known_counties else None,
        "unit": "people",
        "method": "sum",
        "kind": "UNKNOWN" if not known_counties else "PROXY",
        "known_probes": known_counties,
        "probe_count": len(row.get("counties") or []),
        "counties": counties,
        "civilian_labor_force": labor_force if known_counties else None,
        "workers_available": None,
        "scale": "county",
        "notes": (
            "County ACS-style employment context. Not a hiring claim, not a "
            "complete MSA labor shed, never used to rank Home."
        ),
    }
    if mission != "home":
        metrics[LABOR_FIELD] = labor

    unknowns = [name for name, metric in metrics.items() if metric["kind"] == "UNKNOWN"]
    return {
        "region_id": region_id,
        "label": row["label"],
        "state": row["state"],
        "geography_family": row["geography_family"],
        "centroid": list(row["centroid"]),
        "fly": list(row["fly"]),
        "probe_ids": [probe["id"] for probe in probes],
        "probe_count": total,
        "metrics": metrics,
        "unknowns": unknowns,
        "spatial_support": {
            "kind": "region",
            "crs": "EPSG:4326",
            "region_id": region_id,
            "probe_ids": [probe["id"] for probe in probes],
        },
        "evidence_status": evidence.get("status") or "replay",
        "source": evidence.get("source"),
        "source_url": evidence.get("source_url"),
        "fetched_at": evidence.get("fetched_at") or utc_now(),
    }


def _sort_value(metric: dict | None, field: str) -> float:
    if not metric or metric.get("kind") == "UNKNOWN" or metric.get("value") is None:
        return float("inf")
    value = float(metric["value"])
    if field in HIGHER_BETTER:
        return -value
    return value


def _declared_preferences(preferences: list[dict] | None) -> list[dict]:
    declared = [
        row
        for row in (preferences or [])
        if isinstance(row, dict)
        and row.get("weight") in WEIGHT_RANK
        and row.get("id") in PREFERENCE_METRIC
    ]
    declared.sort(key=lambda row: (WEIGHT_RANK[row["weight"]], list(preferences or []).index(row)))
    return declared


def _preference_key(bundle: dict, preferences: list[dict] | None, flood_intolerant: bool) -> tuple:
    metrics = bundle["metrics"]
    parts: list[float] = []
    basis = []
    if flood_intolerant:
        parts.append(_sort_value(metrics.get("mapped_sfha_share"), "mapped_sfha_share"))
        basis.append("mapped SFHA share among probes")
    for row in _declared_preferences(preferences):
        field = PREFERENCE_METRIC[row["id"]]
        parts.append(_sort_value(metrics.get(field), field))
        basis.append(f"{row['id']} ({row['weight']})")
    return tuple(parts), basis


def _veto_reason(bundle: dict, *, mission: str, flood_intolerant: bool) -> str | None:
    share = (bundle["metrics"].get("mapped_sfha_share") or {}).get("value")
    if (
        mission == "home"
        and flood_intolerant
        and isinstance(share, (int, float))
        and share >= HOME_FLOOD_VETO_SHARE
    ):
        return (
            f"Home + flood-intolerant: mapped SFHA share {share:.2f} "
            f"is at or above {HOME_FLOOD_VETO_SHARE:.2f} of probes"
        )
    return None


def _counterfactual(bundle: dict, *, mission: str, flood_intolerant: bool) -> str:
    share = (bundle["metrics"].get("mapped_sfha_share") or {}).get("value")
    if mission == "home" and flood_intolerant and isinstance(share, (int, float)) and share >= HOME_FLOOD_VETO_SHARE:
        return "Would survive region ranking if flood-intolerant were off."
    if flood_intolerant and isinstance(share, (int, float)) and share > 0:
        return (
            f"{int(round(share * bundle['probe_count']))} of "
            f"{bundle['probe_count']} probes sit in mapped SFHA. "
            "That does not veto the metro; site screening still can."
        )
    rail = (bundle["metrics"].get("rail_distance_m") or {}).get("value")
    if isinstance(rail, (int, float)):
        return f"Nearest replayed rail probe is {int(rail)} m. Not a siding or a listing."
    return "Region facts are probe aggregates. Pins inside still need screening."


def _row(
    bundle: dict,
    *,
    mission: str,
    preferences: list[dict] | None,
    flood_intolerant: bool,
) -> dict:
    veto = _veto_reason(bundle, mission=mission, flood_intolerant=flood_intolerant)
    key, basis = _preference_key(bundle, preferences, flood_intolerant and not veto)
    metrics_out = {
        name: {
            "value": metric.get("value"),
            "unit": metric.get("unit"),
            "method": metric.get("method"),
            "kind": metric.get("kind"),
            "known_probes": metric.get("known_probes"),
            "probe_count": metric.get("probe_count"),
        }
        for name, metric in bundle["metrics"].items()
    }
    if LABOR_FIELD in bundle["metrics"]:
        labor = bundle["metrics"][LABOR_FIELD]
        metrics_out[LABOR_FIELD] = {
            **metrics_out[LABOR_FIELD],
            "workers_available": None,
            "scale": "county",
            "notes": labor.get("notes"),
            "counties": labor.get("counties"),
        }
    return {
        "region_id": bundle["region_id"],
        "label": bundle["label"],
        "state": bundle["state"],
        "status": "vetoed" if veto else "survivor",
        "veto_reason": veto,
        "centroid": bundle["centroid"],
        "fly": bundle["fly"],
        "probe_ids": bundle["probe_ids"],
        "probe_count": bundle["probe_count"],
        "metrics": metrics_out,
        "preference_basis": ["not vetoed", *basis] if not veto else ["vetoed", *basis],
        "preference_sort": list(key),
        "unknowns": bundle["unknowns"],
        "counterfactual": _counterfactual(
            bundle, mission=mission, flood_intolerant=flood_intolerant
        ),
        "spatial_support": bundle["spatial_support"],
        "source": bundle["source"],
        "source_url": bundle["source_url"],
        "fetched_at": bundle["fetched_at"],
        "evidence_status": bundle["evidence_status"],
    }


def _ordered(rows: list[dict]) -> list[dict]:
    def key(row: dict) -> tuple:
        vetoed = 1 if row["status"] == "vetoed" else 0
        sort = tuple(row.get("preference_sort") or ())
        return (vetoed, *sort, row["region_id"])

    ranked = sorted(rows, key=key)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def _sensitivity(rows: list[dict], preferences: list[dict] | None) -> list[dict]:
    declared = _declared_preferences(preferences)
    if len(rows) < 2 or not declared:
        return []
    top = rows[0]["region_id"]
    out = []
    for row in declared:
        if row["weight"] != "priority":
            continue
        resorted = _drop_preference_order(rows, preferences, row["id"])
        if not resorted:
            continue
        new_top = next(
            (item["region_id"] for item in resorted if item["status"] != "vetoed"),
            resorted[0]["region_id"],
        )
        out.append(
            {
                "dropped": row["id"],
                "from_weight": row["weight"],
                "to_weight": "useful",
                "top_was": top,
                "top_becomes": new_top,
                "order_changed": new_top != top,
            }
        )
    return out


def _drop_preference_order(
    rows: list[dict], preferences: list[dict] | None, dropped_id: str
) -> list[dict]:
    perturbed = []
    for item in preferences or []:
        if item.get("id") == dropped_id:
            perturbed.append({**item, "weight": "useful"})
        else:
            perturbed.append(item)
    rebuilt = []
    for candidate in rows:
        if candidate["status"] == "vetoed":
            rebuilt.append(candidate)
            continue
        fake = {
            "metrics": candidate["metrics"],
            "region_id": candidate["region_id"],
        }
        # Preserve flood-intolerant leading key if it was used.
        original = list(candidate.get("preference_sort") or ())
        flood_prefix = ()
        declared = _declared_preferences(preferences)
        if original and len(original) == len(declared) + 1:
            flood_prefix = (original[0],)
        rest, _ = _preference_key(fake, perturbed, False)
        rebuilt.append({**candidate, "preference_sort": [*flood_prefix, *rest]})
    return _ordered(rebuilt)


def rank_regions(
    mission: str,
    *,
    preferences: list[dict] | None = None,
    allowlist: list[str] | None = None,
    flood_intolerant: bool | None = None,
    geography_band: str = "selected_region",
    catalog: dict | None = None,
    replay: dict | None = None,
) -> dict:
    """Rank metros for a compiled Mission Plan. Spends no Mireye credits."""
    mission = (mission or "warehouse").replace(" ", "_").lower()
    if flood_intolerant is None:
        flood_intolerant = mission in {"warehouse", "home", "data_center"}
    if mission == "home":
        preferences = [
            row
            for row in (preferences or [])
            if isinstance(row, dict) and row.get("id") not in {"labor_access", "labor"}
        ]
    data = catalog or load_catalog()
    evidence = replay or load_replay()
    region_ids = expand_allowlist(
        allowlist, geography_band=geography_band, catalog=data
    )
    rows = [
        _row(
            aggregate_region(
                region_id, catalog=data, replay=evidence, mission=mission
            ),
            mission=mission,
            preferences=preferences,
            flood_intolerant=flood_intolerant,
        )
        for region_id in region_ids
    ]
    ranked = _ordered(rows)
    survivors = [row for row in ranked if row["status"] == "survivor"]
    vetoed = [row for row in ranked if row["status"] == "vetoed"]
    packet = {
        "stage": "locate",
        "mission": mission,
        "flood_intolerant": flood_intolerant,
        "allowlist": region_ids,
        "geography_band": geography_band,
        "regions": ranked,
        "survivors": [row["region_id"] for row in survivors],
        "vetoed": [
            {"region_id": row["region_id"], "reason": row["veto_reason"]}
            for row in vetoed
        ],
        "top_region_ids": [row["region_id"] for row in survivors[:3]],
        "sensitivity": _sensitivity(survivors, preferences),
        "preference_basis": survivors[0]["preference_basis"] if survivors else [],
        "credits": {"spent": 0, "mireye": False, "note": "Region rank uses replayed probe aggregates. Zero Mireye credits."},
        "honesty": (
            "Metros are not listings. Pins inside a survivor stay POTENTIAL. "
            "Labor never ranks Home and never claims workers are available. "
            "This is an ordered comparison, not a suitability score."
        ),
        "fetched_at": evidence.get("fetched_at") or utc_now(),
    }
    return _json_safe(packet)


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    number = float(value)
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return value if isinstance(value, int) and not isinstance(value, bool) else number


def _json_safe(obj):
    if isinstance(obj, dict):
        return {key: _json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(value) for value in obj]
    if isinstance(obj, tuple):
        return [_json_safe(value) for value in obj]
    return _finite_number(obj)


def default_search_region(allowlist: list[str] | None, ranked: dict | None = None) -> str:
    if ranked and ranked.get("top_region_ids"):
        return ranked["top_region_ids"][0]
    if not allowlist:
        return "texas_triangle"
    texas = set(load_catalog()["state_regions"].get("TX") or [])
    if len(allowlist) > 1 and set(allowlist) <= texas:
        return "texas_triangle"
    if allowlist[0] in SEARCH_REGIONS:
        return allowlist[0]
    if set(allowlist) <= texas:
        return "texas_triangle"
    return "texas_triangle"
