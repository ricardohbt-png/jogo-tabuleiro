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


def sala(defn=None):
    random.seed(2024)
    r = S.GameRoom("CHARCOS")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.msgs = []

    async def noop(*a, **k): pass

    async def send(pid, m, *a, **k): r.msgs.append(m)
    r.gm_say = noop; r.broadcast = noop; r.send_to = send; r.push_state = noop
    r.load_authored_dungeon(deepcopy(defn or ALDEIA))
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


# Tabela do spec: salvas -> (renome, xp, ouro, fato)
TABELA = {6: (8, 225, 90, "charcos_criancas_todas"), 5: (5, 150, 60, "charcos_criancas_salvas"),
          4: (5, 150, 60, "charcos_criancas_salvas"), 3: (0, 90, 36, "charcos_criancas_perdidas"),
          2: (-2, 60, 24, "charcos_criancas_perdidas"), 1: (-4, 30, 12, "charcos_criancas_perdidas"),
          0: (-8, 0, 0, "charcos_criancas_mortas")}


def salvar(r, n):
    """As primeiras n crianças chegam à saída; as outras morrem."""
    for pr in r.prisoners[:n]:
        pr.update(freed=True, salvo=True, pos=[-1, -1])
    for pr in r.prisoners[n:]:
        pr["alive"] = False


def encerrar(n, renome=10):
    r, p = sala(); r.renome = renome
    r.world_adventure_progress = {}
    salvar(r, n)
    run(r._check_objectives())
    assert r.mission_complete_pending, f"{n} salvas: o botão Encerrar missão não abriu"
    xp, ouro = p["xp"], p["gold"]
    run(r.handle_encerrar_missao("p1"))
    return r, p["xp"] - xp, p["gold"] - ouro


class CriancasTests(unittest.TestCase):
    def test_seis_criancas_no_motor(self):
        r, _ = sala()
        self.assertEqual(len(r.prisoners), 6)
        self.assertEqual({pr["nome"] for pr in r.prisoners}, {"Tico", "Bento", "Davi", "Lina", "Maia", "Rosa"})

    def test_cada_quantidade_paga_a_faixa_certa(self):
        for n, (renome, xp, ouro, fato) in TABELA.items():
            with self.subTest(salvas=n):
                r, dxp, dgold = encerrar(n)
                self.assertEqual((dxp, dgold), (xp, ouro))
                self.assertEqual(r.renome, max(0, 10 + renome))
                self.assertIn(fato, r.fatos)

    def test_vila_hostil_so_com_zero(self):
        for n in range(7):
            with self.subTest(salvas=n):
                r, _, _ = encerrar(n)
                self.assertEqual(G.FATO_MORTE in r.fatos, n == 0, r.fatos)
                self.assertEqual("charcos_criancas_perdidas" in r.fatos, n in (1, 2, 3))

    def test_preco_sobe_so_com_o_marcador_de_zero(self):
        orig = {k: list(v) for k, v in S.CITY_PRICE_MODS.items()}
        S.CITY_PRICE_MODS.clear(); S.CITY_PRICE_MODS.update(G.modificadores())
        try:
            precos = {}
            for n in (0, 3, 6):
                fatos = encerrar(n)[0].fatos
                c = S.GameRoom("VILA"); c.fatos = set(fatos); c.world_location = G.CIDADE
                precos[n] = next(i["price"] for i in c._itens_da_loja("taverna") if i["id"] == "banquete_viagem")
            self.assertEqual(precos[0], round(precos[3] * 1.5))
            self.assertEqual(precos[3], precos[6])
        finally:
            S.CITY_PRICE_MODS.clear(); S.CITY_PRICE_MODS.update(orig)

    def test_morte_de_crianca_nao_falha_o_resgate(self):
        r, p = sala(); r.renome = 12
        run(r._prisioneiro_morre(r.prisoners[0])); run(r._prisioneiro_morre(r.prisoners[1]))
        self.assertEqual(r.renome, 12, "a consequência só vem da faixa")
        self.assertFalse(r.rescue_failed)
        self.assertNotIn(G.FATO_MORTE, r.fatos)
        self.assertEqual(r.phase, "playing")

    def test_matar_o_ferrao_paga_o_secundario_na_hora(self):
        r, p = sala(); xp0, ouro0 = p["xp"], p["gold"]
        ferrao(r)["hp"] = 0
        run(r._check_objectives())
        self.assertEqual(p["xp"] - xp0, 600)
        self.assertEqual(p["gold"] - ouro0, 250)
        self.assertIn(G.FATO_FERRAO, r.fatos)
        self.assertEqual(r.renome, 3)
        self.assertTrue(any(i.get("id") == G.ITEM_TROFEU for c in r.chests.values() for i in c["items"]))
        self.assertFalse(r.mission_complete_pending, "o principal é o resgate: faltam as crianças")

    def test_ferrao_depois_da_meta_soma_com_a_faixa(self):
        r, p = sala(); r.renome = 0
        salvar(r, 4)
        run(r._check_objectives())
        ferrao(r)["hp"] = 0
        run(r._check_objectives())
        xp0 = p["xp"]
        run(r.handle_encerrar_missao("p1"))
        self.assertEqual(p["xp"] - xp0, 150)
        self.assertEqual(r.renome, 3 + 5)


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
            # O autor edita os mapas à mão depois de gerados: o disco é a verdade, o gerador
            # só garante que cada arquivo existe e que a grade e o nome seguem os mesmos.
            self.assertEqual(gravada.get("name"), d.get("name"), arq)
            ok, msg = S.validar_dungeon(gravada)
            self.assertTrue(ok, f"{arq}: {msg}")

    def test_aldeia_gravada_tem_as_seis_criancas_alcancaveis(self):
        """Uma criança que ninguém alcança trava o fim da missão (a Aldeia não tem saída pela escada)."""
        gravada = self.ler("dungeons/charcos_4b_aldeia.json")
        self.assertNotIn("prisoner", gravada)
        prs = gravada["prisoners"]
        self.assertEqual([p["nome"] for p in prs], ["Tico", "Bento", "Davi", "Lina", "Maia", "Rosa"])
        self.assertEqual([p["image"] for p in prs], [a + ".png" for a in (
            "garoto_loiro", "garoto_medieval", "garoto_pele_escura", "menina_cabelos_castanhos",
            "menina_pele_escura", "menina_ruiva")])
        self.assertEqual([p.get("model3d") for p in prs], [a + ".glb" for a in (
            "garoto_loiro", "garoto_medieval", "garoto_pele_escura", "menina_cabelos_castanhos",
            "menina_pele_escura")] + [None])
        r, p = sala(gravada)
        self.assertEqual(len(r.prisoners), 6)
        ocupadas = {tuple(t) for d in r.decorations for t in r._decor_tiles(d)}
        ocupadas |= {tuple(m["pos"]) for m in r.monsters.values()}
        casas = [tuple(pr["pos"]) for pr in prs]
        self.assertEqual(len(set(casas)), 6)
        for pr in prs:
            x, y = pr["pos"]
            self.assertEqual(pr["room_id"], 2)
            self.assertTrue(42 <= x <= 52 and 12 <= y <= 23, pr)
            self.assertFalse(r._blocks_tile(x, y), pr)
            self.assertNotIn((x, y), ocupadas, pr)
        # abre toda passagem/porta que a cela tem (mecanismos) e confere a viagem da entrada até cada uma
        chaves = {k for sp in r.secret_passages for k in sp.get("key_decor_ids", [])}
        for cond in (gravada.get("door_conditions") or {}).values():
            chaves |= set(cond.get("key_decor_ids", []))
        self.assertTrue(chaves, "a cela se abre por mecanismo")
        for did in sorted(chaves):
            d = next(d for d in r.decorations if d["id"] == did)
            perto = next((d["pos"][0] + dx, d["pos"][1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                         if (dx or dy) and not r._blocks_tile(d["pos"][0] + dx, d["pos"][1] + dy))
            p["pos"] = list(perto)
            run(r.handle_activate_decor_mechanism("p1", did))
        from collections import deque
        ent = (gravada["entrance"]["x"], gravada["entrance"]["y"])
        visto, fila = {ent}, deque([ent])
        while fila:
            x, y = fila.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in visto or not (0 <= n[0] < r.map_w and 0 <= n[1] < r.map_h) or r._blocks_tile(*n):
                    continue
                visto.add(n); fila.append(n)
        for c in casas:
            self.assertIn(c, visto, f"a criança em {c} não é alcançável da entrada")
        # e alguma passagem que a gente abriu de fato deixou de ser parede
        self.assertTrue(any(not r._blocks_tile(*sp["pos"]) for sp in r.secret_passages))

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
        self.assertTrue({"charcos_gancho", "charcos_gratidao", "charcos_gratidao_parcial",
                         "charcos_luto_ysa", "charcos_hostil_ysa"} <= ids)
        self.assertEqual({s["name"] for s in slots}, {"Ysa", "Bento", "Velho Quim"})
        self.assertTrue(any(i["id"] == G.ITEM_TROFEU for i in self.ler("itens_personalizados.json")))


if __name__ == "__main__":
    unittest.main()
