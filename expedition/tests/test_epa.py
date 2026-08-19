import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from expedition.adapters import epa, mireye
from expedition.engine import run_site
from expedition.evidence import family_for


class EpaEchoAdapterTests(unittest.TestCase):
    def test_replay_attaches_named_rmp_record_without_claiming_independence(self):
        with patch.object(epa, "CACHE", Path("/definitely/missing/cache")):
            atoms, payload = epa.rmp_record(
                candidate_id="san_leon",
                lat=29.475732,
                lng=-94.966533,
                hit_distance_m=3342.405,
                live=False,
            )
        atom = atoms[0]
        facility = payload["facility"]
        self.assertEqual("FACT", atom.kind)
        self.assertEqual("replay", atom.status)
        self.assertEqual("EPA", atom.independence_group)
        self.assertEqual("110002345515", facility["registry_id"])
        self.assertEqual("P. H. ROBINSON ELECTRIC GENERATING STATION", facility["name"])
        self.assertIn("not a clean-site", atom.notes)
        self.assertEqual(
            family_for("nearest_hazardous_facility_distance_m"),
            family_for("epa_rmp_facility_record"),
        )

    def test_missing_replay_is_a_typed_failed_atom(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory)
            with patch.object(epa, "CACHE", missing), patch.object(epa, "FIXTURES", missing):
                atoms, payload = epa.rmp_record(
                    candidate_id="unknown",
                    lat=35.0,
                    lng=-97.0,
                    hit_distance_m=1000,
                    live=False,
                )
        self.assertEqual({}, payload)
        self.assertEqual("FAILED", atoms[0].kind)
        self.assertEqual("unsupported", atoms[0].failure["class"])


class EnvironmentalRecordIntegrationTests(unittest.TestCase):
    def test_mireye_hit_triggers_epa_record_and_phase_i_gap(self):
        original = mireye.fetch_fields

        def with_environmental_hit(**kwargs):
            atoms, spent, raw = original(**kwargs)
            hit = next(
                atom
                for atom in atoms
                if atom.field_id == "nearest_hazardous_facility_distance_m"
            )
            hit.kind = "PROXY"
            hit.status = "replay"
            hit.value = 3342.405
            hit.authority = "proxy"
            return atoms, spent, raw

        with patch("expedition.engine.mireye.fetch_fields", side_effect=with_environmental_hit):
            packet = run_site(
                "warehouse",
                "san_leon",
                controls={
                    "scan_budget": "standard",
                    "optional_investigations": ["environmental_record"],
                },
            )

        record = next(row for row in packet["workstreams"] if row["id"] == "environmental-record")
        self.assertEqual("done", record["status"])
        self.assertTrue(
            any(atom["field_id"] == "epa_rmp_facility_record" for atom in packet["atoms"])
        )
        self.assertIn(
            "environmental_phase_i",
            {gap["question_id"] for gap in packet["verdict"]["gaps"]},
        )
        self.assertEqual(
            "EPA ECHO / Facility Registry Service",
            packet["brief"]["citations"][0]["source"],
        )
        self.assertTrue(
            any(row["id"] == "environmental-record" for row in packet["scorecard"])
        )


if __name__ == "__main__":
    unittest.main()
