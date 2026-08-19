"""Evidence atoms, gaps, and independence rules."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


KINDS = frozenset(
    {"FACT", "ABSENT", "FAILED", "PROXY", "MODEL", "PRESENTATION", "UNKNOWN"}
)
STATUSES = frozenset(
    {"live", "replay", "stale", "blocked", "partial", "failed", "absent"}
)
EFFECTS = frozenset({"VETO", "GATE", "INFORM", "UNKNOWN", "NONE"})

FAMILY = {
    "fema_flood_zone": ("FEMA_NFHL", "FEMA_NFHL"),
    "within_floodplain_polygon": ("FEMA_NFHL", "FEMA_NFHL"),
    "intersects_wetland": ("USFWS_NWI", "USFWS_NWI"),
    "surface_water_permanence_pct": ("JRC_GSW", "JRC_GSW"),
    "jrc_monthly_water_freq": ("JRC_GSW", "JRC_GSW"),
    "elevation": ("USGS_3DEP", "USGS_3DEP"),
    "nasadem_elevation": ("DEM_OTHER", "NASADEM"),
    "is_cultivated": ("USDA_CDL", "USDA_CDL"),
    "dominant_crop_5y": ("USDA_CDL", "USDA_CDL"),
    "nearest_major_road_distance_m": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "nearest_major_road_class": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "nearest_long_haul_rail_corridor_distance_m": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "nearest_substation_distance_m": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "nearest_substation_max_voltage_kv": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "nearest_hazardous_facility_distance_m": ("EPA_ECHO", "EPA"),
    "nearest_superfund_distance_m": ("EPA_ECHO", "EPA"),
    "epa_rmp_facility_record": ("EPA_ECHO", "EPA"),
    "fiber_broadband_available": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "within_water_service_area": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "within_sewer_service_area": ("MIREYE_INFRA", "MIREYE_INFRA"),
    "days_above_32c_annual_count": ("MIREYE_INFRA", "MIREYE_CLIMATE"),
    "route_duration_s": ("GOOGLE_ROUTES", "GOOGLE_ROUTES"),
    "aerial_video_id": ("GOOGLE_VISUAL", "GOOGLE_VISUAL"),
    "maps_3d_scene": ("GOOGLE_VISUAL", "GOOGLE_VISUAL"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _datetime_utc(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


_DURATION = re.compile(
    r"^P(?:(?P<weeks>\d+(?:\.\d+)?)W)?"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$",
    re.IGNORECASE,
)


def _ttl_expiry(fetched_at: str | datetime | None, ttl: Any) -> datetime | None:
    """Return an expiry for Mireye seconds, ISO durations, or an absolute clock."""
    if ttl is None or ttl == "":
        return None
    if isinstance(ttl, bool):
        return None
    if isinstance(ttl, (int, float)) or (
        isinstance(ttl, str) and re.fullmatch(r"\d+(?:\.\d+)?", ttl.strip())
    ):
        fetched = _datetime_utc(fetched_at)
        return fetched + timedelta(seconds=float(ttl)) if fetched else None
    if not isinstance(ttl, str):
        return None
    duration = _DURATION.fullmatch(ttl.strip())
    if duration:
        fetched = _datetime_utc(fetched_at)
        if not fetched:
            return None
        amounts = {
            key: float(value or 0)
            for key, value in duration.groupdict().items()
        }
        delta = timedelta(
            weeks=amounts["weeks"],
            days=amounts["days"],
            hours=amounts["hours"],
            minutes=amounts["minutes"],
            seconds=amounts["seconds"],
        )
        return fetched + delta
    return _datetime_utc(ttl)


def cache_runtime_status(
    fetched_at: str | datetime | None,
    ttl: Any,
    *,
    now: str | datetime | None = None,
) -> str:
    """Classify a cache hit as replay or stale, failing closed on a bad TTL."""
    if ttl is None or ttl == "":
        return "replay"
    expiry = _ttl_expiry(fetched_at, ttl)
    current = _datetime_utc(now) if now is not None else datetime.now(timezone.utc)
    if expiry is None or current is None:
        return "stale"
    return "stale" if expiry <= current else "replay"


def geometry_hash(lat: float, lng: float, extra: str = "") -> str:
    raw = f"{lat:.7f},{lng:.7f}|{extra}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def cache_identity(
    provider: str,
    dataset: str,
    field_id: str,
    transform: str,
    geom: str,
    support: str,
    window: str = "",
) -> str:
    raw = "|".join([provider, dataset, field_id, transform, geom, support, window])
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class EvidenceAtom:
    atom_id: str
    candidate_id: str
    question_id: str
    field_id: str
    kind: str
    status: str
    decision_effect: str
    value: Any
    unit: str | None
    source: str
    source_url: str | None
    source_family: str
    independence_group: str
    authority: str
    support: dict
    observed_at: str | None
    fetched_at: str
    dataset_vintage: str | None
    ttl: str | None
    confidence: Any
    notes: str | None
    failure: dict | None
    cost: dict
    citation: dict
    transform_version: str
    cache_identity: str
    live_label: str
    partial_failures: list = field(default_factory=list)
    recipe_id: str | None = None
    license: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"bad kind {self.kind}")
        if self.status not in STATUSES:
            raise ValueError(f"bad status {self.status}")
        if self.decision_effect not in EFFECTS:
            raise ValueError(f"bad effect {self.decision_effect}")
        if self.kind == "PRESENTATION" and self.decision_effect != "NONE":
            raise ValueError("PRESENTATION must be NONE")
        if self.live_label == "live" and self.status != "live":
            raise ValueError("live_label live requires status live")
        if self.status == "live" and self.live_label != "live":
            raise ValueError("status live requires live_label live")

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def usable_as_pass(self) -> bool:
        """Whether this atom is eligible to support a pass before contradictions."""
        return (
            self.kind == "FACT"
            and self.authority == "authoritative"
            and self.status in {"live", "replay"}
            and self.decision_effect != "NONE"
        )


@dataclass
class Contradiction:
    contradiction_id: str
    candidate_id: str
    question_id: str
    atom_ids: list[str]
    same_independence_group: bool
    geometry_aligned: bool
    time_aligned: bool
    resolution: str
    notes: str

    def __post_init__(self) -> None:
        if self.resolution not in {"keep_both", "verification_gap"}:
            raise ValueError(f"bad contradiction resolution {self.resolution}")
        if len(self.atom_ids) < 2:
            raise ValueError("a contradiction requires at least two atoms")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerificationGap:
    gap_id: str
    candidate_id: str
    question_id: str
    missing_authority: str
    blocking: bool
    atom_ids: list[str]
    action: str

    def to_dict(self) -> dict:
        return asdict(self)


def family_for(field_id: str) -> tuple[str, str]:
    return FAMILY.get(field_id, ("UNKNOWN", field_id))


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return repr(value)


def _answer_key(atom: EvidenceAtom) -> tuple[str, str]:
    if atom.kind == "ABSENT":
        return ("ABSENT", "")
    return ("VALUE", _canonical(atom.value))


def detect_contradictions(atoms: list[EvidenceAtom]) -> list[Contradiction]:
    """Detect literal disagreements without inventing cross-field semantics.

    Atoms must answer the same Candidate Site question *and* field recipe. A
    Mission-specific semantic reconciler may later combine different fields,
    but comparing unrelated raw values here would create false contradictions.
    """
    groups: dict[tuple[str, str, str], list[EvidenceAtom]] = defaultdict(list)
    answer_kinds = {"FACT", "ABSENT", "PROXY", "MODEL"}
    for atom in atoms:
        if atom.kind in answer_kinds:
            groups[(atom.candidate_id, atom.question_id, atom.field_id)].append(atom)

    found: list[Contradiction] = []
    for (candidate_id, question_id, field_id), candidates in sorted(groups.items()):
        ordered = sorted(candidates, key=lambda atom: atom.atom_id)
        if len(ordered) < 2 or len({_answer_key(atom) for atom in ordered}) < 2:
            continue
        atom_ids = [atom.atom_id for atom in ordered]
        geometry_aligned = len({_canonical(atom.support) for atom in ordered}) == 1
        observed = {atom.observed_at for atom in ordered}
        time_aligned = len(observed) == 1
        same_group = len({atom.independence_group for atom in ordered}) == 1
        resolution = (
            "verification_gap" if geometry_aligned and time_aligned else "keep_both"
        )
        notes: list[str] = []
        if not geometry_aligned or not time_aligned:
            mismatches = []
            if not geometry_aligned:
                mismatches.append("geometry")
            if not time_aligned:
                mismatches.append("time")
            notes.append(
                f"Support mismatch ({' and '.join(mismatches)}); not a site-level contradiction."
            )
        else:
            notes.append(f"Conflicting values for {field_id}; keep every atom.")
        if same_group:
            notes.append("Same Independence Group cannot corroborate.")
        digest = hashlib.sha256(
            "|".join([candidate_id, question_id, field_id, *atom_ids]).encode()
        ).hexdigest()[:16]
        found.append(
            Contradiction(
                contradiction_id=f"contradiction:{digest}",
                candidate_id=candidate_id,
                question_id=question_id,
                atom_ids=atom_ids,
                same_independence_group=same_group,
                geometry_aligned=geometry_aligned,
                time_aligned=time_aligned,
                resolution=resolution,
                notes=" ".join(notes),
            )
        )
    return found


def atom_from_mireye_field(
    *,
    candidate_id: str,
    question_id: str,
    field_id: str,
    raw: dict,
    lat: float,
    lng: float,
    live: bool,
    effect: str,
    kind: str,
    authority: str,
    credits: float,
    transform_version: str = "mireye-field-v1",
    now: str | datetime | None = None,
    partial_failures: list | None = None,
    field_is_partial: bool = False,
) -> EvidenceAtom:
    src_family, group = family_for(field_id)
    status_in = (raw or {}).get("status") or "ok"
    value = (raw or {}).get("value")
    notes = (raw or {}).get("notes")
    err = (raw or {}).get("error")
    preserved_partial_failures = list(partial_failures or [])
    preserved_partial_failures.extend((raw or {}).get("partial_failures") or [])
    if status_in in {"failed", "error"}:
        kind, effect, status = "FAILED", "UNKNOWN", "failed"
        error_text = (
            err.get("message_public") or err.get("message") or str(err)
            if isinstance(err, dict)
            else str(err or "source failed")
        )
        lowered = error_text.lower()
        failure_class = "other"
        if "timeout" in lowered:
            failure_class = "timeout"
        elif "quota" in lowered or "credit" in lowered:
            failure_class = "quota"
        elif "auth" in lowered or (raw or {}).get("http_status") in {401, 403}:
            failure_class = "auth"
        elif "coverage" in lowered:
            failure_class = "no_coverage"
        failure = {
            "class": failure_class,
            "http_status": (raw or {}).get("http_status"),
            "retryable": bool((raw or {}).get("retryable")),
            "message_public": error_text,
        }
    elif status_in == "absent" or (
        value is None and status_in == "ok" and kind != "ABSENT"
    ):
        kind, effect, status = "ABSENT", "UNKNOWN", "absent"
        failure = None
    elif status_in == "partial" or field_is_partial:
        status = "partial"
        failure = None
    else:
        status = "live" if live else "replay"
        failure = None
    support = {
        "kind": "point",
        "crs": "EPSG:4326",
        "lat": lat,
        "lng": lng,
        "radius_m": None,
        "radius_purpose": None,
        "parcel_id": None,
        "parcel_grade": None,
        "geometry_hash": geometry_hash(lat, lng),
    }
    fetched = (raw or {}).get("fetched_at") or utc_now()
    ttl_value = (raw or {}).get("ttl")
    if ttl_value is None:
        ttl_value = (raw or {}).get("ttl_seconds")
    if not live and status in {"replay", "partial"} and value is not None:
        freshness = cache_runtime_status(fetched, ttl_value, now=now)
        if freshness == "stale":
            status = "stale"
    live_label = "live" if status == "live" else "replay"
    source = (raw or {}).get("source") or "mireye"
    atom_authority = "none" if status == "stale" else authority
    return EvidenceAtom(
        atom_id=f"{candidate_id}:{field_id}:{live_label}",
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind=kind,
        status=status,
        decision_effect=effect,
        value=value,
        unit=(raw or {}).get("unit"),
        source=source,
        source_url=(raw or {}).get("source_url"),
        source_family=src_family,
        independence_group=group,
        authority=atom_authority,
        support=support,
        observed_at=(raw or {}).get("observed_at"),
        fetched_at=fetched,
        dataset_vintage=(raw or {}).get("dataset_vintage"),
        ttl=str(ttl_value) if ttl_value is not None else None,
        confidence=(raw or {}).get("confidence"),
        notes=notes,
        failure=failure,
        cost={"credits": credits, "tokens": 0, "unit": "mireye_credit"},
        citation={
            "source": source,
            "source_url": (raw or {}).get("source_url"),
            "fetched_at": fetched,
            "dataset_vintage": (raw or {}).get("dataset_vintage"),
        },
        transform_version=transform_version,
        cache_identity=cache_identity(
            "mireye",
            "v0.14.0",
            field_id,
            transform_version,
            geometry_hash(lat, lng),
            "point",
        ),
        live_label=live_label,
        partial_failures=preserved_partial_failures,
    )


def dump_atoms(atoms: list[EvidenceAtom]) -> list[dict]:
    return [a.to_dict() for a in atoms]


def load_json(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
