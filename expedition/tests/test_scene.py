"""Scene reconstruction is a public packet contract, not a UI decoration.

Known literals come from the San Leon Earth Engine replay cache and the
warehouse glTF extras — not from recomputing the adapter.
"""

import unittest

from expedition.engine import run_site


class SceneReconstructionTests(unittest.TestCase):
    def test_san_leon_past_uses_cached_jrc_years_and_does_not_score(self):
        packet = run_site(
            "warehouse",
            "san_leon",
            controls={"scan_budget": "standard"},
        )
        self.assertEqual("reject", packet["verdict"]["verdict"])
        self.assertIn("mapped_sfha", packet["verdict"]["reasons"])

        scene = packet["scene"]
        self.assertFalse(scene["google_tiles_used"])
        self.assertFalse(scene["parcel_fields_used"])
        self.assertEqual("deferred", scene["fit"]["claim"])

        past = scene["past"]
        self.assertEqual("flood_rewind", past["kind"])
        self.assertFalse(past["scores"])
        self.assertEqual("JRC_GSW", past["independence_group"])
        self.assertEqual(2001, past["breakpoint_year"])
        by_year = {row["year"]: row["water_freq"] for row in past["series"]}
        self.assertEqual(0.0, by_year[1985])
        self.assertEqual(0.1159, by_year[2001])
        self.assertGreater(by_year[2001], by_year[1999])

    def test_warehouse_pad_is_an_assumption_never_a_licensed_fit(self):
        packet = run_site(
            "warehouse",
            "san_marcos_tx",
            controls={"scan_budget": "standard"},
        )
        self.assertEqual("conditional", packet["verdict"]["verdict"])
        pad = packet["scene"]["assumed_pad"]
        self.assertEqual("assumption", pad["claim"])
        self.assertEqual("deferred", packet["scene"]["fit"]["claim"])
        self.assertEqual(80, pad["length_m"])
        self.assertEqual(40, pad["width_m"])
        self.assertEqual(10, pad["height_m"])
        self.assertEqual(10, pad["setback_m"])
        self.assertEqual("visual_concept", packet["scene"]["future"]["claim"])
        self.assertIn("not a permit", packet["scene"]["future"]["note"].lower())

    def test_farm_past_is_rotation_summary_not_invented_yearly_water(self):
        packet = run_site(
            "farm",
            "iowa_corn",
            controls={"scan_budget": "standard"},
        )
        past = packet["scene"]["past"]
        self.assertEqual("farm_history", past["kind"])
        self.assertFalse(past["scores"])
        self.assertEqual([], past["series"])
        self.assertEqual(9, past["years_observed"])
        self.assertIsNone(packet["scene"]["assumed_pad"])
        self.assertEqual("deferred", packet["scene"]["future"]["claim"])
        self.assertEqual("deferred", packet["scene"]["fit"]["claim"])

    def test_scorecard_meters_are_status_fills_not_a_composite_score(self):
        packet = run_site(
            "warehouse",
            "san_leon",
            controls={"scan_budget": "standard"},
        )
        by_id = {row["id"]: row for row in packet["scorecard"]}
        self.assertEqual("fail", by_id["flood"]["status"])
        self.assertEqual(100, by_id["flood"]["meter"])
        self.assertEqual("fail", by_id["flood"]["tone"])
        self.assertEqual("unknown", by_id["availability"]["status"])
        self.assertEqual(35, by_id["availability"]["meter"])
        self.assertNotIn("score", packet)
        self.assertNotIn("composite", str(packet["scorecard"]).lower())
