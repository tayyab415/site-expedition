"""Catered end-to-end harness: need text → intent → plan → replay discovery.

Built after the 2026-08-20 board failure: a Phoenix farm plan showed the
Midtown Manhattan starter pin and live Overpass timed out mid-demo. Every
case here runs with the network patched out. Discovery fixtures are real
OpenStreetMap responses captured 2026-08-20 (data/fixtures/discover/).
"""

import unittest
from unittest.mock import patch

from expedition.adapters import discover
from expedition.intent import propose_intent

# Matches BAND_RADIUS_KM.selected_region in ui/app.js with slack for the
# 36 km search radii; a wrong-metro pin fails by thousands of km.
HUB_NEAR_KM = 60.0

MANHATTAN = (40.748, -73.985)

# (need text, mission, search_region the plan must land on)
CASES = [
    ("big farm in Arizona, dry weather, water availability", "farm", "phoenix"),
    (
        "small 80 acre farm in Phoenix, hot and dry, need available water in the soil",
        "farm",
        "phoenix",
    ),
    ("400 acre soybean farm outside Chicago, no flood", "farm", "chicago"),
    ("rice farm near Houston, flood irrigation is fine", "farm", "houston_metro"),
    ("vineyard in California, keep drought burden down", "farm", "los_angeles"),
    ("looking for acreage to run cattle near Denver", "farm", "denver"),
    ("orchard outside Seattle, irrigation and soil water matter", "farm", "seattle"),
    ("hayfields somewhere in Texas, arid conditions", "farm", "texas_triangle"),
    (
        "organic vegetable acreage in the hill country near Austin",
        "farm",
        "austin_san_antonio",
    ),
    ("greenhouse operation near Atlanta for year-round crops", "farm", "atlanta"),
    (
        "warehouse next to a farm near Dallas, rail and highway, no flood",
        "warehouse",
        "dallas_fort_worth",
    ),
    ("data hall in Seattle, keep heat down, fiber context", "data_center", "seattle"),
    # Crop-belt suggestions: no covered metro named, the crop names one.
    ("somewhere warm to grow oranges", "farm", "miami"),
    ("need 5000 acres for wheat in Montana", "farm", "denver"),
]

OPEN_GEOGRAPHY_CASES = (
    "farm in Toronto",
    "lookign for warehouse for my business prefeabley 80,000 sq feet",
)


def _replay(mission: str, region: str) -> dict:
    with patch.object(discover, "_http_json", side_effect=AssertionError("network hit in replay")):
        return discover.discover_sites(mission, search_region=region, network=False)


def _hub_km(site: dict, region: str) -> float:
    return min(
        discover._distance_km(site["lat"], site["lng"], lat, lng)
        for lat, lng, _ in discover.REGION_HUBS[region]
    )


class CateredHarnessTests(unittest.TestCase):
    def test_catered_cases_end_to_end(self):
        for text, mission, region in CASES:
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertTrue(result["ok"])
                controls = result["controls"]
                self.assertEqual(controls["mission"], mission)
                self.assertEqual(controls["search_region"], region)
                self.assertEqual(result["plan"]["mission"], mission)

                payload = _replay(mission, region)
                candidates = payload["candidates"]
                self.assertGreaterEqual(
                    len(candidates), 1, f"no replay pins for {mission}|{region}"
                )
                for site in candidates:
                    self.assertEqual(site["label"], "POTENTIAL")
                    self.assertEqual(site["source"], "openstreetmap")
                    km = _hub_km(site, region)
                    self.assertLessEqual(
                        km,
                        HUB_NEAR_KM,
                        f"{site['name']} is {km:.0f} km from the {region} hub: wrong metro",
                    )
                scores = [
                    site["distance_km"] - (5.0 if site.get("named") else 0.0)
                    for site in candidates
                ]
                self.assertEqual(scores, sorted(scores), f"{mission}|{region} pins are unranked")

    def test_phoenix_farm_never_shows_manhattan(self):
        payload = _replay("farm", "phoenix")
        for site in payload["candidates"]:
            km = discover._distance_km(site["lat"], site["lng"], *MANHATTAN)
            self.assertGreater(km, 500, f"{site['name']} sits near Midtown Manhattan")

    def test_open_geography_needs_no_metro(self):
        for text in OPEN_GEOGRAPHY_CASES:
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertTrue(result["ok"])
                self.assertTrue(result["open_inventory"])
                self.assertEqual(result["region_allowlist"], [])

    def test_no_fixture_claims_listed(self):
        import json

        for path in sorted(discover.FIXTURE_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for site in payload.get("candidates", []):
                self.assertNotEqual(site.get("label"), "LISTED", path.name)


class GateStarsTests(unittest.TestCase):
    """Stars are a rendering of the deterministic verdict, never a score."""

    def test_stars_map_verdict_and_blocking_gaps(self):
        from expedition.verdict import gate_stars

        self.assertEqual(gate_stars("reject", [{"blocking": True}]), 1)
        self.assertEqual(gate_stars("strong_fit", []), 5)
        self.assertEqual(gate_stars("conditional", [{"blocking": True}] * 5), 2)
        self.assertEqual(gate_stars("conditional", [{"blocking": True}] * 4), 3)
        self.assertEqual(
            gate_stars("conditional", [{"blocking": True}] * 2 + [{"blocking": False}] * 3),
            4,
        )


class AdversarialIntentTests(unittest.TestCase):
    """Catered asks that used to silently become warehouse searches."""

    REFUSALS = (
        "looking for opening a cafe in atlanta",
        "hotel near miami beach",
        "gym franchise location in Dallas",
        "small apartment building in Chicago",
        "solar farm in Texas",
        "wind farm in Iowa",
    )

    def test_unsupported_uses_are_refused_not_warehoused(self):
        for text in self.REFUSALS:
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "unsupported_use")
                self.assertIn("farm", result["supported"])
                self.assertTrue(result["message"])

    def test_energy_farms_are_not_agriculture(self):
        result = propose_intent("solar farm in Texas", live_model=False)
        self.assertIn("energy site", result["message"])

    def test_crop_mismatch_warns_but_keeps_user_geography(self):
        result = propose_intent("cotton plantation in Denver", live_model=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["crop"], "cotton")
        self.assertEqual(result["region_allowlist"], ["denver"])
        self.assertTrue(
            any("not a typical crop" in note for note in result["rationale"]),
            result["rationale"],
        )

    def test_crop_belt_stands_in_when_no_metro_named(self):
        result = propose_intent("somewhere warm to grow oranges", live_model=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["crop"], "citrus")
        self.assertEqual(result["region_allowlist"], ["miami", "phoenix", "los_angeles"])
        self.assertTrue(any("citrus belt" in note for note in result["rationale"]))

    def test_sqft_variants_hit_the_same_band(self):
        for text in (
            "warehouse for my business preferably 80k sq ft",
            "lookign for warehouse for my business prefeabley 80,000 sq feet",
            "warehouse around 80000 sf",
        ):
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertEqual(result["controls"]["size_band"], "under_100k_sqft")

    def test_non_us_geography_is_named_honestly(self):
        result = propose_intent("farm in Toronto", live_model=False)
        self.assertTrue(result["ok"])
        self.assertTrue(any("US-only" in note for note in result["rationale"]))

    def test_named_geography_wins_over_the_crop_belt(self):
        # "corn plantations in New Jersey" must keep the user's geography
        # (New York band covers northern NJ), not swap in a distant corn belt.
        result = propose_intent("corn plantations in New Jersey", live_model=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["region_allowlist"], ["new_york"])
        self.assertEqual(result["controls"]["search_region"], "new_york")
        self.assertTrue(
            any("nearest covered metro" in note for note in result["rationale"])
        )
        self.assertTrue(
            any("not a typical crop" in note for note in result["rationale"])
        )

    def test_adjacent_state_maps_to_nearest_metro(self):
        for text, region in (
            ("dairy farm in Wisconsin", "chicago"),
            ("Iowa corn farm, dry summers, soil water availability", "chicago"),
        ):
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertEqual(result["region_allowlist"], [region])

    def test_uncovered_state_is_named_honestly(self):
        result = propose_intent("need 5000 acres for wheat in Montana", live_model=False)
        self.assertTrue(result["ok"])
        self.assertTrue(any("no locate coverage" in note for note in result["rationale"]))
        self.assertEqual(result["controls"]["size_band"], "2000_plus_acres")

    def test_poultry_does_not_require_cultivated_cropland(self):
        result = propose_intent("chicken farm near Atlanta", live_model=False)
        self.assertTrue(result["ok"])
        self.assertFalse(result["controls"]["require_cultivated"])

    def test_waterfront_with_flood_veto_gets_a_caution(self):
        result = propose_intent(
            "riverfront warehouse with no flood risk ever", live_model=False
        )
        self.assertTrue(result["ok"])
        self.assertTrue(any("Waterfront" in note for note in result["rationale"]))

    def test_typo_heavy_farm_ask_still_lands_on_farm(self):
        result = propose_intent(
            "lokking for cooton plantations in seattle", live_model=False
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["controls"]["mission"], "farm")
        self.assertEqual(result["region_allowlist"], ["seattle"])

    def test_server_farm_is_a_data_center_not_agriculture(self):
        result = propose_intent("server farm in Virginia", live_model=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["controls"]["mission"], "data_center")

    def test_british_data_centre_spelling(self):
        result = propose_intent("data centre in Phoenix", live_model=False)
        self.assertEqual(result["controls"]["mission"], "data_center")

    def test_negated_preference_is_not_set(self):
        result = propose_intent(
            "warehouse, no rail needed, but highway access", live_model=False
        )
        prefs = {row["id"] for row in result["controls"]["preferences"]}
        self.assertIn("major_road_access", prefs)
        self.assertNotIn("rail_access", prefs)

    def test_negated_geography_is_not_selected(self):
        result = propose_intent("warehouse anywhere but not in Texas", live_model=False)
        self.assertEqual(result["region_allowlist"], [])
        result = propose_intent("avoid Houston, prefer Dallas warehouse", live_model=False)
        self.assertEqual(result["region_allowlist"], ["dallas_fort_worth"])

    def test_facilities_with_home_words_are_refused(self):
        for text in ("retirement home in Phoenix", "mobile home park in Houston"):
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertFalse(result["ok"])
                self.assertIn("commercial facility", result["message"])

    def test_homestead_is_home_with_acre_bands(self):
        result = propose_intent("half acre homestead near Austin", live_model=False)
        self.assertEqual(result["controls"]["mission"], "home")
        self.assertEqual(result["controls"]["size_band"], "under_20_acres")
        result = propose_intent("20 acre homestead outside Denver", live_model=False)
        self.assertEqual(result["controls"]["size_band"], "20_50_acres")

    def test_home_sqft_with_under_qualifier(self):
        result = propose_intent("house in Seattle under 2500 sqft", live_model=False)
        self.assertEqual(result["controls"]["size_band"], "1500_2500_sqft")

    def test_million_sqft_parses(self):
        result = propose_intent("3 million sq ft campus", live_model=False)
        self.assertEqual(result["controls"]["size_band"], "500k_plus_sqft")

    def test_aquaculture_and_timber_do_not_require_cultivated(self):
        for text in ("fish farm in Miami", "tree farm in Georgia"):
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertEqual(result["controls"]["mission"], "farm")
                self.assertFalse(result["controls"]["require_cultivated"])

    def test_coffee_note_survives_the_model_merge(self):
        # The live path replaces the deterministic rationale with the model's.
        # The honesty note must survive that merge — it did not on 2026-08-20
        # ("coffee plantations in us" on the board showed no Hawaii note).
        luna_reply = {
            "ok": True,
            "text": (
                '{"mission": "farm", "region_allowlist": [], '
                '"flood_intolerant": false, "require_cultivated": true, '
                '"rationale": ["Coffee plantations require cultivated '
                'agricultural land."]}'
            ),
            "model": "gpt-5.6-luna",
        }
        with patch("expedition.intent._complete_intent", return_value=luna_reply):
            result = propose_intent("coffee plantations in us", live_model=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "model")
        self.assertEqual(result["crop"], "coffee")
        self.assertTrue(
            any("Hawaii" in note for note in result["rationale"]),
            result["rationale"],
        )

    def test_geography_note_survives_the_model_merge(self):
        luna_reply = {
            "ok": True,
            "text": '{"mission": "farm", "region_allowlist": [], "rationale": ["A farm."]}',
            "model": "gpt-5.6-luna",
        }
        with patch("expedition.intent._complete_intent", return_value=luna_reply):
            result = propose_intent("farm in Toronto", live_model=True)
        self.assertTrue(any("US-only" in note for note in result["rationale"]))

    def test_coffee_gets_an_honest_no_belt_note(self):
        for text in ("coffee plantations in us", "coffee plantation in texas"):
            with self.subTest(text=text):
                result = propose_intent(text, live_model=False)
                self.assertTrue(result["ok"])
                self.assertEqual(result["controls"]["mission"], "farm")
                self.assertEqual(result["crop"], "coffee")
                self.assertTrue(
                    any("Hawaii" in note for note in result["rationale"]),
                    result["rationale"],
                )

    def test_no_belt_crop_never_invents_a_region(self):
        result = propose_intent("coffee plantations", live_model=False)
        self.assertEqual(result["region_allowlist"], [])
        self.assertTrue(result["open_inventory"])

    def test_winery_lands_on_farm_in_the_grape_belt(self):
        result = propose_intent(
            "grow grapes for a winery in the hill country", live_model=False
        )
        self.assertEqual(result["controls"]["mission"], "farm")
        self.assertEqual(result["crop"], "grapes")
        self.assertEqual(result["region_allowlist"], ["austin_san_antonio"])
        self.assertFalse(
            any("not a typical crop" in note for note in result["rationale"])
        )


if __name__ == "__main__":
    unittest.main()
