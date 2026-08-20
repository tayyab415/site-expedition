import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

from expedition.adapters.aerial import (
    aerial_atoms,
    ensure_aerial,
    playback_uri,
    postal_address_from_nominatim,
    public_aerial,
    render_video,
    reverse_address,
)


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

    def test_public_aerial_keeps_processing_video_id_and_strips_uris(self):
        record = public_aerial(
            {
                "state": "PROCESSING",
                "metadata": {"videoId": "abc123"},
                "uris": {"MP4_HIGH": "https://secret.example/playback"},
            },
            "3605 Winfield Cove, Austin, TX",
        )
        self.assertEqual(record["state"], "PROCESSING")
        self.assertEqual(record["video_id"], "abc123")
        self.assertEqual(record["query"], "3605 Winfield Cove, Austin, TX")
        self.assertNotIn("uris", record)
        self.assertNotIn("secret", json.dumps(record))

    def test_public_aerial_reads_top_level_active_video_id(self):
        record = public_aerial(
            {"state": "ACTIVE", "videoId": "KPvJfAwQnLollCjP2bks-y", "duration": "40s"},
            "5801 S Ellis Ave, Chicago, IL 60637",
        )
        self.assertEqual(record["state"], "ACTIVE")
        self.assertEqual(record["video_id"], "KPvJfAwQnLollCjP2bks-y")
        self.assertEqual(record["duration"], "40s")

    def test_render_video_posts_address_and_returns_metadata(self):
        class Fake:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {"state": "PROCESSING", "metadata": {"videoId": "new-id"}}
                ).encode()

        with patch(
            "expedition.adapters.aerial.urllib.request.urlopen",
            return_value=Fake(),
        ) as opener:
            result = render_video("500 W 2nd St, Austin, TX 78701", "not-secret")
        self.assertEqual(result["state"], "PROCESSING")
        self.assertEqual(result["metadata"]["videoId"], "new-id")
        request = opener.call_args[0][0]
        self.assertIn("videos:renderVideo", request.full_url)
        self.assertIn("key=not-secret", request.full_url)
        self.assertEqual(
            json.loads(request.data.decode()),
            {"address": "500 W 2nd St, Austin, TX 78701"},
        )

    def test_reverse_address_builds_a_us_postal_line(self):
        class Fake:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {
                        "address": {
                            "house_number": "350",
                            "road": "5th Avenue",
                            "city": "New York",
                            "state": "New York",
                            "postcode": "10118",
                        }
                    }
                ).encode()

        with patch("expedition.adapters.aerial.urllib.request.urlopen", return_value=Fake()):
            self.assertEqual(
                reverse_address(40.748, -73.985),
                "350 5th Avenue, New York, New York, 10118",
            )

    def test_postal_address_requires_a_house_number(self):
        self.assertIsNone(
            postal_address_from_nominatim(
                {
                    "address": {
                        "road": "Avenue Q",
                        "city": "Texas City",
                        "state": "Texas",
                        "postcode": "77539",
                    }
                }
            )
        )

    def test_ensure_aerial_does_not_render_an_imprecise_pin(self):
        with patch("expedition.adapters.aerial.reverse_address", return_value=None):
            with patch("expedition.adapters.aerial.render_video") as render:
                record = ensure_aerial(
                    lat=29.475732, lng=-94.966533, render=True, key="not-secret"
                )
        self.assertEqual(record["state"], "NO_ADDRESS")
        render.assert_not_called()

    def test_ensure_aerial_reverse_geocodes_a_pin_with_no_address(self):
        with patch(
            "expedition.adapters.aerial.reverse_address",
            return_value="350 5th Avenue, New York, New York, 10118",
        ):
            with patch(
                "expedition.adapters.aerial.lookup_metadata",
                return_value={"state": "ACTIVE", "videoId": "midtown-id"},
            ) as lookup:
                record = ensure_aerial(lat=40.748, lng=-73.985, key="not-secret")
        self.assertEqual(record["state"], "ACTIVE")
        self.assertEqual(record["video_id"], "midtown-id")
        self.assertEqual(record["query"], "350 5th Avenue, New York, New York, 10118")
        lookup.assert_called_once_with("350 5th Avenue, New York, New York, 10118", "not-secret")

    def test_ensure_aerial_does_not_render_when_already_active(self):
        with patch(
            "expedition.adapters.aerial.lookup_metadata",
            return_value={"state": "ACTIVE", "videoId": "already"},
        ):
            with patch("expedition.adapters.aerial.render_video") as render:
                record = ensure_aerial(
                    address="350 5th Avenue, New York, NY 10118",
                    render=True,
                    key="not-secret",
                )
        self.assertEqual(record["video_id"], "already")
        render.assert_not_called()

    def test_ensure_aerial_renders_after_a_404(self):
        error = urllib.error.HTTPError("url", 404, "not found", {}, None)
        with patch("expedition.adapters.aerial.lookup_metadata", side_effect=error):
            with patch(
                "expedition.adapters.aerial.render_video",
                return_value={"state": "PROCESSING", "metadata": {"videoId": "queued"}},
            ):
                record = ensure_aerial(
                    address="3605 Winfield Cove, Austin, TX",
                    render=True,
                    key="not-secret",
                )
        self.assertEqual(record["state"], "PROCESSING")
        self.assertEqual(record["video_id"], "queued")


if __name__ == "__main__":
    unittest.main()
