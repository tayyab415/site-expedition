import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

from expedition.adapters.streetview import street_meta


class StreetViewTests(unittest.TestCase):
    def test_ok_coverage_is_cached_without_image_bytes(self):
        raw = {
            "status": "OK",
            "pano_id": "abc",
            "copyright": "© Google",
            "date": "2025-01",
            "location": {"lat": 29.883, "lng": -97.941},
        }
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "expedition.adapters.streetview.lookup_metadata",
                return_value=raw,
            ) as lookup:
                first = street_meta(29.883, -97.941, cache_dir=Path(tmp), key="not-secret")
                second = street_meta(29.883, -97.941, cache_dir=Path(tmp), key="not-secret")
        self.assertTrue(first["available"])
        self.assertEqual(first["pano_id"], "abc")
        self.assertEqual(second["status"], "OK")
        self.assertEqual(lookup.call_count, 1)
        self.assertNotIn("image", str(first))

    def test_zero_results_is_an_honest_miss(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "expedition.adapters.streetview.lookup_metadata",
                return_value={"status": "ZERO_RESULTS"},
            ):
                out = street_meta(29.73, -95.12, cache_dir=Path(tmp), key="not-secret")
        self.assertFalse(out["available"])
        self.assertEqual(out["status"], "ZERO_RESULTS")

    def test_http_error_does_not_raise(self):
        error = urllib.error.HTTPError("url", 403, "blocked", {}, None)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("expedition.adapters.streetview.lookup_metadata", side_effect=error):
                out = street_meta(40.0, -90.0, cache_dir=Path(tmp), key="not-secret")
        self.assertFalse(out["available"])
        self.assertEqual(out["http_status"], 403)


if __name__ == "__main__":
    unittest.main()
