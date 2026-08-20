import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from expedition.adapters import discover
from expedition.plan import compile_plan


OVERPASS = {
    "elements": [
        {
            "type": "way",
            "id": 101,
            "center": {"lat": 41.880, "lon": -87.630},
            "tags": {"building": "warehouse", "name": "Goose Island warehouse"},
        },
        {
            "type": "way",
            "id": 102,
            "center": {"lat": 41.881, "lon": -87.631},
            "tags": {"building": "warehouse"},
        },
        {
            "type": "node",
            "id": 103,
            "lat": 29.76,
            "lon": -95.37,
            "tags": {"building": "warehouse", "name": "Houston logistics"},
        },
    ]
}

NOMINATIM = [
    {
        "lat": "41.8755616",
        "lon": "-87.6244212",
        "display_name": "Chicago, Cook County, Illinois, United States",
    }
]


class DiscoverTests(unittest.TestCase):
    def test_overpass_search_labels_potential_not_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(discover, "_http_json", return_value=OVERPASS):
                payload = discover.discover_sites(
                    "warehouse",
                    search_region="chicago",
                    network=True,
                    cache_dir=Path(tmp),
                    fixture_dir=Path(tmp) / "missing",
                )
        ids = [row["id"] for row in payload["candidates"]]
        self.assertIn("osm_way_101", ids)
        self.assertTrue(all(row["label"] == "POTENTIAL" for row in payload["candidates"]))
        self.assertTrue(all(row["source"] == "openstreetmap" for row in payload["candidates"]))
        self.assertNotIn("LISTED", [row["label"] for row in payload["candidates"]])
        self.assertLessEqual(len(payload["candidates"]), discover.MAX_RESULTS)

    def test_look_query_geocodes_then_searches(self):
        calls = []

        def fake_http(url, data=None, timeout=20):
            calls.append(url)
            if "nominatim" in url:
                return NOMINATIM
            return OVERPASS

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(discover, "_http_json", side_effect=fake_http):
                payload = discover.discover_sites(
                    "warehouse",
                    look_query="Chicago, IL",
                    network=True,
                    cache_dir=Path(tmp),
                    fixture_dir=Path(tmp) / "missing",
                )
        self.assertTrue(any("nominatim" in url for url in calls))
        self.assertEqual(payload["look"]["lat"], 41.8755616)
        self.assertGreaterEqual(len(payload["candidates"]), 1)

    def test_replay_without_network_uses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with patch.object(discover, "_http_json", return_value=OVERPASS):
                live = discover.discover_sites(
                    "warehouse",
                    search_region="chicago",
                    network=True,
                    cache_dir=cache,
                    fixture_dir=cache / "missing",
                )
            with patch.object(discover, "_http_json", side_effect=AssertionError("network")):
                replay = discover.discover_sites(
                    "warehouse",
                    search_region="chicago",
                    network=False,
                    cache_dir=cache,
                    fixture_dir=cache / "missing",
                )
        self.assertEqual(live["candidates"][0]["id"], replay["candidates"][0]["id"])

    def test_nearby_duplicates_collapse(self):
        sites = [
            {"id": "a", "lat": 41.88, "lng": -87.63, "name": "A"},
            {"id": "b", "lat": 41.8801, "lng": -87.6301, "name": "B"},
        ]
        kept = discover._dedup(sites)
        self.assertEqual(len(kept), 1)

    def test_compile_plan_accepts_chicago(self):
        plan = compile_plan("warehouse", search_region="chicago")
        self.assertEqual(plan.search_region, "chicago")
