import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from expedition.adapters import mireye
from expedition.evidence import (
    Contradiction,
    EvidenceAtom,
    atom_from_mireye_field,
    detect_contradictions,
    geometry_hash,
)


NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def make_atom(
    atom_id: str,
    value,
    *,
    candidate_id: str = "site-1",
    question_id: str = "hazards.flood",
    field_id: str = "fema_flood_zone",
    independence_group: str = "FEMA_NFHL",
    observed_at: str | None = "2026-08-01",
    support: dict | None = None,
) -> EvidenceAtom:
    fetched_at = "2026-08-15T10:00:00Z"
    return EvidenceAtom(
        atom_id=atom_id,
        candidate_id=candidate_id,
        question_id=question_id,
        field_id=field_id,
        kind="FACT",
        status="replay",
        decision_effect="GATE",
        value=value,
        unit=None,
        source="test",
        source_url=None,
        source_family=independence_group,
        independence_group=independence_group,
        authority="authoritative",
        support=support
        or {
            "kind": "point",
            "crs": "EPSG:4326",
            "lat": 30.0,
            "lng": -97.0,
            "geometry_hash": geometry_hash(30.0, -97.0),
        },
        observed_at=observed_at,
        fetched_at=fetched_at,
        dataset_vintage="2026-08",
        ttl="P30D",
        confidence="high",
        notes=None,
        failure=None,
        cost={"credits": 0, "tokens": 0, "unit": "test"},
        citation={
            "source": "test",
            "source_url": None,
            "fetched_at": fetched_at,
            "dataset_vintage": "2026-08",
        },
        transform_version="test-v1",
        cache_identity=f"cache:{atom_id}",
        live_label="replay",
    )


class CacheFreshnessTests(unittest.TestCase):
    def test_expired_cached_field_is_stale_and_not_usable_as_pass(self):
        atom = atom_from_mireye_field(
            candidate_id="site-1",
            question_id="hazards.flood",
            field_id="fema_flood_zone",
            raw={
                "value": "X",
                "status": "ok",
                "source": "FEMA_NFHL",
                "fetched_at": "2026-08-15T10:00:00Z",
                "ttl_seconds": 3600,
            },
            lat=30.0,
            lng=-97.0,
            live=False,
            effect="GATE",
            kind="FACT",
            authority="authoritative",
            credits=0,
            now=NOW,
        )

        self.assertEqual(atom.status, "stale")
        self.assertEqual(atom.live_label, "replay")
        self.assertEqual(atom.ttl, "3600")
        self.assertFalse(atom.usable_as_pass)

    def test_unexpired_cached_field_remains_replay(self):
        atom = atom_from_mireye_field(
            candidate_id="site-1",
            question_id="hazards.flood",
            field_id="fema_flood_zone",
            raw={
                "value": "X",
                "status": "ok",
                "source": "FEMA_NFHL",
                "fetched_at": "2026-08-15T11:30:00Z",
                "ttl": "PT1H",
            },
            lat=30.0,
            lng=-97.0,
            live=False,
            effect="GATE",
            kind="FACT",
            authority="authoritative",
            credits=0,
            now=NOW,
        )

        self.assertEqual(atom.status, "replay")
        self.assertTrue(atom.usable_as_pass)

    def test_unparseable_ttl_fails_closed_as_stale(self):
        atom = atom_from_mireye_field(
            candidate_id="site-1",
            question_id="hazards.flood",
            field_id="fema_flood_zone",
            raw={
                "value": "X",
                "status": "ok",
                "source": "FEMA_NFHL",
                "fetched_at": "2026-08-15T11:30:00Z",
                "ttl": "whenever",
            },
            lat=30.0,
            lng=-97.0,
            live=False,
            effect="GATE",
            kind="FACT",
            authority="authoritative",
            credits=0,
            now=NOW,
        )

        self.assertEqual(atom.status, "stale")
        self.assertFalse(atom.usable_as_pass)


class MireyePartialResponseTests(unittest.TestCase):
    def test_successful_partial_atom_and_failure_details_are_preserved(self):
        payload = {
            "fetched_at": "2026-08-15T11:30:00Z",
            "partial_failures": [
                {
                    "field": "broken_field",
                    "source": "BROKEN_SOURCE",
                    "error": "source returned null",
                    "retryable": False,
                }
            ],
            "fields": {
                "good_field": {
                    "value": 42,
                    "status": "partial",
                    "source": "GOOD_SOURCE",
                    "ttl_seconds": 3600,
                    "notes": "usable component retained",
                    "partial_failures": [
                        {
                            "field": "good_field.detail",
                            "source": "DETAIL_SOURCE",
                            "error": "detail unavailable",
                            "retryable": True,
                        }
                    ],
                },
                "clean_field": {
                    "value": "X",
                    "status": "ok",
                    "source": "CLEAN_SOURCE",
                    "ttl_seconds": 3600,
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            cache = Path(tmp) / "cache"
            fixtures.mkdir()
            (fixtures / "site-1.json").write_text(json.dumps(payload))
            with patch.object(mireye, "FIXTURES", fixtures), patch.object(
                mireye, "CACHE", cache
            ):
                atoms, spent, raw = mireye.fetch_fields(
                    candidate_id="site-1",
                    lat=30.0,
                    lng=-97.0,
                    fields=["good_field", "clean_field", "broken_field"],
                    live=False,
                    question_id="screen.core",
                    effects={
                        "good_field": ("FACT", "GATE", "authoritative"),
                        "clean_field": ("FACT", "GATE", "authoritative"),
                        "broken_field": ("FACT", "GATE", "authoritative"),
                    },
                    expedition_spent=0,
                    now=NOW,
                )

        good, clean, broken = atoms
        self.assertEqual(spent, 0)
        self.assertEqual(raw, payload)
        self.assertEqual(good.value, 42)
        self.assertEqual(good.kind, "FACT")
        self.assertEqual(good.status, "partial")
        self.assertEqual(good.notes, "usable component retained")
        self.assertEqual(good.fetched_at, payload["fetched_at"])
        self.assertEqual(
            good.partial_failures,
            payload["partial_failures"]
            + payload["fields"]["good_field"]["partial_failures"],
        )
        self.assertEqual(clean.status, "replay")
        self.assertTrue(clean.usable_as_pass)
        self.assertEqual(clean.partial_failures, payload["partial_failures"])
        self.assertEqual(broken.kind, "FAILED")
        self.assertEqual(broken.status, "failed")
        self.assertEqual(broken.partial_failures, payload["partial_failures"])
        self.assertIn("source returned null", broken.failure["message_public"])


class ContradictionTests(unittest.TestCase):
    def test_detector_keeps_disagreeing_atoms_in_a_verification_gap(self):
        first = make_atom("a-1", "X", independence_group="FEMA_NFHL")
        second = make_atom("a-2", "AE", independence_group="LOCAL_FLOOD_MAP")

        contradictions = detect_contradictions([second, first])

        self.assertEqual(len(contradictions), 1)
        contradiction = contradictions[0]
        self.assertIsInstance(contradiction, Contradiction)
        self.assertEqual(contradiction.atom_ids, ["a-1", "a-2"])
        self.assertFalse(contradiction.same_independence_group)
        self.assertTrue(contradiction.geometry_aligned)
        self.assertTrue(contradiction.time_aligned)
        self.assertEqual(contradiction.resolution, "verification_gap")

    def test_detector_marks_same_family_as_non_corroborating(self):
        first = make_atom("a-1", 10, independence_group="JRC_GSW")
        second = make_atom("a-2", 20, independence_group="JRC_GSW")

        contradiction = detect_contradictions([first, second])[0]

        self.assertTrue(contradiction.same_independence_group)
        self.assertIn("cannot corroborate", contradiction.notes)

    def test_support_mismatch_is_kept_but_not_called_site_level(self):
        point = make_atom("a-1", 10)
        buffer_atom = make_atom(
            "a-2",
            20,
            support={
                "kind": "buffer",
                "crs": "EPSG:4326",
                "lat": 30.0,
                "lng": -97.0,
                "radius_m": 60,
                "radius_purpose": "test",
                "geometry_hash": geometry_hash(30.0, -97.0, "buffer:60"),
            },
        )

        contradiction = detect_contradictions([point, buffer_atom])[0]

        self.assertFalse(contradiction.geometry_aligned)
        self.assertEqual(contradiction.resolution, "keep_both")
        self.assertIn("support mismatch", contradiction.notes.lower())

    def test_different_fields_are_not_compared_as_literal_values(self):
        zone = make_atom("a-1", "AE", field_id="fema_flood_zone")
        polygon = make_atom(
            "a-2", True, field_id="within_floodplain_polygon"
        )

        self.assertEqual(detect_contradictions([zone, polygon]), [])


if __name__ == "__main__":
    unittest.main()
