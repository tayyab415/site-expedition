import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

from expedition.adapters.aerial import aerial_atoms, playback_uri


SITE = {"lat": 29.475732, "lng": -94.966533}


class AerialTests(unittest.TestCase):
    def test_active_retains_only_video_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "expedition.adapters.aerial.lookup_metadata",
                return_value={"state": "ACTIVE", "videoId": "abc123", "uris": {"MP4_HIGH": "signed"}},
            ):
                atoms, scene = aerial_atoms(
                    "site", SITE, True, cache_dir=Path(tmp), key="not-secret"
                )
            cache_text = (Path(tmp) / "site.json").read_text()
        self.assertEqual(scene["video_id"], "abc123")
        self.assertEqual(atoms[0].kind, "PRESENTATION")
        self.assertEqual(atoms[0].decision_effect, "NONE")
        self.assertNotIn("signed", cache_text)
        self.assertNotIn("uris", cache_text)

    def test_404_is_typed_and_falls_back_to_3d(self):
        error = urllib.error.HTTPError("url", 404, "not found", {}, None)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("expedition.adapters.aerial.lookup_metadata", side_effect=error):
                atoms, scene = aerial_atoms(
                    "site", SITE, True, cache_dir=Path(tmp), key="not-secret"
                )
            replay_atoms, replay_scene = aerial_atoms(
                "site", SITE, False, cache_dir=Path(tmp)
            )
        self.assertEqual(scene["state"], "NOT_FOUND")
        self.assertEqual(atoms[0].failure["class"], "no_coverage")
        self.assertEqual(atoms[1].field_id, "maps_3d_scene")
        self.assertEqual(replay_scene["state"], "NOT_FOUND")
        self.assertEqual(replay_atoms[0].failure["http_status"], 404)

    def test_playback_uri_reads_nested_landscape(self):
        uri = playback_uri(
            {
                "uris": {
                    "MP4_HIGH": {
                        "landscapeUri": "https://example.test/high.mp4",
                        "portraitUri": "https://example.test/high-portrait.mp4",
                    }
                }
            }
        )
        self.assertEqual(uri, "https://example.test/high.mp4")
        self.assertIsNone(playback_uri({"uris": {"IMAGE": {"landscapeUri": "https://example.test/thumb.jpg"}}}))


if __name__ == "__main__":
    unittest.main()
