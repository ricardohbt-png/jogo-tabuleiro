"""Regressões para a transformação do Lobo Cinzento customizado em Alfa."""
import asyncio
import json
import struct
import unittest
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S


def definicao(tipo):
    return next((m for m in S.MONSTER_DEFS if m.get("type") == tipo), None)


def sala_teste():
    r = S.GameRoom("TEST")
    async def noop(*_a, **_k):
        pass
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.monsters = {}
    return r


class LoboAlfaFicha(unittest.TestCase):
    def test_customizado_preserva_id_e_vira_alfa_nd2(self):
        m = definicao("lobo_cinzento_customizado")
        self.assertIsNotNone(m)
        self.assertEqual((m["name"], m["cr"], m["hp"], m["ac"], m["movement"]),
                         ("Lobo Alfa", 2, 30, 14, 8))
        self.assertEqual(m["image"], "lobo_alfa")
        self.assertEqual(m["ai_type"], "lobo_cinzento")
        self.assertEqual([(a["atk_bonus"], a["damage"]) for a in m["attacks"]],
                         [(5, "1d8+3")])
        derrubar = next(a for a in m["special_abilities"] if a["id"] == "derrubar")
        self.assertEqual(derrubar["dc"], 15)

    def test_rotulo_no_catalogo_do_editor_e_lobo_alfa(self):
        catalog = (ROOT / "src/lang/catalogo.js").read_text(encoding="utf-8")
        inicio = catalog.index("{", catalog.index("window.LANG_CATALOGO"))
        fim = catalog.rindex("};")
        traducoes = json.loads(catalog[inicio:fim + 1])
        self.assertEqual(traducoes["cat.monstro.lobo_cinzento_customizado.nome"],
                         {"en": "Alpha Wolf", "pt": "Lobo Alfa"})

    def test_aura_sobe_cd_dos_outros_lobos_sem_acumular(self):
        r = sala_teste()
        target = {"hp": 12, "moves_left": 6}
        cds = []
        r._testar_save = lambda alvo, atributo, dc, fonte=None: (cds.append(dc) or True, 10, 2, 12)
        def wolf(monster_id, tipo, cd=11, hp=10):
            return {"id": monster_id, "type": tipo, "hp": hp, "pos": [1, 1],
                    "special_abilities": [{"id": "derrubar", "dc": cd}]}
        normal = wolf("wolf", "lobo_cinzento")
        r.monsters = {"wolf": normal,
                      "alpha1": wolf("alpha1", "lobo_cinzento_customizado", 15),
                      "alpha2": wolf("alpha2", "lobo_cinzento_customizado", 15)}
        asyncio.run(r._lobo_derrubar(normal, {"kind": "player", "obj": target}, True))
        self.assertEqual(cds, [13])

    def test_aura_so_afeta_outro_lobo_vivo_na_sala(self):
        r = sala_teste()
        target = {"hp": 12, "moves_left": 6}
        cds = []
        r._testar_save = lambda alvo, atributo, dc, fonte=None: (cds.append(dc) or True, 10, 2, 12)
        wolf = {"id": "wolf", "type": "lobo_cinzento", "hp": 10,
                "special_abilities": [{"id": "derrubar", "dc": 11}]}
        dead_alpha = {"id": "alpha", "type": "lobo_cinzento_customizado", "hp": 0}
        r.monsters = {"wolf": wolf, "alpha": dead_alpha}
        asyncio.run(r._lobo_derrubar(wolf, {"kind": "player", "obj": target}, True))
        self.assertEqual(cds, [11])

    def test_alpha_mantem_cd15_mesmo_com_outro_alpha(self):
        r = sala_teste()
        target = {"hp": 12, "moves_left": 6}
        cds = []
        r._testar_save = lambda alvo, atributo, dc, fonte=None: (cds.append(dc) or True, 10, 2, 12)
        alpha = {"id": "alpha1", "type": "lobo_cinzento_customizado", "hp": 30,
                 "special_abilities": [{"id": "derrubar", "dc": 15}]}
        other_alpha = {"id": "alpha2", "type": "lobo_cinzento_customizado", "hp": 30}
        r.monsters = {"alpha1": alpha, "alpha2": other_alpha}
        asyncio.run(r._lobo_derrubar(alpha, {"kind": "player", "obj": target}, True))
        self.assertEqual(cds, [15])

    def test_miniatura_tem_png_glb_e_mapeamento(self):
        png = ROOT / "assets/pawns/monstros/lobo_alfa/lobo_alfa.png"
        glb = ROOT / "assets/models3d/monstros/lobo_alfa.glb"
        self.assertTrue(png.is_file())
        self.assertTrue(glb.is_file())
        pixels = np.asarray(Image.open(png).convert("RGB"))[:360]
        self.assertTrue(np.any(pixels.mean(axis=2) < 45), "faltam áreas de pelo preto")
        self.assertTrue(np.any(pixels.mean(axis=2) > 165), "faltam áreas de pelo branco")

        def glb_doc(path):
            raw = path.read_bytes()
            self.assertEqual(raw[:4], b"glTF")
            offset = 12
            while offset < len(raw):
                size, kind = struct.unpack_from("<I4s", raw, offset)
                body = raw[offset + 8:offset + 8 + size]
                if kind == b"JSON":
                    return json.loads(body.decode("utf-8").rstrip(" \0"))
                offset += 8 + size
            self.fail("falta bloco JSON no GLB")

        original = glb_doc(ROOT / "assets/models3d/monstros/lobo.glb")
        recolored = glb_doc(glb)
        self.assertEqual(original["meshes"], recolored["meshes"], "a geometria do lobo mudou")
        self.assertEqual(original["nodes"], recolored["nodes"], "a montagem do modelo mudou")
        game = (ROOT / "game.js").read_text(encoding="utf-8")
        self.assertIn("lobo_alfa:", game)
        custom_js = (ROOT / "tools/editor_monsters_custom.js").read_text(encoding="utf-8")
        self.assertIn('"name": "Lobo Alfa"', custom_js)


if __name__ == "__main__":
    unittest.main(verbosity=2)
