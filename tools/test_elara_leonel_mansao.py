"""A mansão do Leonel: derrotar todos no terreno, achar a entrada e, lá dentro, a passagem secreta.
Roda da raiz: python -X utf8 tools/test_elara_leonel_mansao.py"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_graciero_mapas as M
import gerar_elara_graciero as GG
from gerar_campanha_sombras import salas_alcancaveis


def sala(defn):
    r = S.GameRoom("MANSAO")
    r.players["p0"] = S.make_player("p0", "H0", "warrior", 0)
    r.host_pid = "p0"

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state = nada; r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    r.load_authored_dungeon(defn)
    r.phase = "playing"
    r.players["p0"]["alive"] = True
    r.players["p0"]["pos"] = list(r.stairs_pos)
    return r


def derrota(r, ignorar=()):
    for m in r.monsters.values():
        if m["type"] not in ignorar:
            m["hp"] = 0


class MapasTests(unittest.TestCase):
    def test_alerta_e_a_mansao_com_desafios_a_mais(self):
        n, a = M.masmorra_leonel_1(), M.masmorra_leonel_1_alerta()
        for campo in ("grid", "tiles", "materiais", "decorations", "entrance", "exit", "objectives", "rooms"):
            self.assertEqual(n[campo], a[campo], campo)
        self.assertEqual(a["monsters"][:len(n["monsters"])], n["monsters"])
        self.assertEqual(a["traps"][:len(n["traps"])], n["traps"])
        self.assertEqual(len(a["monsters"]) - len(n["monsters"]), 2)
        self.assertEqual(len(a["traps"]) - len(n["traps"]), 1)
        self.assertIn("casa_alerta", {f["id"] for f in a["falas"]})
        self.assertNotIn("casa_alerta", {f["id"] for f in n["falas"]})
        self.assertEqual(a["id"], "elara_leonel_1_alerta")

    def test_extras_do_alerta_em_casa_livre(self):
        n, a = M.masmorra_leonel_1(), M.masmorra_leonel_1_alerta()
        r = sala(a)
        ocupadas = [tuple(m["pos"]) for m in a["monsters"]] + [tuple(t["pos"]) for t in a["traps"]]
        self.assertEqual(len(ocupadas), len(set(ocupadas)))
        for x in a["monsters"][len(n["monsters"]):] + a["traps"][len(n["traps"]):]:
            self.assertFalse(r._blocks_tile(*x["pos"]), x)

    def test_objetivo_em_duas_etapas(self):
        o = M.masmorra_leonel_1()["objectives"]
        self.assertEqual(o["primary"]["type"], "reach_exit")
        self.assertEqual([s["condition"]["type"] for s in o["steps"]], ["kill_all", "reach_exit"])
        for s in o["steps"]:
            self.assertTrue(s["text"]["pt"] and s["text"]["en"])
        ok, msg = S.validar_dungeon(M.masmorra_leonel_1())
        self.assertTrue(ok, msg)

    def test_falas_contam_o_exterior_e_a_entrada(self):
        d = M.masmorra_leonel_1()
        f = {x["id"]: x for x in d["falas"]}
        self.assertNotIn("cortinas", f["casa_chegada"]["texto"])
        self.assertIn("mansão", f["casa_chegada"]["texto"])
        self.assertEqual(f["casa_entrada"]["pos"], [d["exit"]["x"], d["exit"]["y"]])
        self.assertIn("mansão", f["casa_entrada"]["texto"])


class InteriorTests(unittest.TestCase):
    def test_interior_com_a_sala_secreta_so_pela_estante(self):
        d = M.masmorra_leonel_2()
        self.assertEqual(d["name"], "A Mansão do Leonel")
        self.assertEqual(set(salas_alcancaveis(d)), {0, 1}, "Leonel e Elara só depois da passagem secreta")
        self.assertEqual(set(salas_alcancaveis(d, passagens_abertas=True)), {0, 1, 2})
        self.assertEqual({sp["type"] for sp in d["secret_passages"]}, {"mechanism"})
        self.assertEqual({k for sp in d["secret_passages"] for k in sp["key_decor_ids"]}, {"mansao_estante"})
        est = next(o for o in d["decorations"] if o["id"] == "mansao_estante")
        self.assertEqual(est["type"], "estante_livros")
        self.assertFalse(est.get("key_objective"), "acionar a estante não cumpre o baú da Elara")

    def test_leonel_e_elara_na_sala_secreta(self):
        d = M.masmorra_leonel_2()
        sec = next(r for r in d["rooms"] if r["id"] == 2)

        def dentro(p):
            return sec["x"] <= p[0] < sec["x"] + sec["w"] and sec["y"] <= p[1] < sec["y"] + sec["h"]

        leo = next(m for m in d["monsters"] if m["type"] == M.TIPO_LEONEL)
        self.assertTrue(dentro(leo["pos"]) and leo["target"])
        bau = next(c for c in d["chests"] if c["key_objective"])
        self.assertTrue(dentro(bau["pos"]))
        self.assertTrue(dentro(next(f for f in d["falas"] if f["falante"]["nome"] == "Elara")["pos"]))

    def test_ninguem_mais_fala_em_poroes(self):
        textos = [f["texto"] for fn in (M.masmorra_leonel_1, M.masmorra_leonel_2) for f in fn()["falas"]]
        textos += [s["text"]["pt"] for s in M.masmorra_leonel_1()["objectives"]["steps"]]
        textos.append(M.masmorra_leonel_2()["name"])
        for k in ("elara_leonel_casa", "elara_leonel_casa_alerta"):
            textos += [s["text"] for s in GG.destinos()[k]["outro_rota"]["slides"]]
        cais = S.carregar_dungeon("elara_graciero_cais.json")
        textos += [str(i.get("texto")) for c in cais["chests"] for i in c["items"]]
        for t in textos:
            self.assertNotIn("porõ", t.lower(), t)
            self.assertNotIn("porão", t.lower(), t)


class ObjetivoTests(unittest.IsolatedAsyncioTestCase):
    async def test_estante_abre_a_passagem_de_verdade(self):
        r = sala(M.masmorra_leonel_2())
        self.assertTrue(r._blocks_tile(27, 6))
        r.players["p0"]["pos"] = [26, 6]
        await r.handle_activate_decor_mechanism("p0", "mansao_estante")
        self.assertFalse(r._blocks_tile(27, 6))
        self.assertFalse(r._blocks_tile(27, 7))

    async def test_chegar_a_entrada_com_inimigos_vivos_nao_conclui(self):
        r = sala(M.masmorra_leonel_1())
        r.players["p0"]["pos"] = list(r.exit_pos)
        await r._check_objectives()
        self.assertFalse(r._objetivo_concluido)
        self.assertFalse(r.mission_complete_pending)

    async def test_derrotar_todos_e_depois_achar_a_entrada_conclui(self):
        r = sala(M.masmorra_leonel_1())
        derrota(r)
        await r._check_objectives()
        self.assertEqual(r.mission_step_index, 1)
        self.assertFalse(r._objetivo_concluido, "falta achar a entrada")
        r.players["p0"]["pos"] = list(r.exit_pos)
        await r._check_objectives()
        self.assertTrue(r._objetivo_concluido)
        self.assertTrue(r.mission_complete_pending)

    async def test_cavalos_do_cercado_nao_travam_derrotar_todos(self):
        r = sala(M.masmorra_leonel_1())
        self.assertEqual(sum(m["type"] == "cavalo_sela" for m in r.monsters.values()), 2)
        derrota(r, ignorar=("cavalo_sela",))
        await r._check_objectives()
        self.assertEqual(r.mission_step_index, 1)

    def test_derrotar_todos_ainda_cobra_quem_e_hostil(self):
        r = sala(M.masmorra_leonel_1())
        derrota(r, ignorar=("cavalo_sela", "orc"))
        self.assertFalse(r._objetivo_cumprido({"type": "kill_all"}))

    async def test_a_ultima_etapa_nao_pula_a_anterior_sem_etapas_nao_muda(self):
        d = M.masmorra_leonel_1()
        d["objectives"].pop("steps")
        r = sala(d)
        r.players["p0"]["pos"] = list(r.exit_pos)
        await r._check_objectives()
        self.assertTrue(r._objetivo_concluido, "sem etapas, reach_exit vale como sempre")


if __name__ == "__main__":
    unittest.main()
