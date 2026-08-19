import unittest
from unittest.mock import patch

from expedition.adapters import mireye
from expedition.engine import run_mission, run_site
from expedition.plan import compile_plan


class ExtendedIntegrationTests(unittest.TestCase):
    def test_farm_and_data_center_execute_temporal_witnesses(self):
        farm = run_site("farm", "iowa_corn", controls={"scan_budget": "standard"})
        self.assertTrue(any(row["id"] == "farm-history" and row["status"] == "done" for row in farm["workstreams"]))
        self.assertEqual(
            {atom["field_id"] for atom in farm["atoms"]} & {"annual_cdl_rotation", "chirps_rainfall_history"},
            {"annual_cdl_rotation", "chirps_rainfall_history"},
        )

        dc = run_site("data_center", "ashburn_va", controls={"scan_budget": "standard"})
        self.assertTrue(any(row["id"] == "observed-heat" and row["status"] == "done" for row in dc["workstreams"]))
        self.assertTrue(any(atom["field_id"] == "modis_daytime_land_surface_temperature" for atom in dc["atoms"]))
        self.assertIn("electrical_capacity", {gap["question_id"] for gap in dc["verdict"]["gaps"]})

    def test_display_mission_names_still_execute_temporal_witnesses(self):
        farm = run_site("Farm", "iowa_corn", controls={"scan_budget": "standard"})
        data_center = run_site(
            "Data Center", "ashburn_va", controls={"scan_budget": "standard"}
        )
        self.assertIn("farm-history", {row["id"] for row in farm["workstreams"]})
        self.assertIn("observed-heat", {row["id"] for row in data_center["workstreams"]})

    def test_mission_filters_explicitly_incompatible_site_forms(self):
        result = run_mission(
            "farm",
            ["manhattan_midtown", "elba_ny", "iowa_corn"],
            controls={"site_form": "existing_asset", "scan_budget": "quick"},
        )
        self.assertEqual(
            ["manhattan_midtown"],
            [packet["candidate"]["id"] for packet in result["results"]],
        )
        excluded = [
            row["candidate_id"]
            for row in result["candidate_changes"]
            if row["status"] == "excluded"
        ]
        self.assertEqual(["elba_ny", "iowa_corn"], excluded)

    def test_expanded_find_flow_replaces_a_rejected_candidate(self):
        ids = ["san_leon", "san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"]
        out = run_mission(
            "warehouse",
            ids,
            controls={
                "search_region": "texas_triangle",
                "geography_band": "selected_region",
                "scan_budget": "standard",
            },
        )
        replacements = [row for row in out["candidate_changes"] if row["status"] == "replaced"]
        self.assertEqual(replacements[0]["rejected_candidate_id"], "san_leon")
        self.assertEqual(replacements[0]["candidate"]["id"], "port_houston")
        questions = {
            row["id"]: row.get("question")
            for packet in out["results"]
            for row in packet["workstreams"]
        }
        self.assertIn("veto this site", (questions.get("screen-site-core") or "").lower())
        san_leon = next(packet for packet in out["results"] if packet["candidate"]["id"] == "san_leon")
        rewind = next(row for row in san_leon["workstreams"] if row["id"] == "flood-rewind")
        self.assertIn("NASADEM", rewind.get("note") or "")
        self.assertIn("concept_fit", {gap["question_id"] for gap in san_leon["verdict"]["gaps"]})
        self.assertEqual(
            {"san_leon", "san_marcos_tx", "alliance_tx", "port_houston"},
            {row["candidate"]["id"] for row in out["results"]},
        )

    def test_geography_permission_can_widen_after_reject(self):
        out = run_mission(
            "warehouse",
            ["san_leon", "san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"],
            controls={
                "search_region": "houston_metro",
                "geography_band": "adjacent_regions",
                "scan_budget": "quick",
            },
        )
        widened = [row for row in out["candidate_changes"] if row["status"] == "widened"]
        self.assertEqual(widened[0]["rejected_candidate_id"], "san_leon")
        self.assertEqual(widened[0]["candidate"]["id"], "san_marcos_tx")

    def test_custom_manifest_and_structured_controls_are_compiled(self):
        plan = compile_plan(
            "custom",
            manifest_id="logistics-resilience",
            search_region="texas_triangle",
            geography_band="adjacent_regions",
            size_band="flexible",
            budget_band="10m_25m",
            preferences=[{"id": "major_road_access", "weight": "priority"}],
            optional_investigations=["route_reality", "scene_context"],
        )
        self.assertEqual(plan.manifest_id, "logistics-resilience")
        self.assertEqual(plan.preference_weights["major_road_access"], "priority")
        self.assertEqual(plan.geography_band, "adjacent_regions")
        self.assertIn("route-reality", plan.skills)

    def test_scheduler_trace_is_attached_and_veto_cancels_routes(self):
        packet = run_site("warehouse", "san_leon", controls={"scan_budget": "standard"})
        self.assertEqual(packet["orchestration"]["reliable_vetoes"], ["core-gate"])
        route = next(row for row in packet["workstreams"] if row["id"] == "route-reality")
        self.assertEqual(route["status"], "cancelled")

    def test_core_provider_failure_becomes_typed_candidate_result(self):
        with patch(
            "expedition.engine.mireye.fetch_fields",
            side_effect=TimeoutError("provider timed out"),
        ):
            packet = run_site("warehouse", "san_marcos_tx")
        core = next(row for row in packet["workstreams"] if row["id"] == "screen-site-core")
        self.assertEqual("failed", core["status"])
        self.assertEqual("conditional", packet["verdict"]["verdict"])
        self.assertTrue(
            any(atom["kind"] == "FAILED" for atom in packet["atoms"])
        )

    def test_one_core_failure_does_not_discard_completed_candidates(self):
        original = mireye.fetch_fields

        def flaky(**kwargs):
            if kwargs["candidate_id"] == "san_marcos_tx":
                raise PermissionError("provider denied request")
            return original(**kwargs)

        with patch("expedition.engine.mireye.fetch_fields", side_effect=flaky):
            result = run_mission(
                "warehouse",
                ["san_marcos_tx", "alliance_tx"],
                controls={"scan_budget": "quick"},
            )
        self.assertEqual(2, len(result["results"]))
        by_id = {packet["candidate"]["id"]: packet for packet in result["results"]}
        self.assertEqual(
            "failed",
            next(
                row
                for row in by_id["san_marcos_tx"]["workstreams"]
                if row["id"] == "screen-site-core"
            )["status"],
        )
        self.assertNotEqual(
            "failed",
            next(
                row
                for row in by_id["alliance_tx"]["workstreams"]
                if row["id"] == "screen-site-core"
            )["status"],
        )


if __name__ == "__main__":
    unittest.main()
