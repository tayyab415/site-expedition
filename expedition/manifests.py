"""Reviewed, data-only manifests for constrained Custom Missions.

Custom Missions may compose capabilities already reviewed for this prototype.
They cannot load arbitrary files, discover sources, or name executable code.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from expedition.plan import FIELDS


MANIFEST_SCHEMA_VERSION = 1
MANIFESTS_DIR = Path(__file__).resolve().parent / "data" / "manifests"
MAX_MANIFEST_BYTES = 64 * 1024

# Only manifests named here have passed review.  In particular, callers cannot
# turn a path or URL into a reviewed manifest by passing it to the loader.
REVIEWED_MANIFESTS: dict[str, str] = {
    "logistics-resilience": "logistics-resilience.v1.json",
}

# These skills are already part of the frozen MVP capability vocabulary and
# have a shipped execution/presentation path. Deferred source-scout and other
# unproved capabilities intentionally do not appear here.
ALLOWED_CUSTOM_SKILLS = frozenset(
    {
        "resolve-site",
        "screen-site-core",
        "flood-rewind",
        "grid-readiness",
        "route-reality",
        "scene-context",
        "skeptic-review",
        "compare-candidates",
        "farm-history",
    }
)
REQUIRED_CUSTOM_SKILLS = frozenset(
    {"resolve-site", "screen-site-core", "skeptic-review"}
)

# FIELDS is the deterministic Mireye /fetch catalog already accepted by the
# built-in recipes. A Custom manifest cannot expand that data-source boundary.
ALLOWED_MIREYE_FIELDS = frozenset(
    field_id for mission_fields in FIELDS.values() for field_id in mission_fields
)
ALLOWED_HARD_CONSTRAINTS = frozenset(
    {"not_mapped_sfha", "must_be_cultivated"}
)
ALLOWED_GAPS = frozenset(
    {
        "market_availability",
        "electrical_capacity",
        "truck_ingress",
        "zoning_permission",
        "water_right",
        "yield",
        "enterprise_fiber_redundancy",
        "water_capacity",
        "route_time",
    }
)

_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "manifest_id",
        "manifest_version",
        "title",
        "description",
        "skills",
        "fields",
        "hard_constraints",
        "preferences",
        "gaps",
    }
)
_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_VERSION_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")


class ManifestValidationError(ValueError):
    """A Custom Mission manifest escaped its reviewed data boundary."""


@dataclass(frozen=True)
class CustomMissionManifest:
    schema_version: int
    manifest_id: str
    manifest_version: str
    title: str
    description: str
    skills: tuple[str, ...]
    fields: tuple[str, ...]
    hard_constraints: tuple[str, ...]
    preferences: tuple[str, ...]
    gaps: tuple[str, ...]

    def plan_overrides(self) -> dict[str, list[str]]:
        """Return the validated values a MissionPlan compiler may consume.

        A fresh mutable copy is returned so callers cannot mutate the reviewed
        manifest cached on disk or widen the validation boundary accidentally.
        """

        return {
            "skills": list(self.skills),
            "fields": list(self.fields),
            "hard_constraints": list(self.hard_constraints),
            "preferences": list(self.preferences),
            "gaps_always": list(self.gaps),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "manifest_version": self.manifest_version,
            "title": self.title,
            "description": self.description,
            "skills": list(self.skills),
            "fields": list(self.fields),
            "hard_constraints": list(self.hard_constraints),
            "preferences": list(self.preferences),
            "gaps": list(self.gaps),
        }


def list_reviewed_manifests() -> list[dict[str, str]]:
    """Return safe metadata for the manifest picker, in stable ID order."""

    return [
        {
            "manifest_id": manifest.manifest_id,
            "manifest_version": manifest.manifest_version,
            "title": manifest.title,
            "description": manifest.description,
        }
        for manifest in (
            load_reviewed_manifest(manifest_id)
            for manifest_id in sorted(REVIEWED_MANIFESTS)
        )
    ]


def load_reviewed_manifest(manifest_id: str) -> CustomMissionManifest:
    """Load one manifest from the fixed, reviewed registry.

    ``manifest_id`` is deliberately not treated as a filename. This prevents
    path traversal, arbitrary local JSON, URLs, and runtime manifest discovery.
    """

    if not isinstance(manifest_id, str) or manifest_id not in REVIEWED_MANIFESTS:
        raise ManifestValidationError(f"manifest is not reviewed: {manifest_id!r}")

    path = MANIFESTS_DIR / REVIEWED_MANIFESTS[manifest_id]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ManifestValidationError(
            f"reviewed manifest {manifest_id!r} is unavailable"
        ) from exc
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestValidationError(
            f"reviewed manifest {manifest_id!r} exceeds {MAX_MANIFEST_BYTES} bytes"
        )
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(
            f"reviewed manifest {manifest_id!r} is not valid JSON"
        ) from exc
    return validate_manifest(payload, expected_id=manifest_id)


def validate_manifest(
    payload: Mapping[str, Any], *, expected_id: str | None = None
) -> CustomMissionManifest:
    """Validate untrusted data against the constrained manifest schema.

    Passing this function does not make a manifest reviewed. Only IDs accepted
    by :func:`load_reviewed_manifest` are approved for runtime selection.
    """

    if not isinstance(payload, Mapping):
        raise ManifestValidationError("manifest must be a JSON object")

    if any(not isinstance(key, str) for key in payload):
        raise ManifestValidationError("manifest keys must be strings")
    keys = frozenset(payload.keys())
    missing = sorted(_REQUIRED_KEYS - keys)
    unknown = sorted(keys - _REQUIRED_KEYS)
    if missing:
        raise ManifestValidationError(f"manifest is missing keys: {', '.join(missing)}")
    if unknown:
        raise ManifestValidationError(
            "manifest contains unreviewed keys (sources, discovery, and code "
            f"references are forbidden): {', '.join(unknown)}"
        )

    schema_version = payload["schema_version"]
    if type(schema_version) is not int or schema_version != MANIFEST_SCHEMA_VERSION:
        raise ManifestValidationError(
            f"schema_version must be {MANIFEST_SCHEMA_VERSION}"
        )

    manifest_id = _string(payload, "manifest_id", maximum=64)
    if not _ID_RE.fullmatch(manifest_id):
        raise ManifestValidationError("manifest_id must be a lowercase kebab-case ID")
    if expected_id is not None and manifest_id != expected_id:
        raise ManifestValidationError(
            f"manifest ID {manifest_id!r} does not match reviewed ID {expected_id!r}"
        )

    manifest_version = _string(payload, "manifest_version", maximum=32)
    if not _VERSION_RE.fullmatch(manifest_version):
        raise ManifestValidationError("manifest_version must be semantic x.y.z")

    title = _string(payload, "title", maximum=100)
    description = _string(payload, "description", maximum=500)
    skills = _string_list(payload, "skills", maximum=16)
    fields = _string_list(payload, "fields", maximum=32)
    hard_constraints = _string_list(payload, "hard_constraints", maximum=8)
    preferences = _string_list(payload, "preferences", maximum=12)
    gaps = _string_list(payload, "gaps", maximum=16)

    _only_allowed("skills", skills, ALLOWED_CUSTOM_SKILLS)
    absent_base_skills = sorted(REQUIRED_CUSTOM_SKILLS - set(skills))
    if absent_base_skills:
        raise ManifestValidationError(
            "skills are missing required reviewed capabilities: "
            + ", ".join(absent_base_skills)
        )
    _only_allowed("fields", fields, ALLOWED_MIREYE_FIELDS)
    if not fields:
        raise ManifestValidationError("fields must contain at least one Mireye field")
    _only_allowed("hard_constraints", hard_constraints, ALLOWED_HARD_CONSTRAINTS)
    _only_allowed("preferences", preferences, ALLOWED_MIREYE_FIELDS)
    _only_allowed("gaps", gaps, ALLOWED_GAPS)

    fields_set = set(fields)
    preference_only_fields = sorted(set(preferences) - fields_set)
    if preference_only_fields:
        raise ManifestValidationError(
            "preferences must also be selected Mireye fields: "
            + ", ".join(preference_only_fields)
        )
    if "not_mapped_sfha" in hard_constraints and not fields_set.intersection(
        {"fema_flood_zone", "within_floodplain_polygon"}
    ):
        raise ManifestValidationError(
            "not_mapped_sfha requires fema_flood_zone or within_floodplain_polygon"
        )
    if "must_be_cultivated" in hard_constraints and "is_cultivated" not in fields_set:
        raise ManifestValidationError(
            "must_be_cultivated requires the is_cultivated Mireye field"
        )
    if "route-reality" in skills and "route_time" not in gaps:
        raise ManifestValidationError(
            "route-reality requires route_time as an honest Verification Gap"
        )

    return CustomMissionManifest(
        schema_version=schema_version,
        manifest_id=manifest_id,
        manifest_version=manifest_version,
        title=title,
        description=description,
        skills=skills,
        fields=fields,
        hard_constraints=hard_constraints,
        preferences=preferences,
        gaps=gaps,
    )


def _string(payload: Mapping[str, Any], key: str, *, maximum: int) -> str:
    value = payload[key]
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ManifestValidationError(f"{key} must be a non-empty trimmed string")
    if len(value) > maximum:
        raise ManifestValidationError(f"{key} must be at most {maximum} characters")
    return value


def _string_list(
    payload: Mapping[str, Any], key: str, *, maximum: int
) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list):
        raise ManifestValidationError(f"{key} must be a JSON array")
    if len(value) > maximum:
        raise ManifestValidationError(f"{key} may contain at most {maximum} entries")
    if any(not isinstance(item, str) or not item for item in value):
        raise ManifestValidationError(f"{key} entries must be non-empty strings")
    if len(set(value)) != len(value):
        raise ManifestValidationError(f"{key} must not contain duplicates")
    return tuple(value)


def _only_allowed(name: str, values: tuple[str, ...], allowed: frozenset[str]) -> None:
    rejected = sorted(set(values) - allowed)
    if rejected:
        if "source-scout" in rejected:
            raise ManifestValidationError(
                "source-scout is forbidden: Custom Missions cannot perform arbitrary source discovery"
            )
        raise ManifestValidationError(
            f"{name} contain values outside the reviewed catalog: {', '.join(rejected)}"
        )
