"""Literal intent cases. These failed the substring parser (corn plantations → warehouse)."""

import json
import unittest
from pathlib import Path

from expedition.intent import parse_intent, propose_intent


CASES_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "intent" / "cases.json"
)


def _cases() -> list[dict]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return list(payload["cases"])


class IntentHarnessTests(unittest.TestCase):
    def test_harness_has_at_least_ten_cases(self):
        self.assertGreaterEqual(len(_cases()), 10)

    def test_fixture_literals(self):
        for case in _cases():
            with self.subTest(case["id"]):
                got = parse_intent(case["text"])
                exp = case["expect"]
                self.assertEqual(exp["mission"], got["mission"], got["rationale"])
                self.assertEqual(exp["flood_intolerant"], got["flood_intolerant"])
                self.assertEqual(exp["require_cultivated"], got["require_cultivated"])
                self.assertEqual(exp["size_band"], got["size_band"])
                self.assertEqual(exp["region_allowlist"], got["region_allowlist"])
                self.assertEqual(
                    set(exp["preference_ids"]),
                    {row["id"] for row in got["preferences"]},
                )

    def test_compiled_plan_matches_mission_and_flood_gate(self):
        for case in _cases():
            with self.subTest(case["id"]):
                result = propose_intent(case["text"])
                exp = case["expect"]
                self.assertTrue(result["ok"])
                self.assertEqual(exp["mission"], result["controls"]["mission"])
                self.assertEqual(
                    exp["flood_intolerant"], result["controls"]["flood_intolerant"]
                )
                self.assertEqual(exp["size_band"], result["controls"]["size_band"])
                self.assertEqual(
                    exp["require_cultivated"], result["controls"]["require_cultivated"]
                )
                if exp["flood_intolerant"]:
                    self.assertIn("not_mapped_sfha", result["plan"]["hard_constraints"])
                else:
                    self.assertNotIn("not_mapped_sfha", result["plan"]["hard_constraints"])
                if exp["require_cultivated"]:
                    self.assertIn("must_be_cultivated", result["plan"]["hard_constraints"])
                else:
                    self.assertNotIn("must_be_cultivated", result["plan"]["hard_constraints"])


if __name__ == "__main__":
    unittest.main()
