"""Campanha "A Maré do Charco" com o motor real: o Ferrão, os bruxos e as crianças.
Roda da raiz: python -X utf8 tools/test_charcos_fluxo.py"""
import asyncio
import json
import random
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))
import server as S  # noqa: E402
import gerar_campanha_charcos as G  # noqa: E402

G.preparar()                      # registra o troféu no catálogo vivo deste processo
ALDEIA = G.masmorras()["charcos_4b_aldeia.json"]


def run(coro): return asyncio.run(coro)


def sala():
    random.seed(2024)
    r = S.GameRoom("CHARCOS")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.msgs = []

    async def noop(*a, **k): pass

    async def send(pid, m, *a, **k): r.msgs.append(m)
    r.gm_say = noop; r.broadcast = noop; r.send_to = send; r.push_state = noop
    r.load_authored_dungeon(deepcopy(ALDEIA))
    r.phase = "playing"
    for rm in r.rooms:
        rm["locked"] = False
    r.world_adventure_id = G.AVENTURA; r.world_adventure_index = 4
    p["pos"] = [5, 18]
    return r, p


def ferrao(r): return next(m for m in r.monsters.values() if m["type"] == "ferrao_charcos_adulto")
def tipo(r, t): return [m for m in r.monsters.values() if m["type"] == t]
def puxar_corrente(r, p):
    c = next(d for d in r.decorations if d["id"] == "aldeia_corrente")
    p["pos"] = [c["pos"][0] - 1, c["pos"][1]]
    run(r.handle_activate_decor_mechanism("p1", "aldeia_corrente"))
    p["pos"] = [5, 18]


class FerraoTests(unittest.TestCase):
    def test_cela_fechada_ferrao_nao_ataca(self):
        r, p = sala()
        f = ferrao(r)
        antes = (list(f["pos"]), {m["id"]: m["hp"] for m in r.monsters.values()}, p["hp"])
        for _ in range(3):
            run(r.gm_phase(only_monster=f))
        self.assertEqual(f["pos"], antes[0])
        self.assertEqual({m["id"]: m["hp"] for m in r.monsters.values()}, antes[1])
        self.assertEqual(p["hp"], antes[2])

    def test_alavanca_solta_e_ele_ataca_monstros_da_mesma_sala(self):
        r, p = sala()
        f = ferrao(r)
        puxar_corrente(r, p)
        hp0 = {m["id"]: m["hp"] for m in r.monsters.values()}
        for _ in range(6):
            run(r.gm_phase(only_monster=f))
        feridos = [m for m in r.monsters.values() if m["hp"] < hp0[m["id"]] and m is not f]
        self.assertTrue(feridos, "o Ferrão solto fere os bruxos")
        self.assertTrue(all(m["room_id"] == f["room_id"] for m in feridos))

    def test_bruxos_revidam(self):
        r, p = sala()
        f = ferrao(r)
        puxar_corrente(r, p)
        bruxos = [m for m in r.monsters.values() if m["type"] in ("goblin_xama", "necromante")]
        golpes = []
        orig_um, orig_varios = r._execute_one_monster_attack, r._monster_execute_attacks

        async def espia_um(monstro, ataque, alvo, *a, **k):
            golpes.append((monstro["type"], alvo["obj"].get("id")))
            return await orig_um(monstro, ataque, alvo, *a, **k)

        async def espia_varios(monstro, alvo, *a, **k):
            golpes.append((monstro["type"], alvo["obj"].get("id")))
            return await orig_varios(monstro, alvo, *a, **k)
        r._execute_one_monster_attack, r._monster_execute_attacks = espia_um, espia_varios
        for _ in range(10):
            for b in bruxos:
                if b["hp"] > 0:
                    run(r.gm_phase(only_monster=b))
        contra_ferrao = [g for g in golpes if g[1] == f["id"]]
        self.assertTrue(contra_ferrao, "os bruxos atacam o Ferrão solto")
        self.assertTrue(all(g[1] == f["id"] for g in golpes), "e só ele (nenhum herói à vista)")

    def test_bruxos_nao_atacam_outros_monstros(self):
        r, _ = sala()
        xama = tipo(r, "goblin_xama")[0]
        zumbi = tipo(r, "zumbi_infectado")[0]
        self.assertFalse(r._monster_hostility_matches(xama, zumbi))
        self.assertTrue(r._monster_hostility_matches(xama, ferrao(r)))


class CriancasTests(unittest.TestCase):
    def libertar(self, r):
        r.prisoner["freed"] = True
        r.prisoner["alive"] = True
        r.prisoner["pos"] = [r.exit_pos[0] + 1, r.exit_pos[1]]

    def test_criancas_mortas_aplica_a_consequencia_e_a_missao_segue(self):
        r, p = sala(); r.renome = 12
        run(r._prisioneiro_morre()); run(r._prisioneiro_morre())
        self.assertEqual(r.renome, 7)
        self.assertIn(G.FATO_MORTE, r.fatos)
        self.assertEqual(r.phase, "playing")
        run(r._check_objectives())
        self.assertEqual(r.objective_status["primary"]["status"], "failed")
        self.assertEqual(r.objective_status["alternativo"]["status"], "pending")
        self.assertFalse(r.mission_complete_pending)

    def test_matar_o_ferrao_com_criancas_vivas_paga_o_secundario(self):
        r, p = sala(); xp0 = p["xp"]
        self.libertar(r)
        ferrao(r)["hp"] = 0
        run(r._check_objectives())
        self.assertTrue(r.mission_complete_pending)
        self.assertEqual(p["xp"] - xp0, 150 + 600)
        self.assertEqual(p["gold"], 60 + 250)
        self.assertIn(G.FATO_FERRAO, r.fatos)
        self.assertEqual(r.renome, 3)
        self.assertTrue(any(i.get("id") == G.ITEM_TROFEU for c in r.chests.values() for i in c["items"]))

    def test_matar_com_criancas_mortas_so_xp_reduzido(self):
        r, p = sala(); r.renome = 10; xp0 = p["xp"]; ouro0 = p["gold"]
        run(r._prisioneiro_morre())
        ferrao(r)["hp"] = 0
        run(r._check_objectives())
        self.assertTrue(r.mission_complete_pending)
        self.assertEqual(p["xp"] - xp0, 150)
        self.assertEqual(p["gold"], ouro0)
        self.assertIn(G.FATO_FERRAO, r.fatos)
        self.assertEqual(r.renome, 5, "só a perda das crianças; nada da recompensa do Ferrão")
        self.assertFalse(any(i.get("id") == G.ITEM_TROFEU for c in r.chests.values() for i in c["items"]))

    def test_fugir_pela_escada_com_criancas_mortas_nao_conclui(self):
        r, p = sala()
        run(r._prisioneiro_morre())
        run(r._check_objectives())
        self.assertFalse(r._objetivo_concluido)
        self.assertEqual(r.world_adventure_progress.get(G.AVENTURA, 0), 0)
        self.assertIn(G.FATO_MORTE, r.fatos)

    def test_nova_tentativa_restaura_as_criancas_mas_nao_o_renome(self):
        r, p = sala(); r.renome = 10
        run(r._prisioneiro_morre())
        r.load_authored_dungeon(deepcopy(ALDEIA))
        self.assertFalse(r.rescue_failed)
        self.assertTrue(r.prisoner["alive"] if "alive" in r.prisoner else True)
        self.assertEqual(r.renome, 5)
        self.assertIn(G.FATO_MORTE, r.fatos)

    def test_criancas_mortas_com_o_ferrao_ja_morto_conclui_na_hora(self):
        r, p = sala()
        ferrao(r)["hp"] = 0
        run(r._check_objectives())
        run(r._prisioneiro_morre())
        run(r._check_objectives())
        self.assertTrue(r.mission_complete_pending)


class VilaTests(unittest.TestCase):
    def setUp(self):
        self._orig = {k: list(v) for k, v in S.CITY_PRICE_MODS.items()}
        S.CITY_PRICE_MODS.clear(); S.CITY_PRICE_MODS.update(G.modificadores())

    def tearDown(self):
        S.CITY_PRICE_MODS.clear(); S.CITY_PRICE_MODS.update(self._orig)

    def cidade(self, fatos):
        r = S.GameRoom("VILA")
        r.fatos = set(fatos)
        r.world_location = G.CIDADE
        return r

    def test_hostilidade_da_vila_sobe_os_precos_e_muda_as_conversas(self):
        normal, hostil = self.cidade(set()), self.cidade({G.FATO_MORTE})
        base = next(i["price"] for i in normal._itens_da_loja("taverna") if i["id"] == "banquete_viagem")
        sobe = next(i["price"] for i in hostil._itens_da_loja("taverna") if i["id"] == "banquete_viagem")
        self.assertEqual(sobe, round(base * 1.5))
        conv = G.conversas_taverna()["npc_ms42peq8"]
        visiveis = lambda r: [c["id"] for c in conv if r._avaliar_requisito(c["requisito"])[0]]
        self.assertIn("charcos_gancho", visiveis(normal))
        self.assertNotIn("charcos_gancho", visiveis(hostil))
        self.assertIn("charcos_hostil_ysa", visiveis(hostil))
        self.assertNotIn("charcos_hostil_ysa", visiveis(normal))

    def test_cadeia_de_destinos_pelo_motor_real(self):
        S.WORLD_ADVENTURES.update(G.destinos())
        try:
            r = self.cidade(set())
            visivel = lambda aid: r._aventura_visivel(S.WORLD_ADVENTURES[aid])
            self.assertFalse(visivel(G.AVENTURA))
            r.fatos.add(G.FATO_GANCHO)
            self.assertTrue(visivel(G.AVENTURA))
            r.world_adventure_progress[G.AVENTURA] = len(S.WORLD_ADVENTURES[G.AVENTURA]["dungeons"])
            self.assertFalse(visivel(G.AVENTURA), "concluída a cadeia, o destino some do mapa")
        finally:
            for k in G.destinos():
                S.WORLD_ADVENTURES.pop(k, None)


class DiscoTests(unittest.TestCase):
    """O que o gerador gravou é o que o gerador produz hoje (ninguém esqueceu de rodá-lo)."""

    def ler(self, nome):
        import json
        return json.loads((RAIZ / nome).read_text(encoding="utf-8"))

    def test_masmorras_gravadas(self):
        for arq, d in G.masmorras().items():
            gravada = self.ler(f"dungeons/{arq}")
            self.assertEqual(gravada, json.loads(json.dumps(d)), arq)
            ok, msg = S.validar_dungeon(gravada)
            self.assertTrue(ok, f"{arq}: {msg}")

    def test_destinos_gravados_e_carregados(self):
        gravados = self.ler("world_adventures.json")
        sem_vazios = lambda v: json.loads(json.dumps(v))
        for did, dest in G.destinos().items():
            self.assertEqual(sem_vazios(gravados[did]), sem_vazios(dest), did)
            self.assertIn(did, S.WORLD_ADVENTURES, "o servidor carrega o destino no boot")

    def test_modificador_e_cenas_e_troféu_gravados(self):
        self.assertEqual(self.ler("cidade_modificadores.json"), G.modificadores())
        self.assertEqual(S.CITY_PRICE_MODS.get(G.CIDADE), G.modificadores()[G.CIDADE], "carregado no boot")
        slots = self.ler("city_scenes.json")[G.CIDADE]["taverna"]["slots"]
        ids = {c["id"] for s in slots for c in s["conversations"]}
        self.assertTrue({"charcos_gancho", "charcos_gratidao", "charcos_hostil_ysa"} <= ids)
        self.assertEqual({s["name"] for s in slots}, {"Ysa", "Bento", "Velho Quim"})
        self.assertTrue(any(i["id"] == G.ITEM_TROFEU for i in self.ler("itens_personalizados.json")))


if __name__ == "__main__":
    unittest.main()
