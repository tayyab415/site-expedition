import base64
import json
import struct
import unittest

from expedition.concept import ASSET, load_footprint, place, run_concept_test


class ConceptTest(unittest.TestCase):
    def test_three_cases_without_google(self):
        out = run_concept_test()
        self.assertFalse(out["google_tiles_used"])
        self.assertFalse(out["parcel_fields_used"])
        self.assertTrue(out["pass"], out)
        self.assertEqual(out["claim"]["FUTURE"], "visual_concept")
        self.assertEqual(out["claim"]["FIT"], "deferred")

    def test_heading_can_create_conflict(self):
        foot = load_footprint()
        square = {"width_m": 90, "length_m": 90, "quality": "ok"}
        aligned = place(foot, square, heading_deg=0, setback_m=5)
        self.assertEqual(aligned["result"], "fit")
        rotated = place(foot, square, heading_deg=45, setback_m=5)
        self.assertEqual(rotated["result"], "conflict")

    def test_visual_asset_has_valid_buffer_views_and_indices(self):
        gltf = json.loads(ASSET.read_text())
        encoded = gltf["buffers"][0]["uri"].split(",", 1)[1]
        payload = base64.b64decode(encoded)
        self.assertEqual(gltf["buffers"][0]["byteLength"], len(payload))
        for view in gltf["bufferViews"]:
            start = view.get("byteOffset", 0)
            self.assertLessEqual(start + view["byteLength"], len(payload))

        position_accessor = gltf["accessors"][0]
        index_accessor = gltf["accessors"][2]
        index_view = gltf["bufferViews"][index_accessor["bufferView"]]
        self.assertEqual(34963, index_view["target"])
        start = index_view.get("byteOffset", 0) + index_accessor.get("byteOffset", 0)
        end = start + index_accessor["count"] * 2
        indices = struct.unpack(
            f"<{index_accessor['count']}H", payload[start:end]
        )
        self.assertLess(max(indices), position_accessor["count"])
