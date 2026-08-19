import unittest

from expedition.engine import run_site
from expedition.verify.score import score_packet


class HeldOutTests(unittest.TestCase):
    def test_manhattan_farm_matches_held_out_gate(self):
        packet = run_site("farm", "manhattan_midtown", live=False)
        scored = score_packet(
            {"id": "F-bad", "expect_verdict": "reject", "must_include_reason": "not_cultivated"},
            packet,
        )
        self.assertTrue(scored["pass"], scored)

    def test_elba_not_rejected(self):
        packet = run_site("farm", "elba_ny", live=False)
        scored = score_packet(
            {"id": "F-good-NY", "forbid_verdict": "reject", "forbid_reason": "state_is_new_york"},
            packet,
        )
        self.assertTrue(scored["pass"], scored)

    def test_san_leon_warehouse_reject(self):
        packet = run_site("warehouse", "san_leon", live=False)
        scored = score_packet(
            {"id": "W-kill", "expect_verdict": "reject", "must_include_reason": "mapped_sfha"},
            packet,
        )
        self.assertTrue(scored["pass"], scored)

    def test_warehouse_expedition_compares_five(self):
        from expedition.engine import run_mission

        out = run_mission(
            "warehouse",
            ["san_leon", "san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"],
            live=False,
        )
        by_id = {row["candidate_id"]: row for row in out["comparison"]}
        self.assertEqual(by_id["san_leon"]["verdict"], "reject")
        for cid in ("san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"):
            self.assertEqual(by_id[cid]["verdict"], "conditional")
            self.assertIn("Would Reject", by_id[cid]["counterfactual"])
        self.assertEqual(out["comparison"][-1]["candidate_id"], "san_leon")
        self.assertEqual(out["comparison"][0]["candidate_id"], "san_marcos_tx")
        self.assertIn("scorecard", out["results"][0])
        self.assertGreaterEqual(out["results"][0]["coverage"]["relevant"], 1)

    def test_inline_user_site_keeps_label(self):
        packet = run_site(
            "warehouse",
            "san_leon",
            live=False,
            candidate={
                "id": "san_leon",
                "name": "User pin at San Leon",
                "lat": 29.475732,
                "lng": -94.966533,
                "label": "USER SITE",
            },
        )
        self.assertEqual(packet["candidate"]["label"], "USER SITE")
        self.assertEqual(packet["verdict"]["verdict"], "reject")
        self.assertIn("mapped_sfha", packet["verdict"]["reasons"])
