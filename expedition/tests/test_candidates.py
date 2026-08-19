import unittest
from datetime import datetime, timedelta, timezone

from expedition.candidates import (
    CandidateError,
    CandidateIdentity,
    CandidateLabel,
    CandidatePool,
    CandidatePoolEntry,
    CandidateProvenance,
    IdentityConflict,
    IdentityResolution,
    ProvenanceError,
    ReplacementStatus,
    SearchBand,
    SearchRegion,
    SourceKind,
)


NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)


def region(*, widen=True, stop="state"):
    return SearchRegion(
        region_id="texas-triangle",
        label="Texas Triangle",
        bands=(
            SearchBand("metro", "Selected metros"),
            SearchBand("corridor", "Texas Triangle corridors"),
            SearchBand("state", "Texas statewide"),
        ),
        widening_allowed=widen,
        stop_after_band_id=stop,
    )


def entry(
    candidate_id,
    *,
    band="metro",
    lat=30.0,
    lng=-97.0,
    location_id=None,
    parcel_id=None,
    listing_id=None,
    label=CandidateLabel.POTENTIAL,
    source_kind=SourceKind.CURATED,
    last_seen_at=None,
    resolution=IdentityResolution.RESOLVED,
    ambiguity=None,
):
    return CandidatePoolEntry(
        candidate_id=candidate_id,
        name=candidate_id.replace("_", " ").title(),
        identity=CandidateIdentity(
            location_id=location_id or candidate_id,
            lat=lat,
            lng=lng,
            parcel_id=parcel_id,
            resolution=resolution,
            ambiguity=ambiguity,
        ),
        label=label,
        site_form="either",
        provenance=CandidateProvenance(
            source="test reviewed pool",
            source_kind=source_kind,
            captured_at=NOW,
            authorization="test fixture",
            listing_id=listing_id,
            last_seen_at=last_seen_at,
        ),
        band_id=band,
    )


class CandidateProvenanceTests(unittest.TestCase):
    def test_listed_requires_an_authorized_timestamped_listing_source(self):
        with self.assertRaises(ProvenanceError):
            entry("fake_listing", label=CandidateLabel.LISTED)

        listed = entry(
            "real_listing",
            label=CandidateLabel.LISTED,
            source_kind=SourceKind.LICENSED,
            listing_id="listing-17",
            last_seen_at=NOW,
        )
        self.assertEqual(listed.label, CandidateLabel.LISTED)

    def test_user_site_requires_user_provenance(self):
        with self.assertRaises(ProvenanceError):
            entry("not_user", label=CandidateLabel.USER_SITE)
        user = entry(
            "user_pin",
            label=CandidateLabel.USER_SITE,
            source_kind=SourceKind.USER,
        )
        self.assertEqual(user.label, CandidateLabel.USER_SITE)

    def test_stale_listing_becomes_potential_with_confirmation_action(self):
        listed = entry(
            "old_listing",
            label=CandidateLabel.LISTED,
            source_kind=SourceKind.LICENSED,
            listing_id="listing-old",
            last_seen_at=NOW - timedelta(days=31),
        )
        pool = CandidatePool(
            region(widen=False),
            [listed],
            listing_as_of=NOW,
            listing_maximum_age=timedelta(days=30),
        )
        selected = pool.acquire_initial(1).candidates[0]
        self.assertEqual(selected.label, CandidateLabel.POTENTIAL)
        self.assertIn("broker or owner", selected.confirmation_actions[0])


class CandidateIdentityTests(unittest.TestCase):
    def test_same_site_is_deduplicated_but_source_assertions_are_preserved(self):
        first = entry(
            "site_a_source_1",
            lat=30.1,
            parcel_id="parcel-a",
            listing_id="listing-1",
            source_kind=SourceKind.LICENSED,
        )
        second = entry(
            "site_a_source_2",
            lat=30.2,
            location_id="another-location-id",
            parcel_id="parcel-a",
            listing_id="listing-2",
            source_kind=SourceKind.LICENSED,
        )
        pool = CandidatePool(region(), [first, second], listing_as_of=NOW)
        self.assertEqual([row.candidate_id for row in pool.canonical_entries], ["site_a_source_1"])
        self.assertEqual(len(pool.duplicate_groups["site_a_source_1"]), 2)

    def test_listing_identity_cannot_point_to_incompatible_sites(self):
        with self.assertRaises(IdentityConflict):
            CandidatePool(
                region(),
                [
                    entry(
                        "a",
                        lat=30.0,
                        listing_id="same-listing",
                        source_kind=SourceKind.LICENSED,
                    ),
                    entry(
                        "b",
                        lat=31.0,
                        listing_id="same-listing",
                        source_kind=SourceKind.LICENSED,
                    ),
                ],
                listing_as_of=NOW,
            )

    def test_ambiguous_identity_is_not_silently_selected(self):
        pool = CandidatePool(
            region(widen=False),
            [
                entry(
                    "ambiguous",
                    resolution=IdentityResolution.AMBIGUOUS,
                    ambiguity="two equally plausible geocodes",
                ),
                entry("resolved", lat=30.2),
            ],
            listing_as_of=NOW,
        )
        acquired = pool.acquire_initial(2)
        self.assertEqual([row.candidate_id for row in acquired.candidates], ["resolved"])
        self.assertEqual(
            acquired.identity_issues,
            ("ambiguous: two equally plausible geocodes",),
        )

    def test_ambiguous_duplicate_blocks_the_canonical_site(self):
        pool = CandidatePool(
            region(widen=False),
            [
                entry("resolved", lat=30.2, location_id="same-site"),
                entry(
                    "ambiguous",
                    lat=30.2,
                    location_id="same-site",
                    resolution=IdentityResolution.AMBIGUOUS,
                    ambiguity="parcel match is unresolved",
                ),
            ],
            listing_as_of=NOW,
        )
        acquired = pool.acquire_initial(1)
        self.assertEqual(acquired.candidates, ())
        self.assertEqual(
            acquired.identity_issues,
            ("resolved: parcel match is unresolved",),
        )


class CandidateReplacementTests(unittest.TestCase):
    def test_rejected_candidate_is_replaced_in_active_band_first(self):
        pool = CandidatePool(
            region(),
            [entry("a"), entry("b", lat=30.1), entry("c", band="corridor", lat=30.2)],
            listing_as_of=NOW,
        )
        initial = pool.acquire_initial(1)
        self.assertEqual(initial.candidates[0].candidate_id, "a")
        decision = pool.reject_and_replace("a")
        self.assertEqual(decision.status, ReplacementStatus.REPLACED)
        self.assertEqual(decision.candidate.candidate_id, "b")
        self.assertEqual(decision.active_band_id, "metro")

    def test_replacement_widens_only_to_an_explicit_band(self):
        pool = CandidatePool(
            region(),
            [entry("a"), entry("b", band="corridor", lat=30.1)],
            listing_as_of=NOW,
        )
        pool.acquire_initial(1)
        decision = pool.reject_and_replace("a")
        self.assertEqual(decision.status, ReplacementStatus.WIDENED)
        self.assertEqual(decision.candidate.candidate_id, "b")
        self.assertEqual(decision.traversed_bands, ("corridor",))

    def test_pool_exhaustion_stops_at_configured_band(self):
        pool = CandidatePool(
            region(stop="corridor"),
            [entry("a")],
            listing_as_of=NOW,
        )
        pool.acquire_initial(1)
        decision = pool.reject_and_replace("a")
        self.assertEqual(decision.status, ReplacementStatus.EXHAUSTED)
        self.assertIsNone(decision.candidate)
        self.assertEqual(decision.active_band_id, "corridor")
        self.assertIn("explicit Search Region stop corridor", decision.reason)

    def test_replacement_does_not_widen_without_permission(self):
        pool = CandidatePool(
            region(widen=False),
            [entry("a"), entry("b", band="corridor", lat=30.1)],
            listing_as_of=NOW,
        )
        pool.acquire_initial(1)
        decision = pool.reject_and_replace("a")
        self.assertEqual(decision.status, ReplacementStatus.EXHAUSTED)
        self.assertEqual(decision.active_band_id, "metro")
        self.assertIn("not permitted", decision.reason)

    def test_only_selected_candidates_can_be_rejected(self):
        pool = CandidatePool(region(), [entry("a")], listing_as_of=NOW)
        with self.assertRaises(CandidateError):
            pool.reject_and_replace("a")


class CandidateRecordAdapterTests(unittest.TestCase):
    def test_repository_record_shape_adapts_without_claiming_listed(self):
        pool = CandidatePool.from_records(
            search_region=region(widen=False),
            records=[
                {
                    "id": "san_marcos_tx",
                    "name": "San Marcos I-35 / rail pin",
                    "lat": 29.883,
                    "lng": -97.941,
                    "label": "POTENTIAL",
                    "site_form": "either",
                    "source": "curated_locator_lock_2026-08-15",
                    "captured_at": "2026-08-15T02:10:00Z",
                }
            ],
            band_by_candidate_id={"san_marcos_tx": "metro"},
            listing_as_of=NOW,
        )
        selected = pool.acquire_initial(1).candidates[0]
        self.assertEqual(selected.label, CandidateLabel.POTENTIAL)
        self.assertEqual(selected.to_candidate_dict()["label"], "POTENTIAL")

    def test_every_record_requires_an_explicit_band(self):
        with self.assertRaises(CandidateError):
            CandidatePool.from_records(
                search_region=region(),
                records=[{"id": "orphan"}],
                band_by_candidate_id={},
            )


if __name__ == "__main__":
    unittest.main()
