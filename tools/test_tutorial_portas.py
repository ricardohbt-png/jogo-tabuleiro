"""Placas e guia até a sala exclusiva de cada herói no Campo de Treinamento."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import server as S
import gerar_guia_comum as G
from test_tutorial_salas import room, D

CLASSES = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")
ULTIMA_COMUM = {"warrior": "fala_6", "mage": "fala_8", "rogue": "fala_10",
                "cleric": "fala_12", "bard": "fala_14", "paladin": "fala_16"}


def sala_de(cls):
    return next(r for r in D["rooms"] if r.get("allowed_class") == cls)


def porta_de(cls):
    return tuple(sala_de(cls)["doors"][0])


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class PlacasTests(unittest.TestCase):
    def test_mapa_valido(self):
        self.assertEqual(S.validar_dungeon(D), (True, "ok"))

    def test_uma_placa_por_classe_junto_da_porta_certa(self):
        placas = [d for d in D["decorations"] if d["type"] == "placa"]
        self.assertEqual(len(placas), len(CLASSES))
        usadas = set()
        for cls in CLASSES:
            porta = porta_de(cls)
            sala = sala_de(cls)
            minhas = [p for p in placas if cheb(p["pos"], porta) <= 2]
            # a placa mais perto desta porta é desta classe: nenhuma outra porta está mais perto
            self.assertEqual(len(minhas), 1, cls)
            p = minhas[0]
            self.assertNotIn(p["id"], usadas); usadas.add(p["id"])
            for outra in CLASSES:
                if outra != cls:
                    self.assertGreater(cheb(p["pos"], porta_de(outra)), cheb(p["pos"], porta), (cls, outra))
            x, y = p["pos"]
            self.assertEqual(D["tiles"][y][x], 1, "placa em chão")
            self.assertNotEqual(tuple(p["pos"]), porta)
            dentro = sala["x"] <= x < sala["x"] + sala["w"] and sala["y"] <= y < sala["y"] + sala["h"]
            self.assertFalse(dentro, "placa fica do lado de fora da sala")
            self.assertTrue(p["texto"].strip() and len(p["texto"]) <= 600)

    def test_casa_da_placa_esta_livre(self):
        placas = [tuple(d["pos"]) for d in D["decorations"] if d["type"] == "placa"]
        ocupadas = set()
        for chave in ("monsters", "chests", "traps", "hero_spawns"):
            ocupadas |= {tuple(e["pos"]) for e in D[chave]}
        ocupadas |= {tuple(f["pos"]) for f in D["falas"]}
        self.assertFalse(set(placas) & ocupadas)
        self.assertEqual(len(set(placas)), len(placas))


class PonteTests(unittest.IsolatedAsyncioTestCase):
    def test_licao_ponte_por_classe(self):
        falas = {f["id"]: f for f in D["falas"]}
        guia = G.guia_todos()
        for cls in CLASSES:
            f = falas[f"porta_{cls}"]
            ant = falas[ULTIMA_COMUM[cls]]
            self.assertEqual(f["classe"], cls)
            self.assertEqual(f["ordem"], ant["ordem"] + 1)
            self.assertEqual(f["tarefa"]["tipo"], "mover_ate")
            self.assertEqual(tuple(f["tarefa"]["alvo"]), porta_de(cls))
            # a primeira lição exclusiva vem depois da ponte
            excl = [x for x in D["falas"] if x.get("classe") == cls and x.get("sala_exclusiva")]
            self.assertTrue(all(x["ordem"] > f["ordem"] for x in excl), cls)
            passos = guia[f"porta_{cls}"]
            self.assertEqual(passos[-1]["ui"], "porta:" + json.dumps(list(porta_de(cls))).replace(" ", ""))

    async def test_fluxo_matar_ponte_sala(self):
        for cls in CLASSES:
            r, p = room(cls)
            ant = next(f for f in r.licoes if f["id"] == ULTIMA_COMUM[cls])
            feitas = [f["id"] for f in r.licoes if f.get("classe") == cls and f["ordem"] < ant["ordem"]]
            p["licoes_feitas"] = list(feitas)
            p["licao_progresso"] = {i: 1 for i in feitas}
            p["licao_atual"] = None
            p["pos"] = list(ant["pos"])
            await r._verificar_falas(p, r._room_containing_point(p["pos"]))
            self.assertEqual(p["licao_atual"], ant["id"])
            await r._licao_evento(p, "matar", alvo="boneco_treino")
            self.assertEqual(p["licao_atual"], f"porta_{cls}", cls)
            # andar numa casa qualquer não conclui; a porta conclui
            await r._licao_evento(p, "mover_ate", alvo=[1, 1])
            self.assertEqual(p["licao_atual"], f"porta_{cls}")
            await r._licao_evento(p, "mover_ate", alvo=list(porta_de(cls)))
            self.assertIn(f"porta_{cls}", p["licoes_feitas"])
            self.assertIsNone(p["licao_atual"])
            # entrar na sala própria dispara a primeira lição exclusiva
            sala = sala_de(cls)
            p["pos"] = [sala["x"] + 1, sala["y"] + 2]
            await r._verificar_falas(p, r._room_containing_point(p["pos"]))
            atual = next((x for x in r.licoes if x["id"] == p["licao_atual"]), None)
            self.assertIsNotNone(atual, cls)
            self.assertTrue(atual.get("sala_exclusiva"), cls)



if __name__ == "__main__":
    unittest.main()
