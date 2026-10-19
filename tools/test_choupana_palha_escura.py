import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ChoupanaPalhaEscuraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT))
        import server
        cls.server = server

    def test_editor_catalog_registers_solid_rotatable_three_by_three_hut(self):
        decor = self.server.DECOR_TYPES.get("choupana_palha_escura")
        self.assertIsNotNone(decor, "o tipo precisa existir no catálogo autoritativo")
        self.assertEqual(decor["nome"], "Choupana de palha escura")
        self.assertEqual(decor["size"], [3, 3])
        self.assertTrue(decor["gira"])
        self.assertTrue(decor["alto"])
        self.assertFalse(decor["pisavel"])
        self.assertFalse(decor["loot_capaz"])
        self.assertEqual(decor["image"], "choupana_palha_escura.png")

    def test_runtime_maps_png_and_type_to_glb(self):
        self.assertEqual(
            self.server.DECOR_MODEL3D.get("choupana_palha_escura"),
            "assets/objetos/choupana_palha_escura.glb",
        )
        game = (ROOT / "game.js").read_text(encoding="utf-8")
        self.assertIn("choupana_palha_escura: 'assets/objetos/choupana_palha_escura.glb'", game)
        self.assertIn("'choupana_palha_escura.png': 'assets/objetos/choupana_palha_escura.glb'", game)

    def test_editor_catalog_and_assets_are_published(self):
        raw = (ROOT / "tools/editor_catalog.js").read_text(encoding="utf-8")
        match = re.search(r"window\.EDITOR_CATALOG\s*=\s*(\{.*?\})\s*;", raw, re.S)
        self.assertIsNotNone(match)
        catalog = json.loads(match.group(1))
        decor = next((d for d in catalog["decorations"]
                      if d["type"] == "choupana_palha_escura"), None)
        self.assertIsNotNone(decor, "a decoração precisa chegar ao catálogo do editor")
        self.assertEqual(decor["size"], [3, 3])
        self.assertEqual(decor["image"], "choupana_palha_escura.png")
        self.assertTrue((ROOT / "assets/objetos/choupana_palha_escura.png").is_file())
        glb_path = ROOT / "assets/objetos/choupana_palha_escura.glb"
        self.assertTrue(glb_path.is_file())
        self.assertTrue((ROOT / "assets/objetos/choupana_palha_escura.blend").is_file())
        import struct
        with glb_path.open("rb") as stream:
            magic, version, total_length = struct.unpack("<4sII", stream.read(12))
        self.assertEqual((magic, version, total_length),
                         (b"glTF", 2, glb_path.stat().st_size))
        import trimesh
        model = trimesh.load(glb_path, force="scene")
        extents = model.extents
        self.assertLessEqual(extents[0], 3.05)
        self.assertLessEqual(extents[2], 3.05)
        self.assertGreater(extents[1], 3.0)
        from PIL import Image
        with Image.open(ROOT / "assets/objetos/choupana_palha_escura.png") as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.getchannel("A").getextrema(), (0, 255))


if __name__ == "__main__":
    unittest.main(verbosity=2)
