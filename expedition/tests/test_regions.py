"""Region aggregation and ranking. Expected values are fixture literals."""

import copy
import json
import math
import unittest

from expedition.regions import (
    aggregate_region,
    expand_allowlist,
    load_catalog,
    load_replay,
    locate_inventory,
    rank_regions,
)


class RegionHarnessTests(unittest.TestCase):
    def test_locate_inventory_excludes_texas_triangle(self):
        inventory = locate_inventory()
        self.assertNotIn("texas_triangle", inventory)
        self.assertEqual(11, len(inventory))
        self.assertIn("dallas_fort_worth", inventory)
        self.assertIn("houston_metro", inventory)

    def test_texas_triangle_expands_to_three_metros(self):
        self.assertEqual(
            ["houston_metro", "austin_san_antonio", "dallas_fort_worth"],
            expand_allowlist(["texas_triangle"]),
        )

    def test_multi_texas_metros_search_the_triangle(self):
        from expedition.regions import default_search_region

        self.assertEqual(
            "texas_triangle",
            default_search_region(
                ["houston_metro", "austin_san_antonio", "dallas_fort_worth"]
            ),
        )
        self.assertEqual("dallas_fort_worth", default_search_region(["dallas_fort_worth"]))

    def test_adjacent_band_adds_neighbors_not_other_states(self):
        expanded = expand_allowlist(
            ["dallas_fort_worth"], geography_band="adjacent_regions"
        )
        self.assertEqual(
            ["dallas_fort_worth", "austin_san_antonio", "houston_metro"],
            expanded,
        )
        self.assertNotIn("chicago", expanded)

    def test_houston_sfha_share_is_one_of_four_probes(self):
        bundle = aggregate_region("houston_metro")
        self.assertEqual(4, bundle["probe_count"])
        share = bundle["metrics"]["mapped_sfha_share"]
        self.assertEqual("share", share["method"])
        self.assertEqual(0.25, share["value"])
        self.assertEqual("PROXY", share["kind"])
        self.assertEqual("region", bundle["spatial_support"]["kind"])

    def test_houston_rail_is_the_ship_channel_probe(self):
        bundle = aggregate_region("houston_metro")
        self.assertEqual(400.0, bundle["metrics"]["rail_distance_m"]["value"])
        self.assertEqual("min", bundle["metrics"]["rail_distance_m"]["method"])

    def test_dfw_has_no_mapped_sfha_probes_and_alliance_rail(self):
        bundle = aggregate_region("dallas_fort_worth")
        self.assertEqual(0.0, bundle["metrics"]["mapped_sfha_share"]["value"])
        self.assertEqual(600.0, bundle["metrics"]["rail_distance_m"]["value"])
        self.assertEqual(1500.0, bundle["metrics"]["grid_distance_m"]["value"])

    def test_labor_sums_counties_and_never_claims_workers(self):
        bundle = aggregate_region("dallas_fort_worth", mission="warehouse")
        labor = bundle["metrics"]["civilian_employed"]
        self.assertEqual("sum", labor["method"])
        self.assertEqual(1408200 + 1072100, labor["value"])
        self.assertIsNone(labor["workers_available"])
        self.assertEqual("county", labor["scale"])

    def test_home_omits_labor_entirely(self):
        warehouse = aggregate_region("houston_metro", mission="warehouse")
        home = aggregate_region("houston_metro", mission="home")
        self.assertIn("civilian_employed", warehouse["metrics"])
        self.assertNotIn("civilian_employed", home["metrics"])

    def test_null_probe_is_not_a_false_for_share(self):
        replay = copy.deepcopy(load_replay())
        catalog = load_catalog()
        replay["probes"]["houston_cbd"]["mapped_sfha"] = None
        bundle = aggregate_region(
            "houston_metro", catalog=catalog, replay=replay, mission="warehouse"
        )
        # 1 true, 2 false, 1 null → 1/3, not 1/4 and not 0.
        self.assertAlmostEqual(1 / 3, bundle["metrics"]["mapped_sfha_share"]["value"])
        self.assertEqual(3, bundle["metrics"]["mapped_sfha_share"]["known_probes"])

    def test_all_null_metric_is_unknown_not_zero(self):
        replay = copy.deepcopy(load_replay())
        for probe_id in ("dallas_cbd", "fort_worth_cbd", "alliance"):
            replay["probes"][probe_id]["nearest_substation_distance_m"] = None
        bundle = aggregate_region(
            "dallas_fort_worth",
            catalog=load_catalog(),
            replay=replay,
            mission="warehouse",
        )
        grid = bundle["metrics"]["grid_distance_m"]
        self.assertIsNone(grid["value"])
        self.assertEqual("UNKNOWN", grid["kind"])
        self.assertIn("grid_distance_m", bundle["unknowns"])

    def test_flood_intolerant_warehouse_ranks_dfw_ahead_of_houston(self):
        packet = rank_regions(
            "warehouse",
            allowlist=["texas_triangle"],
            flood_intolerant=True,
            preferences=[{"id": "rail_access", "weight": "priority"}],
        )
        self.assertEqual(
            ["dallas_fort_worth", "houston_metro", "austin_san_antonio"],
            packet["survivors"],
        )
        self.assertEqual(0, packet["credits"]["spent"])
        self.assertFalse(packet["credits"]["mireye"])
        self.assertIn("not a suitability score", packet["honesty"].lower())
        dfw = packet["regions"][0]
        self.assertEqual("dallas_fort_worth", dfw["region_id"])
        self.assertIn("mapped SFHA share", dfw["preference_basis"][1])

    def test_without_flood_gate_houston_wins_on_rail(self):
        packet = rank_regions(
            "warehouse",
            allowlist=["texas_triangle"],
            flood_intolerant=False,
            preferences=[{"id": "rail_access", "weight": "priority"}],
        )
        self.assertEqual("houston_metro", packet["top_region_ids"][0])
        self.assertEqual(
            ["houston_metro", "dallas_fort_worth", "austin_san_antonio"],
            packet["survivors"],
        )

    def test_dropping_rail_priority_can_swap_houston_and_dfw(self):
        packet = rank_regions(
            "warehouse",
            allowlist=["texas_triangle"],
            flood_intolerant=False,
            preferences=[
                {"id": "rail_access", "weight": "priority"},
                {"id": "grid_proximity", "weight": "important"},
            ],
        )
        self.assertEqual("houston_metro", packet["top_region_ids"][0])
        swap = next(row for row in packet["sensitivity"] if row["dropped"] == "rail_access")
        self.assertTrue(swap["order_changed"])
        self.assertEqual("dallas_fort_worth", swap["top_becomes"])

    def test_home_flood_vetoes_miami_and_strips_labor(self):
        packet = rank_regions(
            "home",
            allowlist=["miami", "denver", "dallas_fort_worth"],
            flood_intolerant=True,
            preferences=[
                {"id": "lower_wildfire", "weight": "priority"},
                {"id": "labor_access", "weight": "priority"},
            ],
        )
        vetoed = {row["region_id"]: row["reason"] for row in packet["vetoed"]}
        self.assertIn("miami", vetoed)
        self.assertIn("SFHA", vetoed["miami"])
        miami = next(row for row in packet["regions"] if row["region_id"] == "miami")
        self.assertEqual("vetoed", miami["status"])
        denver = next(row for row in packet["regions"] if row["region_id"] == "denver")
        self.assertNotIn("civilian_employed", denver["metrics"])
        self.assertEqual("survivor", denver["status"])

    def test_labor_is_never_a_sort_key(self):
        packet = rank_regions(
            "warehouse",
            allowlist=["houston_metro", "denver"],
            flood_intolerant=False,
            preferences=[{"id": "labor_access", "weight": "priority"}],
        )
        houston = next(row for row in packet["regions"] if row["region_id"] == "houston_metro")
        self.assertEqual(["not vetoed"], houston["preference_basis"])
        self.assertEqual([], houston["preference_sort"])
        self.assertIn("civilian_employed", houston["metrics"])

    def test_unknown_route_time_does_not_emit_non_finite_json(self):
        """Board preference selects default to useful, including route_time.

        No probe carries a declared-anchor duration, so the internal sort key
        is +inf. The HTTP handler refuses NaN/Inf, so the packet must serialize
        with allow_nan=False.
        """
        packet = rank_regions(
            "warehouse",
            allowlist=["dallas_fort_worth", "houston_metro", "austin_san_antonio"],
            flood_intolerant=True,
            preferences=[
                {"id": "major_road_access", "weight": "priority"},
                {"id": "route_time", "weight": "useful"},
                {"id": "rail_access", "weight": "priority"},
                {"id": "grid_proximity", "weight": "useful"},
            ],
        )
        json.dumps(packet, allow_nan=False)
        self.assertEqual("dallas_fort_worth", packet["top_region_ids"][0])
        self.assertEqual(0, packet["credits"]["spent"])
        for row in packet["regions"]:
            for value in row["preference_sort"]:
                if value is None:
                    continue
                self.assertTrue(math.isfinite(value), value)


if __name__ == "__main__":
    unittest.main()
