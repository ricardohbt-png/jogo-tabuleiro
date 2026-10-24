"""Fatia 20 do tutorial: Sala das Reações de Terreno (gás + ilha de água, piche + fogo).
Roda da raiz: python -X utf8 tools/test_tutorial_fatia20.py
Spec: docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md"""
import copy
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S  # noqa: E402
import aplicar_fatia20_tutorial as F20  # noqa: E402
import gerar_guia_comum as G  # noqa: E402

CAMINHO = os.path.join(RAIZ, "dungeons", "campo_de_treinamento.json")
with open(CAMINHO, encoding="utf-8") as f:
    ATUAL = json.load(f)


def aplicado():
    """O que o `main()` grava: a fatia 20 + o guia gerado (como em aplicar_fatia13)."""
    d = copy.deepcopy(ATUAL)
    F20.aplicar(d)
    G.aplicar_guia(d)
    return d


def sala(d, ident):
    return next(r for r in d["rooms"] if r["id"] == ident)


def fala(d, ident):
    return next(f for f in d["falas"] if f["id"] == ident)


class MapaTests(unittest.TestCase):
    def test_grid_e_tiles(self):
        d = aplicado()
        self.assertEqual(d["grid"], {"w": 57, "h": 40})
        self.assertEqual(len(d["tiles"]), 40)
        self.assertTrue(all(len(row) == 57 for row in d["tiles"]))
        self.assertTrue(all(c == S.WALL for c in d["tiles"][39]))
        self.assertEqual(d["tiles"][32][51], S.DOOR)
        for y in range(33, 39):
            self.assertTrue(all(d["tiles"][y][x] == S.FLOOR for x in range(48, 54)), y)

    def test_salas(self):
        d = aplicado()
        s49, s51 = sala(d, 49), sala(d, 51)
        self.assertEqual((s49["x"], s49["y"], s49["w"], s49["h"]), (48, 26, 6, 6))
        self.assertEqual(s49["doors"], [[51, 25], [51, 32]])
        self.assertEqual((s51["x"], s51["y"], s51["w"], s51["h"]), (48, 33, 6, 6))
        self.assertTrue(s49["locked"] and s51["locked"])
        self.assertEqual(s51["doors"], [[51, 32], [47, 35]])

    def test_saida_e_porta(self):
        d = aplicado()
        self.assertEqual(d["exit"], {"x": 36, "y": 36})
        self.assertEqual(d["door_conditions"]["51,32"], {"type": "gas", "zona_id": "gas_tutorial"})

    def test_lago_bau_e_boneco(self):
        d = aplicado()
        for y in (28, 29):
            for x in (50, 51, 52):
                self.assertEqual(d["materiais"].get(f"{x},{y}"), "agua", (x, y))
        gas = next(c for c in d["chests"] if c["pos"] == [51, 29])
        self.assertEqual([i["id"] for i in gas["items"]], ["frasco_oleo"] * 3)
        self.assertEqual(d["materiais"]["51,29"], "agua")
        bau2 = next(c for c in d["chests"] if sala(d, 51)["x"] <= c["pos"][0] < 54 and c["pos"][1] >= 33)
        self.assertEqual(sorted(i["id"] for i in bau2["items"]),
                         ["frasco_oleo", "frasco_oleo", "frasco_piche", "frasco_piche"])
        bonecos = [m for m in d["monsters"] if m.get("room_id") == 51]
        self.assertEqual([m["type"] for m in bonecos], ["boneco_treino"])
        bx, by = bonecos[0]["pos"]
        self.assertLessEqual(max(abs(bx - bau2["pos"][0]), abs(by - bau2["pos"][1])), 4)
        self.assertNotEqual([bx, by], [36, 36])

    def test_valida(self):
        ok, msg = S.validar_dungeon(aplicado())
        self.assertTrue(ok, msg)

    def test_idempotente(self):
        a = aplicado()
        b = copy.deepcopy(a)
        F20.aplicar(b)
        G.aplicar_guia(b)
        self.assertEqual(a, b)

    def test_arquivo_atual_ja_esta_aplicado(self):
        self.assertEqual(aplicado(), ATUAL, "rode: python tools/aplicar_fatia20_tutorial.py")

    def test_pipeline_da_missao_nao_desfaz(self):
        import aplicar_tutorial_missao as Missao
        d = aplicado()
        Missao.aplicar(d)
        G.aplicar_guia(d)

        def sem_ruido(m):
            # O editor grava `tarefa.alvo: null` e gatilho de sala sem `raio`; o pipeline não escreve esses
            # campos. Nenhum dos dois muda o jogo, então não contam como "desfazer" o trabalho do autor.
            m = copy.deepcopy(m)
            for f in m["falas"]:
                if isinstance(f.get("tarefa"), dict) and f["tarefa"].get("alvo") is None:
                    f["tarefa"].pop("alvo", None)
                if isinstance(f.get("trigger"), dict) and f["trigger"].get("tipo") == "sala":
                    f["trigger"].pop("raio", None)
            return m
        self.assertEqual(sem_ruido(d), sem_ruido(aplicado()))


class LicoesTests(unittest.TestCase):
    def test_ordens_e_tarefas(self):
        d = aplicado()
        gas, piche, retirada = fala(d, "fala_gas"), fala(d, "fala_piche"), fala(d, "fala_retirada")
        gargula = fala(d, "fala_gargula")
        self.assertEqual((gas["ordem"], piche["ordem"], gargula["ordem"], retirada["ordem"]), (36, 37, 38, 39))
        self.assertEqual(gargula["tarefa"]["tipo"], "desativar_armadilha")
        self.assertEqual(gargula["tarefa"]["alvo"], "decor_133")
        self.assertEqual(gas["tarefa"]["tipo"], "explodir_gas")
        self.assertEqual(gas["tarefa"]["alvo"], "gas_tutorial")
        self.assertEqual(piche["tarefa"]["tipo"], "incendiar_piche")
        self.assertEqual(retirada["pos"], [36, 36])
        self.assertEqual(retirada["tarefa"]["alvo"], [36, 36])
        self.assertIn("fala_piche", retirada["continua_sem"])
        self.assertIn("fala_gargula", retirada["continua_sem"])
        ordens = [f["ordem"] for f in d["falas"] if isinstance(f.get("ordem"), int) and 35 <= f["ordem"] <= 39]
        self.assertEqual(sorted(ordens), [35, 36, 37, 38, 39])

    def test_guia_com_chaves_de_idioma(self):
        d = aplicado()
        lang = G.gerar_lang()
        for lid in ("fala_gas", "fala_piche", "fala_gargula", "fala_retirada"):
            passos = fala(d, lid)["guia"]
            self.assertTrue(passos, lid)
            for p in passos:
                for campo in ("texto", "porque"):
                    if p.get(campo):
                        self.assertIn(p[campo], lang, (lid, p["id"], campo))
                        self.assertTrue(lang[p[campo]]["pt"] and lang[p[campo]]["en"])
        # regra de ouro: nada de conclui_com em evento que o herói pode ter feito antes
        for lid in ("fala_gas", "fala_piche"):
            self.assertFalse([p for p in fala(d, lid)["guia"] if p.get("conclui_com")], lid)
        self.assertIn("ui.tutorial.glossario.inflamavel.nome", lang)
        self.assertIn("ui.tutorial.glossario.reacao.nome", lang)
        self.assertEqual(fala(d, "fala_retirada")["guia"][0]["ui"], "casa:[36,36]")


if __name__ == "__main__":
    unittest.main()
