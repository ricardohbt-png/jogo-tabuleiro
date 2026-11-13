"""IA do bardo inimigo: escolha do alvo da Provocação e recuo do atirador.
Roda da raiz: python -X utf8 tools/test_bardo_ia.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def distancia(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def montar(arma="besta"):
    """Bardo da Caravana sozinho num mapa aberto, com a Canção e o instrumento fora de jogo."""
    r = S.GameRoom("BARDO")
    for i, classe in enumerate(("warrior", "mage", "cleric")):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", classe, i)
    r.host_pid = "p0"; r.phase = "playing"

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state_or_city = nada; r.push_state = nada; r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    r.load_authored_dungeon(S.carregar_dungeon("elara_graciero_cais.json"))
    b = next(m for m in r.monsters.values() if m["type"] == "capanga")
    molde = next(m for m in S.MONSTER_DEFS if m["type"] == "bardo_da_caravana")
    sala = next(x for x in r.rooms if x["id"] == b["room_id"])
    novo = S.make_monster(molde, sala)
    novo["id"] = b["id"]
    r.monsters = {b["id"]: novo}
    b = novo
    b["pos"] = [8, 6]
    b["bardo_arma"] = arma
    b["bardo_instrumento"] = {}
    b["virotes"] = 20
    b["virotes_especiais_count"] = 0
    if arma == "besta":
        b["attacks"][0].update({"name": "Besta", "range": 8, "damage": "1d8"})
    b["_water_moves_left"] = b["movement"]
    b.setdefault("monster_ability_uses", {})["hero_bard_cancao_heroica"] = 0
    for i, p in enumerate(r.players.values()):
        p.update(hp=300, max_hp=300, alive=True, connected=True, pos=[1 + i, 28])
    ataques = []

    async def atacar(m, atk, alvo):
        ataques.append(alvo["obj"]["id"])
    r._execute_one_monster_attack = atacar
    return r, b, ataques


def alvos(r):
    """Como no jogo, a IA só recebe quem o bardo enxerga."""
    b = next(iter(r.monsters.values()))
    return [{"kind": "player", "obj": p} for p in r.players.values() if distancia(p["pos"], b["pos"]) <= 10]


class ProvocacaoTests(unittest.TestCase):
    def test_escolhe_quem_tem_menor_vontade(self):
        r, b, _ = montar()
        p0, p1, p2 = r.players.values()
        p0["pos"], p1["pos"], p2["pos"] = [10, 6], [8, 8], [6, 6]
        p0["will"], p1["will"], p2["will"] = 5, 0, 3
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(p1.get("bardo_provocado_por"), b["id"])
        self.assertIsNone(p0.get("bardo_provocado_por"))

    def test_em_empate_escolhe_o_mais_proximo(self):
        r, b, _ = montar()
        p0, p1, p2 = r.players.values()
        p0["pos"], p1["pos"], p2["pos"] = [11, 6], [9, 6], [1, 28]
        p0["will"] = p1["will"] = p2["will"] = 2
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(p1.get("bardo_provocado_por"), b["id"])

    def test_nao_repete_em_quem_ja_esta_provocado(self):
        r, b, _ = montar()
        p0, p1, p2 = r.players.values()
        p0["pos"], p1["pos"] = [10, 6], [11, 6]
        p0["will"], p1["will"] = 0, 9
        p0["bardo_provocado_por"] = b["id"]; p0["bardo_provocacao_turnos"] = 2
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(p0["bardo_provocacao_turnos"], 2)
        self.assertEqual(p1.get("bardo_provocado_por"), b["id"])

    def test_sem_candidato_nao_gasta_o_turno_e_ataca(self):
        r, b, ataques = montar()
        p0, p1, p2 = r.players.values()
        p0["pos"] = [11, 6]
        p0["bardo_provocado_por"] = b["id"]; p0["bardo_provocacao_turnos"] = 2
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(p0["bardo_provocacao_turnos"], 2)
        self.assertFalse(b["monster_ability_cooldowns"].get("bardo_provocacao"))
        self.assertTrue(ataques)

    def test_provocacao_vencida_libera_o_heroi(self):
        r, b, _ = montar()
        p0, p1, p2 = r.players.values()
        p0["pos"] = [10, 6]
        p0["bardo_provocado_por"] = b["id"]; p0["bardo_provocacao_turnos"] = 0
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(p0["bardo_provocacao_turnos"], 3)


class RecuoTests(unittest.TestCase):
    def _sem_provocar(self, b):
        b.setdefault("monster_ability_cooldowns", {})["bardo_provocacao"] = 3

    def test_atirador_ameacado_se_afasta_e_atira(self):
        r, b, ataques = montar()
        self._sem_provocar(b)
        p0 = r.players["p0"]; p0["pos"] = [9, 6]
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertGreater(distancia(b["pos"], p0["pos"]), 2)
        self.assertEqual(ataques, ["p0"])
        self.assertEqual(b["virotes"], 19)

    def test_foge_tambem_do_heroi_que_nao_e_o_alvo(self):
        r, b, _ = montar()
        self._sem_provocar(b)
        p0, p1, p2 = r.players.values()
        p0["pos"], p1["pos"] = [8, 8], [8, 2]
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertGreater(min(distancia(b["pos"], p0["pos"]), distancia(b["pos"], p1["pos"])), 2)

    def test_depois_do_recuo_o_alvo_continua_no_tiro(self):
        r, b, _ = montar()
        self._sem_provocar(b)
        p0 = r.players["p0"]; p0["pos"] = [9, 6]
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertLessEqual(distancia(b["pos"], p0["pos"]), b["attacks"][0]["range"])
        self.assertTrue(r._tem_linha_de_visao(b["pos"], p0["pos"]))

    def test_longe_dos_herois_fica_parado_atirando(self):
        r, b, ataques = montar()
        self._sem_provocar(b)
        p0 = r.players["p0"]; p0["pos"] = [12, 6]
        antes = list(b["pos"])
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(b["pos"], antes)
        self.assertEqual(ataques, ["p0"])

    def test_sem_movimento_atira_de_onde_esta(self):
        r, b, ataques = montar()
        self._sem_provocar(b)
        b["movement"] = 0; b["_water_moves_left"] = 0
        p0 = r.players["p0"]; p0["pos"] = [9, 6]
        antes = list(b["pos"])
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(b["pos"], antes)
        self.assertEqual(ataques, ["p0"])

    def test_agarrado_atira_de_onde_esta(self):
        r, b, ataques = montar()
        self._sem_provocar(b)
        p0 = r.players["p0"]; p0["pos"] = [9, 6]
        b["preso"] = True
        antes = list(b["pos"])
        r._captor_ativo = lambda *_a, **_k: {"id": "x", "hp": 5}
        asyncio.run(r._ai_bardo(b, alvos(r)))
        self.assertEqual(b["pos"], antes)
        self.assertEqual(ataques, ["p0"])

    def test_heroi_fora_da_masmorra_nao_conta_como_ameaca(self):
        r, b, _ = montar()
        self._sem_provocar(b)
        p0, p1, p2 = r.players.values()
        p0["pos"] = [12, 6]
        p1["pos"] = [9, 6]; p1["alive"] = False
        antes = list(b["pos"])
        asyncio.run(r._ai_bardo(b, [{"kind": "player", "obj": p0}]))
        self.assertEqual(b["pos"], antes)


if __name__ == "__main__":
    unittest.main(verbosity=1)
