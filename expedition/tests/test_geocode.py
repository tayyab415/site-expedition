import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from expedition.adapters.mireye import resolve_address


ADDRESS = "3605 Winfield Cove, Austin, TX 78704"


class GeocodeTests(unittest.TestCase):
    def test_rooftop_resolution_is_cached_and_replayed(self):
        raw = {
            "lat": 30.2363775,
            "lng": -97.7807633,
            "accuracy": 1.0,
            "accuracy_type": "rooftop",
            "normalized_address": ADDRESS,
            "provider": "geocodio",
            "source": "local authority",
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            with patch("expedition.adapters.mireye.credits.authorize"), patch(
                "expedition.adapters.mireye._request", return_value=raw
            ):
                live, spent = resolve_address(ADDRESS, live=True, cache_dir=cache_dir)
            replay, replay_spent = resolve_address(ADDRESS, live=False, cache_dir=cache_dir)
        self.assertEqual(live["disposition"], "resolved")
        self.assertTrue(live["parcel_grade"])
        self.assertEqual(spent, 1)
        self.assertEqual(replay["lat"], 30.2363775)
        self.assertEqual(replay_spent, 0)

    def test_range_interpolation_requires_clarification(self):
        raw = {
            "lat": 30.23,
            "lng": -97.78,
            "accuracy_type": "range_interpolation",
            "normalized_address": ADDRESS,
        }
        with tempfile.TemporaryDirectory() as tmp, patch(
            "expedition.adapters.mireye.credits.authorize"
        ), patch("expedition.adapters.mireye._request", return_value=raw):
            result, _ = resolve_address(ADDRESS, live=True, cache_dir=Path(tmp))
        self.assertEqual(result["disposition"], "clarify")
        self.assertFalse(result["candidates"][0]["parcel_grade"])

    def test_incomplete_input_stops_before_call(self):
        with patch("expedition.adapters.mireye._request") as request:
            result, spent = resolve_address("Springfield", live=True)
        request.assert_not_called()
        self.assertEqual(result["disposition"], "clarify")
        self.assertEqual(spent, 0)

    def test_replay_without_cache_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                resolve_address(ADDRESS, live=False, cache_dir=Path(tmp))


if __name__ == "__main__":
    unittest.main()
