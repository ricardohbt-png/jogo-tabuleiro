"""Fichas da rota do Olho. Roda da raiz: python -X utf8 tools/test_elara_montanha_fichas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_montanha_fichas as F


class FichasTests(unittest.TestCase):
    def test_validam_e_tem_o_cr(self):
        ok, norm = S._validate_custom_monster(F.ficha_assassino())
        self.assertTrue(ok, norm)
        self.assertEqual(S.monster_cr(norm), 3)

    def test_bardo_da_caravana_e_um_bardo_mais_forte(self):
        """É variante nativa do Bardo: mesma IA e habilidades, mas mais vida, ataque, defesa e recarga menor."""
        defs = [m for m in S.MONSTER_DEFS if m["type"] == F.TIPO_BARDO]
        self.assertEqual(len(defs), 1, "uma só ficha (a personalizada antiga não pode coexistir)")
        v, base = defs[0], next(m for m in S.MONSTER_DEFS if m["type"] == "bardo")
        self.assertEqual((v["ai_type"], S.monster_cr(v)), ("bardo", 2))
        self.assertEqual([a["id"] for a in v["special_abilities"]], [a["id"] for a in base["special_abilities"]])
        self.assertGreater(v["hp"], base["hp"] * 2)
        self.assertGreater(v["attacks"][0]["atk_bonus"], base["attacks"][0]["atk_bonus"])
        self.assertGreater(v["bardo_cd_provocacao"], 11)
        self.assertLess(v["bardo_recarga"], 4)
        sala = {"cx": 5, "cy": 5, "x": 3, "y": 3, "w": 5, "h": 5, "id": "r0"}
        for _ in range(60):
            m = S.make_monster(v, sala)
            self.assertIn(m["bardo_instrumento"]["qualidade"], ("padrao", "refinado"))
            self.assertEqual(m["equipped_items"][0], "leather_plate")
            self.assertEqual(m["attacks"][0]["atk_bonus"], 6)
        outro = S.make_monster(base, sala)
        self.assertEqual(outro["attacks"][0]["atk_bonus"], 3, "o Bardo original não mudou")

    def test_ia_do_bardo_joga_varios_turnos_sem_erro(self):
        """A variante usa a IA do Bardo (Provocação, instrumento). O Cajado de Madeira (`reach` em texto) já
        derrubava a IA do Bardo original: cobre os dois."""
        import asyncio
        import random

        async def nada(*a, **k):
            pass

        def joga(tipo, arma=None):
            r = S.GameRoom("T")
            r.players["p0"] = S.make_player("p0", "Heroi", "warrior", 0)
            r.host_pid = "p0"
            r.load_authored_dungeon(S.carregar_dungeon("elara_montanha_3.json"))
            r.phase = "playing"
            r.send_to = nada; r.broadcast = nada; r.push_state = nada; r.gm_say = nada
            r.monsters.clear()
            d = next(m for m in S.MONSTER_DEFS if m["type"] == tipo)
            m = S.make_monster(d, {"cx": 10, "cy": 10, "x": 8, "y": 8, "w": 5, "h": 5, "id": "r0"})
            if arma:
                m["equipped_items"] = ["cloak", arma]
                S._aplicar_equipamentos_monstro(m)
                m["bardo_arma"] = arma
            r.monsters[m["id"]] = m
            m["alertado"] = True
            heroi = r.players["p0"]
            heroi["pos"] = [m["pos"][0] + 2, m["pos"][1]]

            async def turnos():
                for n in range(6):
                    r.round_num = n + 1
                    cds = m.setdefault("monster_ability_cooldowns", {})
                    for k in list(cds):
                        cds[k] = max(0, cds[k] - 1)
                    await r._ai_bardo(m, [{"kind": "player", "obj": heroi, "id": "p0"}])
            asyncio.run(turnos())
            return m

        random.seed(7)
        for _ in range(15):
            joga(F.TIPO_BARDO)
        joga("bardo", "cajado_madeira")

    def test_assassino_e_chefe(self):
        ok, n = S._validate_custom_monster(F.ficha_assassino())
        self.assertTrue(n["boss"])

    def test_nada_da_rede_por_nome(self):
        bardo = next(m for m in S.MONSTER_DEFS if m["type"] == F.TIPO_BARDO)
        t = json.dumps([F.ficha_assassino(), bardo], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
