"""Lawful, deterministic candidate acquisition for Find-a-Site Expeditions.

This module deliberately does not discover inventory.  It accepts a reviewed
curated/user/licensed pool, keeps site identity separate from listing identity,
and provides bounded replacement and geography-widening mechanics for the
Expedition controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import math
from typing import Iterable, Mapping, Sequence


class CandidateError(ValueError):
    """Base class for invalid candidate-pool input or transitions."""


class ProvenanceError(CandidateError):
    """Raised when a candidate label is unsupported by its provenance."""


class IdentityConflict(CandidateError):
    """Raised when one identifier points at incompatible physical sites."""


class CandidateLabel(str, Enum):
    LISTED = "LISTED"
    USER_SITE = "USER SITE"
    POTENTIAL = "POTENTIAL"


class SourceKind(str, Enum):
    CURATED = "curated"
    USER = "user"
    LICENSED = "licensed"


class IdentityResolution(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"


class ReplacementStatus(str, Enum):
    REPLACED = "replaced"
    WIDENED = "widened"
    EXHAUSTED = "exhausted"


def _timestamp(value: datetime | str, field_name: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProvenanceError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if not isinstance(value, datetime):
        raise ProvenanceError(f"{field_name} must be an ISO-8601 timestamp")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ProvenanceError(f"{field_name} must include a timezone")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class CandidateProvenance:
    """The source assertion behind one Candidate Site.

    ``authorized`` means the source is permitted for this use.  It is not a
    claim that the site is available.  Only licensed provenance with a listing
    identity and ``last_seen_at`` can support the LISTED label.
    """

    source: str
    source_kind: SourceKind
    captured_at: datetime | str
    authorization: str
    authorized: bool = True
    listing_id: str | None = None
    last_seen_at: datetime | str | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "source_kind", SourceKind(self.source_kind))
        except (TypeError, ValueError) as exc:
            raise ProvenanceError(f"unsupported candidate source kind: {self.source_kind}") from exc
        if not self.source.strip():
            raise ProvenanceError("candidate provenance requires a named source")
        if not self.authorization.strip():
            raise ProvenanceError("candidate provenance requires an authorization basis")
        if not self.authorized:
            raise ProvenanceError("unauthorized candidates cannot enter the lawful pool")
        object.__setattr__(self, "captured_at", _timestamp(self.captured_at, "captured_at"))
        if self.last_seen_at is not None:
            object.__setattr__(
                self, "last_seen_at", _timestamp(self.last_seen_at, "last_seen_at")
            )

    def supports(self, label: CandidateLabel) -> bool:
        if label is CandidateLabel.LISTED:
            return (
                self.source_kind is SourceKind.LICENSED
                and bool(self.listing_id)
                and self.last_seen_at is not None
            )
        if label is CandidateLabel.USER_SITE:
            return self.source_kind is SourceKind.USER
        return self.source_kind in {SourceKind.CURATED, SourceKind.LICENSED}


@dataclass(frozen=True)
class CandidateIdentity:
    """Resolved physical identity, kept distinct from market assertions."""

    location_id: str
    lat: float
    lng: float
    resolution: IdentityResolution = IdentityResolution.RESOLVED
    input_value: str | None = None
    geocode_precision: str | None = None
    parcel_id: str | None = None
    parcel_match_method: str | None = None
    parcel_match_distance_m: float | None = None
    boundary_source: str | None = None
    boundary_version: str | None = None
    building_id: str | None = None
    ambiguity: str | None = None

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "resolution", IdentityResolution(self.resolution))
        except (TypeError, ValueError) as exc:
            raise CandidateError(f"unsupported identity resolution: {self.resolution}") from exc
        if not self.location_id.strip():
            raise CandidateError("identity requires a stable location_id")
        if not math.isfinite(self.lat) or not -90 <= self.lat <= 90:
            raise CandidateError("latitude must be finite and between -90 and 90")
        if not math.isfinite(self.lng) or not -180 <= self.lng <= 180:
            raise CandidateError("longitude must be finite and between -180 and 180")
        if self.resolution is IdentityResolution.AMBIGUOUS and not self.ambiguity:
            raise CandidateError("ambiguous identity requires an explanation")
        if self.resolution is IdentityResolution.RESOLVED and self.ambiguity:
            raise CandidateError("resolved identity cannot retain an ambiguity explanation")
        if self.parcel_match_distance_m is not None and self.parcel_match_distance_m < 0:
            raise CandidateError("parcel_match_distance_m cannot be negative")

    @property
    def point_key(self) -> tuple[float, float]:
        # Roughly decimetre precision; this is identity dedupe, not cache identity.
        return (round(self.lat, 6), round(self.lng, 6))

    @property
    def site_keys(self) -> tuple[tuple[str, object], ...]:
        keys: list[tuple[str, object]] = [
            ("location", self.location_id),
            ("point", self.point_key),
        ]
        if self.parcel_id:
            keys.append(("parcel", self.parcel_id))
        if self.building_id:
            keys.append(("building", self.building_id))
        return tuple(keys)


@dataclass(frozen=True)
class CandidatePoolEntry:
    candidate_id: str
    name: str
    identity: CandidateIdentity
    label: CandidateLabel
    site_form: str
    provenance: CandidateProvenance
    band_id: str
    confirmation_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "label", CandidateLabel(self.label))
        except (TypeError, ValueError) as exc:
            raise ProvenanceError(f"unsupported candidate label: {self.label}") from exc
        if not self.candidate_id.strip():
            raise CandidateError("candidate_id cannot be empty")
        if not self.name.strip():
            raise CandidateError("candidate name cannot be empty")
        if not self.band_id.strip():
            raise CandidateError("candidate requires a Search Region band_id")
        if self.site_form not in {"existing_asset", "developable_land", "either"}:
            raise CandidateError(f"unsupported site_form: {self.site_form}")
        if not self.provenance.supports(self.label):
            raise ProvenanceError(
                f"{self.label.value} is not supported by {self.provenance.source_kind.value} "
                f"provenance for {self.candidate_id}"
            )

    @property
    def selectable(self) -> bool:
        return self.identity.resolution is IdentityResolution.RESOLVED

    def apply_listing_freshness(
        self, *, as_of: datetime, maximum_age: timedelta
    ) -> CandidatePoolEntry:
        """Downgrade an expired LISTED assertion without discarding the site."""

        if self.label is not CandidateLabel.LISTED:
            return self
        checked_at = _timestamp(as_of, "as_of")
        last_seen = self.provenance.last_seen_at
        assert isinstance(last_seen, datetime)  # Guaranteed by label validation.
        if checked_at - last_seen <= maximum_age:
            return self
        action = "Confirm current sale/lease availability with broker or owner"
        actions = self.confirmation_actions
        if action not in actions:
            actions += (action,)
        return replace(self, label=CandidateLabel.POTENTIAL, confirmation_actions=actions)

    def to_candidate_dict(self) -> dict:
        """Return the existing engine's candidate shape without losing provenance."""

        return {
            "id": self.candidate_id,
            "name": self.name,
            "lat": self.identity.lat,
            "lng": self.identity.lng,
            "label": self.label.value,
            "site_form": self.site_form,
            "source": self.provenance.source,
            "captured_at": self.provenance.captured_at.isoformat().replace("+00:00", "Z"),
            "band_id": self.band_id,
            "identity": {
                "location_id": self.identity.location_id,
                "parcel_id": self.identity.parcel_id,
                "building_id": self.identity.building_id,
                "resolution": self.identity.resolution.value,
            },
            "provenance": {
                "kind": self.provenance.source_kind.value,
                "authorization": self.provenance.authorization,
                "listing_id": self.provenance.listing_id,
                "last_seen_at": (
                    self.provenance.last_seen_at.isoformat().replace("+00:00", "Z")
                    if self.provenance.last_seen_at
                    else None
                ),
                "source_url": self.provenance.source_url,
            },
            "confirmation_actions": list(self.confirmation_actions),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object], *, band_id: str) -> CandidatePoolEntry:
        """Adapt the repository's reviewed JSON records into the typed contract."""

        try:
            label = CandidateLabel(str(record["label"]))
            candidate_id = str(record["id"])
            lat = float(record["lat"])
            lng = float(record["lng"])
            captured_at = record["captured_at"]
            source = str(record["source"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CandidateError("candidate record is missing a required typed field") from exc

        inferred_kind = {
            CandidateLabel.LISTED: SourceKind.LICENSED,
            CandidateLabel.USER_SITE: SourceKind.USER,
            CandidateLabel.POTENTIAL: SourceKind.CURATED,
        }[label]
        source_kind = SourceKind(str(record.get("source_kind", inferred_kind.value)))
        provenance = CandidateProvenance(
            source=source,
            source_kind=source_kind,
            captured_at=captured_at,  # type: ignore[arg-type]
            authorization=str(
                record.get(
                    "authorization",
                    "user_supplied" if label is CandidateLabel.USER_SITE else "reviewed_repository_fixture",
                )
            ),
            authorized=bool(record.get("authorized", True)),
            listing_id=str(record["listing_id"]) if record.get("listing_id") else None,
            last_seen_at=record.get("last_seen_at"),  # type: ignore[arg-type]
            source_url=str(record["source_url"]) if record.get("source_url") else None,
        )
        resolution = IdentityResolution(str(record.get("identity_resolution", "resolved")))
        identity = CandidateIdentity(
            location_id=str(record.get("location_id", f"point:{lat:.6f},{lng:.6f}")),
            lat=lat,
            lng=lng,
            resolution=resolution,
            input_value=str(record["address"]) if record.get("address") else None,
            geocode_precision=(
                str(record["geocode_precision"]) if record.get("geocode_precision") else None
            ),
            parcel_id=str(record["parcel_id"]) if record.get("parcel_id") else None,
            building_id=str(record["building_id"]) if record.get("building_id") else None,
            ambiguity=str(record["ambiguity"]) if record.get("ambiguity") else None,
        )
        return cls(
            candidate_id=candidate_id,
            name=str(record.get("name", candidate_id)),
            identity=identity,
            label=label,
            site_form=str(record.get("site_form", "either")),
            provenance=provenance,
            band_id=band_id,
        )


def normalize_inline_candidate(
    record: Mapping[str, object], *, candidate_id: str
) -> dict:
    """Validate a Check-a-Site request and force user-owned provenance.

    Inline HTTP input is never an inventory adapter.  It may identify a site
    the user wants checked, but it cannot assert that the site is listed or
    convert an arbitrary source string into reviewed/authorized provenance.
    """

    if not isinstance(record, Mapping):
        raise CandidateError("inline candidate must be an object")
    supplied_id = str(record.get("id") or candidate_id)
    if supplied_id != candidate_id:
        raise IdentityConflict("inline candidate id must match candidate_id")
    claimed_label = str(record.get("label") or CandidateLabel.USER_SITE.value)
    if claimed_label != CandidateLabel.USER_SITE.value:
        raise ProvenanceError("inline candidates must be labeled USER SITE")
    try:
        lat = float(record["lat"])
        lng = float(record["lng"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CandidateError("inline candidate requires numeric lat/lng") from exc
    if not math.isfinite(lat) or not math.isfinite(lng):
        raise CandidateError("inline candidate coordinates must be finite")
    if not 18 <= lat <= 72 or not -180 <= lng <= -65:
        raise CandidateError("inline candidate is outside the US Mireye envelope")
    site_form = str(record.get("site_form") or "either")
    source = str(record.get("source") or "user_supplied_request")
    entry = CandidatePoolEntry(
        candidate_id=candidate_id,
        name=str(record.get("name") or candidate_id),
        identity=CandidateIdentity(
            location_id=f"user-point:{lat:.6f},{lng:.6f}",
            lat=lat,
            lng=lng,
            input_value=str(record.get("address")) if record.get("address") else None,
        ),
        label=CandidateLabel.USER_SITE,
        site_form=site_form,
        provenance=CandidateProvenance(
            source=source,
            source_kind=SourceKind.USER,
            captured_at=datetime.now(timezone.utc),
            authorization="user_supplied_in_request",
        ),
        band_id="user_input",
    )
    return entry.to_candidate_dict()


@dataclass(frozen=True)
class SearchBand:
    band_id: str
    label: str

    def __post_init__(self) -> None:
        if not self.band_id.strip() or not self.label.strip():
            raise CandidateError("Search Region bands require an id and display label")


@dataclass(frozen=True)
class SearchRegion:
    """Ordered geography bands with an explicit widening permission and stop."""

    region_id: str
    label: str
    bands: tuple[SearchBand, ...]
    widening_allowed: bool = False
    stop_after_band_id: str | None = None
    country_code: str = "US"

    def __post_init__(self) -> None:
        if not self.region_id.strip() or not self.label.strip():
            raise CandidateError("Search Region requires an id and display label")
        if self.country_code != "US":
            raise CandidateError("the Site Expedition candidate pool is US-only")
        if not self.bands:
            raise CandidateError("Search Region requires at least one explicit band")
        band_ids = [band.band_id for band in self.bands]
        if len(set(band_ids)) != len(band_ids):
            raise CandidateError("Search Region band ids must be unique")
        stop = self.stop_after_band_id or band_ids[-1]
        if stop not in band_ids:
            raise CandidateError("stop_after_band_id must name an explicit Search Region band")
        object.__setattr__(self, "stop_after_band_id", stop)

    @property
    def allowed_band_ids(self) -> tuple[str, ...]:
        stop_index = self.band_index(self.stop_after_band_id or "")
        return tuple(band.band_id for band in self.bands[: stop_index + 1])

    def band_index(self, band_id: str) -> int:
        for index, band in enumerate(self.bands):
            if band.band_id == band_id:
                return index
        raise CandidateError(f"unknown Search Region band: {band_id}")


@dataclass(frozen=True)
class InitialAcquisition:
    candidates: tuple[CandidatePoolEntry, ...]
    active_band_id: str
    identity_issues: tuple[str, ...]
    pool_available_through_band: int


@dataclass(frozen=True)
class ReplacementDecision:
    status: ReplacementStatus
    rejected_candidate_id: str
    candidate: CandidatePoolEntry | None
    from_band_id: str
    active_band_id: str
    traversed_bands: tuple[str, ...]
    identity_issues: tuple[str, ...]
    reason: str

    @property
    def exhausted(self) -> bool:
        return self.status is ReplacementStatus.EXHAUSTED

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "rejected_candidate_id": self.rejected_candidate_id,
            "candidate": self.candidate.to_candidate_dict() if self.candidate else None,
            "from_band_id": self.from_band_id,
            "active_band_id": self.active_band_id,
            "traversed_bands": list(self.traversed_bands),
            "identity_issues": list(self.identity_issues),
            "reason": self.reason,
        }


@dataclass
class CandidatePool:
    """Stateful selection over a finite, lawful, reviewed candidate pool."""

    search_region: SearchRegion
    entries: Sequence[CandidatePoolEntry]
    listing_as_of: datetime | None = None
    listing_maximum_age: timedelta = timedelta(days=30)
    _canonical_entries: tuple[CandidatePoolEntry, ...] = field(init=False, repr=False)
    _duplicate_groups: dict[str, tuple[CandidatePoolEntry, ...]] = field(
        init=False, repr=False
    )
    _selected: set[str] = field(default_factory=set, init=False, repr=False)
    _rejected: set[str] = field(default_factory=set, init=False, repr=False)
    _active_band_index: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.listing_maximum_age < timedelta(0):
            raise CandidateError("listing_maximum_age cannot be negative")
        allowed_bands = set(self.search_region.allowed_band_ids)
        as_of = self.listing_as_of or datetime.now(timezone.utc)
        source_entries = [
            entry.apply_listing_freshness(
                as_of=as_of, maximum_age=self.listing_maximum_age
            )
            for entry in self.entries
        ]
        for entry in source_entries:
            if entry.band_id not in allowed_bands:
                raise CandidateError(
                    f"candidate {entry.candidate_id} is outside the allowed Search Region bands"
                )

        by_candidate_id: dict[str, CandidatePoolEntry] = {}
        listing_sites: dict[str, frozenset[tuple[str, object]]] = {}
        canonical: list[CandidatePoolEntry] = []
        groups: dict[str, list[CandidatePoolEntry]] = {}
        key_owner: dict[tuple[str, object], str] = {}

        for entry in source_entries:
            if entry.candidate_id in by_candidate_id:
                raise IdentityConflict(f"duplicate candidate_id: {entry.candidate_id}")
            by_candidate_id[entry.candidate_id] = entry
            site_keys = frozenset(entry.identity.site_keys)
            listing_id = entry.provenance.listing_id
            if listing_id:
                previous = listing_sites.get(listing_id)
                if previous is not None and previous.isdisjoint(site_keys):
                    raise IdentityConflict(
                        f"listing {listing_id} points at incompatible Candidate Sites"
                    )
                listing_sites[listing_id] = (previous or frozenset()) | site_keys

            owners = {key_owner[key] for key in site_keys if key in key_owner}
            if len(owners) > 1:
                raise IdentityConflict(
                    f"candidate {entry.candidate_id} bridges incompatible site identities"
                )
            if owners:
                owner = owners.pop()
                groups[owner].append(entry)
                for key in site_keys:
                    key_owner[key] = owner
                continue
            canonical.append(entry)
            groups[entry.candidate_id] = [entry]
            for key in site_keys:
                key_owner[key] = entry.candidate_id

        self._duplicate_groups = {
            owner: tuple(group) for owner, group in groups.items()
        }
        # An unresolved occurrence must never disappear merely because another
        # assertion for the same site happened to be ordered first.
        safe_canonical = []
        for entry in canonical:
            unresolved = [
                occurrence
                for occurrence in self._duplicate_groups[entry.candidate_id]
                if not occurrence.selectable
            ]
            if unresolved and entry.selectable:
                explanations = "; ".join(
                    occurrence.identity.ambiguity or "identity unresolved"
                    for occurrence in unresolved
                )
                entry = replace(
                    entry,
                    identity=replace(
                        entry.identity,
                        resolution=IdentityResolution.AMBIGUOUS,
                        ambiguity=explanations,
                    ),
                )
            safe_canonical.append(entry)
        self._canonical_entries = tuple(safe_canonical)

    @classmethod
    def from_records(
        cls,
        *,
        search_region: SearchRegion,
        records: Iterable[Mapping[str, object]],
        band_by_candidate_id: Mapping[str, str],
        listing_as_of: datetime | None = None,
        listing_maximum_age: timedelta = timedelta(days=30),
    ) -> CandidatePool:
        entries = []
        for record in records:
            candidate_id = str(record.get("id", ""))
            if candidate_id not in band_by_candidate_id:
                raise CandidateError(
                    f"candidate {candidate_id or '<missing id>'} has no explicit geography band"
                )
            entries.append(
                CandidatePoolEntry.from_record(
                    record, band_id=band_by_candidate_id[candidate_id]
                )
            )
        return cls(
            search_region=search_region,
            entries=entries,
            listing_as_of=listing_as_of,
            listing_maximum_age=listing_maximum_age,
        )

    @property
    def active_band_id(self) -> str:
        return self.search_region.bands[self._active_band_index].band_id

    @property
    def canonical_entries(self) -> tuple[CandidatePoolEntry, ...]:
        return self._canonical_entries

    @property
    def duplicate_groups(self) -> Mapping[str, tuple[CandidatePoolEntry, ...]]:
        """All source assertions, grouped under the selected site identity."""

        return dict(self._duplicate_groups)

    @property
    def selected_ids(self) -> frozenset[str]:
        return frozenset(self._selected)

    @property
    def rejected_ids(self) -> frozenset[str]:
        return frozenset(self._rejected)

    def acquire_initial(self, limit: int) -> InitialAcquisition:
        if limit < 1:
            raise CandidateError("initial acquisition limit must be positive")
        candidates, issues = self._available_through(self._active_band_index)
        chosen = tuple(candidates[:limit])
        self._selected.update(entry.candidate_id for entry in chosen)
        return InitialAcquisition(
            candidates=chosen,
            active_band_id=self.active_band_id,
            identity_issues=tuple(issues),
            pool_available_through_band=len(candidates),
        )

    def reject_and_replace(
        self, rejected_candidate_id: str, *, allow_widening: bool = True
    ) -> ReplacementDecision:
        if rejected_candidate_id not in self._selected:
            raise CandidateError(
                f"cannot reject unselected candidate: {rejected_candidate_id}"
            )
        self._rejected.add(rejected_candidate_id)
        starting_band_id = self.active_band_id
        candidates, issues = self._available_through(self._active_band_index)
        if candidates:
            candidate = candidates[0]
            self._selected.add(candidate.candidate_id)
            return ReplacementDecision(
                status=ReplacementStatus.REPLACED,
                rejected_candidate_id=rejected_candidate_id,
                candidate=candidate,
                from_band_id=starting_band_id,
                active_band_id=self.active_band_id,
                traversed_bands=(),
                identity_issues=tuple(issues),
                reason="replacement selected from the approved active geography",
            )

        traversed: list[str] = []
        all_issues = list(issues)
        stop_index = len(self.search_region.allowed_band_ids) - 1
        can_widen = allow_widening and self.search_region.widening_allowed
        while can_widen and self._active_band_index < stop_index:
            self._active_band_index += 1
            traversed.append(self.active_band_id)
            candidates, issues = self._available_through(self._active_band_index)
            all_issues.extend(issue for issue in issues if issue not in all_issues)
            if candidates:
                candidate = candidates[0]
                self._selected.add(candidate.candidate_id)
                return ReplacementDecision(
                    status=ReplacementStatus.WIDENED,
                    rejected_candidate_id=rejected_candidate_id,
                    candidate=candidate,
                    from_band_id=starting_band_id,
                    active_band_id=self.active_band_id,
                    traversed_bands=tuple(traversed),
                    identity_issues=tuple(all_issues),
                    reason="replacement required an explicitly permitted geography widening",
                )

        if not self.search_region.widening_allowed:
            reason = "lawful pool exhausted; Search Region widening was not permitted"
        elif not allow_widening:
            reason = "lawful pool exhausted; this replacement did not authorize widening"
        else:
            reason = (
                "lawful pool exhausted at the explicit Search Region stop "
                f"{self.search_region.stop_after_band_id}"
            )
        return ReplacementDecision(
            status=ReplacementStatus.EXHAUSTED,
            rejected_candidate_id=rejected_candidate_id,
            candidate=None,
            from_band_id=starting_band_id,
            active_band_id=self.active_band_id,
            traversed_bands=tuple(traversed),
            identity_issues=tuple(all_issues),
            reason=reason,
        )

    def _available_through(
        self, band_index: int
    ) -> tuple[list[CandidatePoolEntry], list[str]]:
        allowed_ids = {
            band.band_id for band in self.search_region.bands[: band_index + 1]
        }
        available: list[CandidatePoolEntry] = []
        issues: list[str] = []
        for entry in self._canonical_entries:
            if entry.band_id not in allowed_ids or entry.candidate_id in self._selected:
                continue
            if not entry.selectable:
                issues.append(
                    f"{entry.candidate_id}: {entry.identity.ambiguity or 'identity unresolved'}"
                )
                continue
            available.append(entry)
        return available, issues
