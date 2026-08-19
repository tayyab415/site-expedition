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
        self.assertEqual(out["claim"]["INTERIOR"], "schematic_program")
        self.assertGreaterEqual(len(out["presets"]), 10)
        self.assertTrue(all(row.get("cad") for row in out["presets"]))

    def test_presets_are_mission_scoped_and_keep_warehouse_footprint(self):
        from expedition.concept import list_presets, load_preset

        warehouse = load_preset(mission="warehouse")
        self.assertEqual(80, warehouse["length_m"])
        self.assertEqual(40, warehouse["width_m"])
        self.assertTrue(warehouse["interior"])
        farm = load_preset(mission="farm")
        self.assertEqual("farm-packing", farm["id"])
        self.assertEqual("farm", farm["mission"])
        self.assertEqual("packing_shed", farm["cad"]["studio_id"])
        self.assertGreaterEqual(len(list_presets(mission="warehouse")), 8)
        self.assertEqual(
            {"warehouse", "farm", "home", "data_center"},
            {row["mission"] for row in list_presets()},
        )

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

    def test_conceptual_cad_is_labeled_not_for_permit(self):
        from expedition.studio import dxf_bytes, ifc_bytes, list_presets

        studio = {row["id"] for row in list_presets()}
        self.assertGreaterEqual(len(studio), 10)
        dxf = dxf_bytes("cross_dock").decode()
        ifc = ifc_bytes("cross_dock").decode()
        self.assertIn("NOT FOR PERMIT", dxf)
        self.assertIn("CONCEPTUAL NOT FOR PERMIT", ifc)
        self.assertIn("PermitReady", ifc)
        self.assertIn(".F.", ifc)
        home = dxf_bytes("home_massing").decode()
        self.assertIn("NOT FOR PERMIT", home)
