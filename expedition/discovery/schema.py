"""Discovery packet types. Labels stay honest: LISTED needs a licensed listing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


US_LAT = (18.0, 72.0)
US_LNG = (-180.0, -65.0)


def in_us(lat: float, lng: float) -> bool:
    return US_LAT[0] <= lat <= US_LAT[1] and US_LNG[0] <= lng <= US_LNG[1]


@dataclass(frozen=True)
class SourceSkip:
    source: str
    reason: str
    verdict: str  # BUILD_NOW | PARTNER | BLOCKED | NO_KEY | WITNESS_ONLY


@dataclass(frozen=True)
class SourcePlan:
    mission: str
    scan_budget: str
    seeds: tuple[str, ...]
    hops: tuple[str, ...]
    skipped: tuple[SourceSkip, ...]
    mireye_prefilter: bool
    why: str


@dataclass
class Seed:
    """One discovered pin. ``role=anchor`` is infrastructure, not a candidate site."""

    id: str
    name: str
    lat: float
    lng: float
    source: str
    source_url: str
    authorization: str
    family: str
    role: str = "candidate"
    label: str = "POTENTIAL"
    site_form: str = "either"
    address: str | None = None
    captured_at: str = ""
    extra: dict = field(default_factory=dict)

    def to_candidate(self) -> dict:
        row = {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "address": self.address,
            "label": self.label,
            "site_form": self.site_form,
            "source": self.source,
            "captured_at": self.captured_at,
            "source_url": self.source_url,
            "authorization": self.authorization,
            "family": self.family,
            "role": self.role,
        }
        if self.extra:
            row["extra"] = self.extra
        return row


def seed_dict(seed: Seed) -> dict:
    return asdict(seed)
