import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CabanaPalhaVelhaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT))
        import server
        cls.server = server

    def test_authoritative_catalog_registers_solid_rotatable_three_by_three_hut(self):
        decor = self.server.DECOR_TYPES.get("cabana_palha_velha")
        self.assertIsNotNone(decor)
        self.assertEqual(decor["nome"], "Cabana de palha velha")
        self.assertEqual(decor["size"], [3, 3])
        self.assertTrue(decor["gira"])
        self.assertTrue(decor["alto"])
        self.assertFalse(decor["pisavel"])
        self.assertFalse(decor["loot_capaz"])
        self.assertEqual(decor["image"], "cabana_palha_velha.png")

    def test_runtime_maps_image_and_type_to_model(self):
        self.assertEqual(
            self.server.DECOR_MODEL3D.get("cabana_palha_velha"),
            "assets/objetos/cabana_palha_velha.glb",
        )
        game = (ROOT / "game.js").read_text(encoding="utf-8")
        expected = "assets/objetos/cabana_palha_velha.glb"
        self.assertIn(f"cabana_palha_velha: '{expected}'", game)
        self.assertIn(f"'cabana_palha_velha.png': '{expected}'", game)

    def test_editor_catalog_and_localized_name_include_hut(self):
        raw = (ROOT / "tools/editor_catalog.js").read_text(encoding="utf-8")
        match = re.search(r"window\.EDITOR_CATALOG\s*=\s*(\{.*?\})\s*;", raw, re.S)
        self.assertIsNotNone(match)
        catalog = json.loads(match.group(1))
        decor = next((d for d in catalog["decorations"]
                      if d["type"] == "cabana_palha_velha"), None)
        self.assertIsNotNone(decor)
        self.assertEqual(decor["size"], [3, 3])
        self.assertEqual(decor["image"], "cabana_palha_velha.png")
        lang = (ROOT / "src/lang/catalogo.js").read_text(encoding="utf-8")
        self.assertIn('"cat.decor.cabana_palha_velha.nome"', lang)

    def test_png_and_glb_assets_are_valid_and_match_footprint(self):
        png_path = ROOT / "assets/objetos/cabana_palha_velha.png"
        glb_path = ROOT / "assets/objetos/cabana_palha_velha.glb"
        blend_path = ROOT / "assets/objetos/cabana_palha_velha.blend"
        self.assertTrue(png_path.is_file())
        self.assertTrue(glb_path.is_file())
        self.assertTrue(blend_path.is_file())
        with glb_path.open("rb") as stream:
            magic, version, total_length = struct.unpack("<4sII", stream.read(12))
        self.assertEqual((magic, version, total_length),
                         (b"glTF", 2, glb_path.stat().st_size))
        import trimesh
        model = trimesh.load(glb_path, force="scene")
        mesh_names = " ".join(model.geometry.keys()).casefold()
        self.assertIn("parede circular de palha", mesh_names)
        self.assertIn("telhado conico de palha", mesh_names)
        extents = model.extents
        self.assertLessEqual(extents[0], 3.05)
        self.assertLessEqual(extents[2], 3.05)
        self.assertGreater(extents[1], 3.0)
        from PIL import Image
        with Image.open(png_path) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.getchannel("A").getextrema(), (0, 255))


if __name__ == "__main__":
    unittest.main(verbosity=2)
