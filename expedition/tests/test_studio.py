import json
import unittest

from expedition.concept import load_preset
from expedition.studio import dxf_bytes, gltf_bytes, ifc_bytes, list_presets


class ConceptStudioCadTests(unittest.TestCase):
    def test_generated_cad_is_conceptual_not_permit_ready(self):
        dxf = dxf_bytes("cross_dock").decode()
        ifc = ifc_bytes("cross_dock").decode()
        self.assertIn("NOT FOR PERMIT", dxf)
        self.assertIn("Not stamped", dxf)
        self.assertIn("Not for permit", ifc)
        self.assertIn("Not permit-ready", ifc)

    def test_interior_gltf_has_more_geometry_than_shell(self):
        shell = json.loads(gltf_bytes("cross_dock", interiors=False))
        interior = json.loads(gltf_bytes("cross_dock", interiors=True))
        self.assertGreater(
            interior["accessors"][0]["count"],
            shell["accessors"][0]["count"],
        )
        self.assertEqual("original parametric concept, CC0", shell["extras"]["rights"])
        self.assertTrue(interior["extras"]["interiors"])

    def test_warehouse_preset_exposes_cad_claim(self):
        preset = load_preset(mission="warehouse")
        self.assertEqual("conceptual_not_permit_ready", preset["cad"]["claim"])
        self.assertTrue(preset["interior"])
        self.assertGreaterEqual(len(list_presets()), 8)
