import unittest
from unittest.mock import patch

from expedition.engine import run_mission


WAREHOUSE_IDS = [
    "san_leon",
    "san_marcos_tx",
    "alliance_tx",
    "port_houston",
    "joliet_il",
]


class SkepticReviewTests(unittest.TestCase):
    def test_survivors_are_reviewed_automatically(self):
        review = {
            "stamp": "SKEPTIC REVIEW",
            "flags": ["clean"],
            "deterministic_flags": [],
            "model_flags": ["clean"],
            "notes": "No visible defect.",
            "model": "gemini-3.5-flash-lite",
            "provider": "vertex",
            "ok": True,
            "cached": False,
        }
        with patch("expedition.engine.skeptic_review", return_value=review) as mocked:
            packet = run_mission("warehouse", WAREHOUSE_IDS, live=False)
        mocked.assert_called_once()
        by_id = {result["candidate"]["id"]: result for result in packet["results"]}
        self.assertNotIn("skeptic", by_id["san_leon"])
        for candidate_id in WAREHOUSE_IDS[1:]:
            self.assertEqual(by_id[candidate_id]["skeptic"]["stamp"], "SKEPTIC REVIEW")
            self.assertTrue(
                any(w["id"] == "skeptic-review" for w in by_id[candidate_id]["workstreams"])
            )

    def test_override_reviews_rejects_without_changing_verdict(self):
        review = {
            "stamp": "SKEPTIC REVIEW",
            "flags": ["clean"],
            "deterministic_flags": [],
            "model_flags": [],
            "notes": "Deterministic review.",
            "model": None,
            "provider": None,
            "ok": False,
            "cached": False,
        }
        with patch("expedition.engine.skeptic_review", return_value=review):
            packet = run_mission("warehouse", WAREHOUSE_IDS, live=False, review=True)
        san_leon = next(r for r in packet["results"] if r["candidate"]["id"] == "san_leon")
        self.assertEqual(san_leon["verdict"]["verdict"], "reject")
        self.assertIn("skeptic", san_leon)


if __name__ == "__main__":
    unittest.main()
