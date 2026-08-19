import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from expedition.adapters.routes import route_atom
from expedition.engine import run_site
from expedition.plan import compile_plan


class RouteRealityTests(unittest.TestCase):
    def test_warehouse_plan_declares_default_anchors(self):
        plan = compile_plan("warehouse")
        self.assertEqual(
            [anchor["id"] for anchor in plan.route_anchors],
            ["port_houston", "san_antonio_customer"],
        )
        self.assertIn("route-reality", plan.skills)

    def test_live_result_is_cached_and_replayed_as_fact(self):
        origin = {"lat": 29.883, "lng": -97.941}
        destination = {
            "id": "port_houston",
            "name": "Port of Houston",
            "lat": 29.73,
            "lng": -95.12,
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            result = {"duration_s": 7200, "distance_m": 250000, "status": {}}
            with patch("expedition.adapters.routes.route_matrix", return_value=result):
                live_atom = route_atom(
                    "san_marcos_tx", origin, destination, True, cache_dir=cache_dir
                )
            replay_atom = route_atom(
                "san_marcos_tx", origin, destination, False, cache_dir=cache_dir
            )
        self.assertEqual(live_atom.kind, "FACT")
        self.assertEqual(replay_atom.kind, "FACT")
        self.assertEqual(replay_atom.value, 7200)
        self.assertEqual(replay_atom.status, "replay")

    def test_missing_replay_is_explicit_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            atom = route_atom(
                "x",
                {"lat": 30.0, "lng": -97.0},
                {"id": "anchor", "lat": 31.0, "lng": -96.0},
                False,
                cache_dir=Path(tmp),
            )
        self.assertEqual(atom.kind, "UNKNOWN")
        self.assertEqual(atom.decision_effect, "UNKNOWN")

    def test_survivor_runs_routes_and_reject_cancels(self):
        survivor = run_site("warehouse", "san_marcos_tx", live=False)
        route_stream = next(
            stream for stream in survivor["workstreams"] if stream["id"] == "route-reality"
        )
        route_atoms = [
            atom for atom in survivor["atoms"] if atom["field_id"] == "route_duration_s"
        ]
        self.assertIn(route_stream["status"], {"done", "partial"})
        self.assertEqual(len(route_atoms), 2)
        self.assertTrue(all(atom["kind"] in {"FACT", "UNKNOWN"} for atom in route_atoms))

        reject = run_site("warehouse", "san_leon", live=False)
        route_stream = next(
            stream for stream in reject["workstreams"] if stream["id"] == "route-reality"
        )
        self.assertEqual(route_stream["status"], "cancelled")
        self.assertFalse(
            any(atom["field_id"] == "route_duration_s" for atom in reject["atoms"])
        )

    def test_port_does_not_route_to_itself(self):
        packet = run_site("warehouse", "port_houston", live=False)
        route_atoms = [
            atom for atom in packet["atoms"] if atom["field_id"] == "route_duration_s"
        ]
        self.assertEqual(len(route_atoms), 1)
        self.assertEqual(
            route_atoms[0]["support"]["destination_id"], "san_antonio_customer"
        )


if __name__ == "__main__":
    unittest.main()
