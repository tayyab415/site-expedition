import unittest

from expedition.intent import parse_intent, propose_intent


class IntentTests(unittest.TestCase):
    def test_warehouse_dallas_no_flood_compiles(self):
        result = propose_intent(
            "I need a warehouse near Dallas with rail and highway access, no flood"
        )
        self.assertTrue(result["ok"])
        self.assertEqual("deterministic", result["source"])
        self.assertEqual("warehouse", result["controls"]["mission"])
        self.assertEqual("dallas_fort_worth", result["controls"]["search_region"])
        self.assertEqual(["dallas_fort_worth"], result["region_allowlist"])
        self.assertTrue(result["controls"]["flood_intolerant"])
        pref_ids = {row["id"] for row in result["controls"]["preferences"]}
        self.assertIn("rail_access", pref_ids)
        self.assertIn("major_road_access", pref_ids)
        self.assertEqual("warehouse", result["plan"]["mission"])
        self.assertIn("not_mapped_sfha", result["plan"]["hard_constraints"])

    def test_texas_wide_keeps_three_metros(self):
        parsed = parse_intent("logistics warehouse somewhere in Texas")
        self.assertEqual("warehouse", parsed["mission"])
        self.assertEqual(
            ["houston_metro", "austin_san_antonio", "dallas_fort_worth"],
            parsed["region_allowlist"],
        )
        self.assertEqual("texas_triangle", parsed["search_region"])

    def test_home_denver_wildfire_strips_labor(self):
        result = propose_intent(
            "Looking for a home in Denver, lower wildfire, and rank by labor market"
        )
        self.assertEqual("home", result["controls"]["mission"])
        self.assertEqual(["denver"], result["region_allowlist"])
        pref_ids = {row["id"] for row in result["controls"]["preferences"]}
        self.assertIn("lower_wildfire", pref_ids)
        self.assertNotIn("labor_access", pref_ids)
        self.assertNotIn("labor-access", result["plan"]["skills"])

    def test_empty_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            propose_intent("   ")

    def test_live_model_failure_falls_back_to_deterministic(self):
        from unittest.mock import patch

        with patch("expedition.intent._complete_intent", side_effect=RuntimeError("offline")):
            result = propose_intent("warehouse in Chicago", live_model=True)
        self.assertTrue(result["ok"])
        self.assertEqual("deterministic", result["source"])
        self.assertEqual("warehouse", result["controls"]["mission"])
        self.assertEqual(["chicago"], result["region_allowlist"])

    def test_luna_farm_overlay_does_not_keep_warehouse_flood(self):
        from unittest.mock import patch

        payload = {
            "ok": True,
            "text": '{"mission":"farm","preferences":[{"id":"drought_context","weight":"priority"}]}',
            "provider": "azure",
            "model": "gpt-5.6-luna",
        }
        with patch("expedition.intent._complete_intent", return_value=payload):
            result = propose_intent("a place for growing food", live_model=True)
        self.assertEqual("model", result["source"])
        self.assertEqual("farm", result["controls"]["mission"])
        self.assertFalse(result["controls"]["flood_intolerant"])
        self.assertEqual("azure", result["provider"])
        self.assertEqual("gpt-5.6-luna", result["model"])
        self.assertNotIn("not_mapped_sfha", result["plan"]["hard_constraints"])
        self.assertIn("must_be_cultivated", result["plan"]["hard_constraints"])


if __name__ == "__main__":
    unittest.main()
