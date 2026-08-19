import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from expedition.adapters.temporal import farm_history, observed_heat


class TemporalWitnessTests(unittest.TestCase):
    def test_farm_replay_emits_cdl_and_chirps_atoms(self):
        atoms, payload = farm_history(
            candidate_id="iowa_corn", lat=42.032, lng=-93.52, live=False
        )
        self.assertEqual([atom.field_id for atom in atoms], [
            "annual_cdl_rotation",
            "chirps_rainfall_history",
        ])
        self.assertTrue(all(atom.status == "replay" for atom in atoms))
        self.assertEqual(atoms[0].independence_group, "USDA_CDL")
        self.assertEqual(atoms[1].independence_group, "CHIRPS")
        self.assertEqual(payload["farm_history"]["chirps"]["annual_mean_mm"], 894.5)
        self.assertIn("not yield", atoms[0].notes.lower())
        self.assertIn("water right", atoms[1].notes.lower())
        self.assertFalse(atoms[1].support["parcel_grade"])

    def test_observed_heat_is_context_not_capacity_or_air_temperature(self):
        atoms, payload = observed_heat(
            candidate_id="ashburn_va", lat=39.0438, lng=-77.4874, live=False
        )
        self.assertEqual(len(atoms), 1)
        atom = atoms[0]
        self.assertEqual(atom.kind, "FACT")
        self.assertEqual(atom.decision_effect, "INFORM")
        self.assertEqual(atom.source_family, "MODIS_LST")
        self.assertEqual(payload["observed_heat"]["daytime_mean_c"], 33.6)
        self.assertIn("not ambient air temperature", atom.notes.lower())
        self.assertIn("deliverable mw", atom.notes.lower())
        self.assertEqual(atom.transform_version, "modis-summer-lst-legacy-v0")
        self.assertIn("predates qc_day masking", atom.notes.lower())

    def test_missing_fixture_returns_explicit_unknowns(self):
        with tempfile.TemporaryDirectory() as cache, tempfile.TemporaryDirectory() as fixtures:
            atoms, payload = farm_history(
                candidate_id="unproven",
                lat=40.0,
                lng=-100.0,
                live=False,
                cache_dir=Path(cache),
                fixture_dir=Path(fixtures),
            )
        self.assertEqual(payload, {})
        self.assertEqual(len(atoms), 2)
        self.assertTrue(all(atom.kind == "UNKNOWN" for atom in atoms))
        self.assertTrue(all(atom.decision_effect == "UNKNOWN" for atom in atoms))

    def test_fixture_is_not_reused_for_different_geometry(self):
        atoms, payload = farm_history(
            candidate_id="iowa_corn", lat=42.033, lng=-93.52, live=False
        )
        self.assertEqual(payload, {})
        self.assertTrue(all(atom.kind == "UNKNOWN" for atom in atoms))

    def test_live_result_is_cached_then_replayed(self):
        live_payload = {
            "farm_history": {
                "window": "2016-01-01/2024-12-31",
                "cdl": {"annual_series": [{"year": 2024, "code": 1, "label": "Corn"}]},
                "chirps": {"annual_mean_mm": 800.0},
            }
        }
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as fixtures:
            cache = Path(tmp)
            with patch("expedition.adapters.temporal._live_farm", return_value=live_payload):
                live_atoms, _ = farm_history(
                    candidate_id="site",
                    lat=42.0,
                    lng=-93.0,
                    live=True,
                    cache_dir=cache,
                    fixture_dir=Path(fixtures),
                )
            replay_atoms, _ = farm_history(
                candidate_id="site",
                lat=42.0,
                lng=-93.0,
                live=False,
                cache_dir=cache,
                fixture_dir=Path(fixtures),
            )
        self.assertTrue(all(atom.status == "live" for atom in live_atoms))
        self.assertTrue(all(atom.status == "replay" for atom in replay_atoms))
        self.assertEqual(replay_atoms[1].value["annual_mean_mm"], 800.0)


if __name__ == "__main__":
    unittest.main()
