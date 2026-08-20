import unittest

from expedition.adapters import extended
from expedition.engine import run_site
from expedition.plan import compile_plan


class StretchSkillsTests(unittest.TestCase):
    def test_warehouse_land_change_is_inform_and_does_not_score(self):
        packet = run_site("warehouse", "alliance_tx", controls={"scan_budget": "standard"})
        self.assertEqual("conditional", packet["verdict"]["verdict"])
        land = next(row for row in packet["workstreams"] if row["id"] == "land-change")
        self.assertEqual("done", land["status"])
        atom = next(row for row in packet["atoms"] if row["field_id"] == "dw_built_fraction_change")
        self.assertEqual("INFORM", atom["decision_effect"])
        self.assertEqual("none", atom["authority"])
        self.assertIsInstance(atom["value"]["early_built_frac"], float)
        self.assertIsInstance(atom["value"]["late_built_frac"], float)
        self.assertFalse(atom["value"].get("score_used"))
        self.assertEqual("land_change", packet["scene"]["past"]["kind"])
        self.assertFalse(packet["scene"]["past"]["scores"])
        by_id = {row["id"]: row for row in packet["scorecard"]}
        self.assertEqual("inform", by_id["land-change"]["status"])

    def test_farm_climate_trajectory_is_labeled_model_not_parcel_prediction(self):
        packet = run_site("farm", "iowa_corn", controls={"scan_budget": "standard"})
        climate = next(row for row in packet["workstreams"] if row["id"] == "climate-trajectory")
        self.assertEqual("done", climate["status"])
        atom = next(row for row in packet["atoms"] if row["field_id"] == "climate_scenario_tasmax")
        self.assertEqual("MODEL", atom["kind"])
        self.assertEqual("INFORM", atom["decision_effect"])
        self.assertTrue(atom["value"].get("models") or atom["value"].get("model"))
        self.assertFalse(atom["value"].get("prediction") or atom["value"].get("parcel_prediction"))
        self.assertIsInstance(atom["value"]["delta_c"], (int, float))
        self.assertIn("climate_scenario_tasmax", packet["verdict"]["inform"])

    def test_labor_access_never_compiles_for_home(self):
        plan = compile_plan(
            "home",
            optional_investigations=["labor_access", "climate_trajectory", "source_scout"],
        )
        self.assertNotIn("labor-access", plan.skills)
        self.assertIn("climate-trajectory", plan.skills)
        self.assertIn("source-scout", plan.skills)
        packet = run_site("home", "manhattan_midtown", controls={"scan_budget": "standard"})
        self.assertFalse(any(row["id"] == "labor-access" for row in packet["workstreams"]))

    def test_warehouse_labor_is_proxy_not_hiring(self):
        packet = run_site("warehouse", "san_marcos_tx", controls={"scan_budget": "standard"})
        labor = next(row for row in packet["workstreams"] if row["id"] == "labor-access")
        self.assertEqual("done", labor["status"])
        atom = next(row for row in packet["atoms"] if row["field_id"] == "labor_shed_context")
        self.assertEqual("PROXY", atom["kind"])
        self.assertFalse(atom["value"]["availability_claim"])
        self.assertIsNone(atom["value"].get("workers_available"))
        self.assertIn("does not claim workers", (labor.get("note") or "").lower())
        by_id = {row["id"]: row for row in packet["scorecard"]}
        self.assertEqual("inform", by_id["labor-access"]["status"])
        self.assertIn("not a hiring claim", by_id["labor-access"]["value"])

    def test_source_scout_is_constrained_official_followup(self):
        packet = run_site("warehouse", "san_marcos_tx", controls={"scan_budget": "standard"})
        scout = next(row for row in packet["workstreams"] if row["id"] == "source-scout")
        self.assertEqual("done", scout["status"])
        atom = next(row for row in packet["atoms"] if row["field_id"] == "official_followup_sources")
        self.assertFalse(atom["value"]["discovery"])
        urls = {row["url"] for row in atom["value"]["followups"]}
        self.assertTrue(urls)
        self.assertTrue(all(url.startswith("https://") for url in urls))
        self.assertIn("not web discovery", (scout.get("note") or "").lower())

    def test_data_center_gets_climate_and_concept_preset(self):
        packet = run_site("data_center", "ashburn_va", controls={"scan_budget": "standard"})
        self.assertTrue(any(row["id"] == "climate-trajectory" and row["status"] == "done" for row in packet["workstreams"]))
        self.assertEqual("visual_concept", packet["scene"]["future"]["claim"])
        self.assertEqual("dc-hall", packet["scene"]["future"]["preset_id"])
        self.assertEqual("deferred", packet["scene"]["fit"]["claim"])
        self.assertIn("not a permit", packet["scene"]["future"]["note"].lower())

    def test_quick_scan_skips_stretch_skills(self):
        packet = run_site("warehouse", "san_marcos_tx", controls={"scan_budget": "quick"})
        by_id = {row["id"]: row for row in packet["workstreams"]}
        self.assertEqual("skipped", by_id["land-change"]["status"])
        self.assertEqual("skipped", by_id["labor-access"]["status"])
        self.assertEqual("skipped", by_id["source-scout"]["status"])
        self.assertEqual("skipped", by_id["climate-trajectory"]["status"])

    def test_adapter_unknown_without_fixture(self):
        atoms, payload = extended.land_change(
            candidate_id="austin_winfield",
            lat=30.2363775,
            lng=-97.7807633,
        )
        self.assertEqual([], list(payload))
        self.assertEqual("UNKNOWN", atoms[0].kind)
        self.assertEqual("UNKNOWN", atoms[0].decision_effect)


class LandChangeClassifyTests(unittest.TestCase):
    def test_classify_never_uses_a_mean_probability_score(self):
        from expedition.adapters.change import classify

        stable = classify({
            "dynamic_world": {"early_built_frac": 0.20, "late_built_frac": 0.22},
            "nlcd": {"early_developed_frac": 0.30, "late_developed_frac": 0.31},
        })
        self.assertEqual("stable", stable["change_type"])
        self.assertFalse(stable["score_used"])

        gain = classify({
            "dynamic_world": {"early_built_frac": 0.10, "late_built_frac": 0.40},
            "nlcd": {"early_developed_frac": 0.12, "late_developed_frac": 0.28},
        })
        self.assertEqual("built_gain", gain["change_type"])
        self.assertEqual("agree", gain["agreement"])

        disagree = classify({
            "dynamic_world": {"early_built_frac": 0.10, "late_built_frac": 0.40},
            "nlcd": {"early_developed_frac": 0.50, "late_developed_frac": 0.20},
        })
        self.assertEqual("disagreement", disagree["change_type"])
        self.assertEqual("disagree", disagree["agreement"])


class ClimateEnsembleTests(unittest.TestCase):
    def test_replay_is_a_range_not_a_single_prediction(self):
        from expedition.adapters import extended

        atoms, payload = extended.climate_trajectory(
            candidate_id="iowa_corn",
            lat=42.032,
            lng=-93.52,
        )
        climate = payload["climate_trajectory"]
        self.assertGreaterEqual(len(climate.get("models") or []), 2)
        self.assertFalse(climate.get("prediction"))
        self.assertIsInstance(climate["delta_c"], (int, float))
        self.assertEqual("MODEL", atoms[0].kind)


class ScoutConstraintTests(unittest.TestCase):
    def test_scout_catalog_is_official_followups_not_discovery(self):
        from expedition.adapters import extended

        atoms, payload = extended.source_scout(
            candidate_id="san_marcos_tx",
            lat=29.883,
            lng=-97.941,
            mission="warehouse",
            core_atoms=[],
        )
        self.assertFalse(payload["discovery"])
        self.assertEqual("constrained_official_followup", payload["mode"])
        self.assertTrue(payload["followups"])
        self.assertTrue(all(row["url"].startswith("https://") for row in payload["followups"]))
        self.assertTrue(any("FEMA" in row["title"] for row in payload["followups"]))
        self.assertEqual("PROXY", atoms[0].kind)

    def test_anticipated_gaps_add_constrained_authorities(self):
        from expedition.adapters import extended

        _atoms, payload = extended.source_scout(
            candidate_id="san_marcos_tx",
            lat=29.883,
            lng=-97.941,
            mission="warehouse",
            core_atoms=[],
            anticipated_gaps=["electrical_capacity", "market_availability"],
        )
        titles = " ".join(row["title"] for row in payload["followups"])
        self.assertIn("utility", titles.lower())
        self.assertFalse(payload["discovery"])


if __name__ == "__main__":
    unittest.main()
