"""A mansão do Leonel: derrotar todos no terreno, achar a entrada e, lá dentro, a passagem secreta.
Roda da raiz: python -X utf8 tools/test_elara_leonel_mansao.py"""
import json
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


def alcance(r, inicio=None, evitar=()):
    """Casas alcançáveis a pé, com as portas abertas e sem atravessar `evitar`."""
    inicio = tuple(inicio or r.stairs_pos)
    vistas, fila = {inicio}, [inicio]
    while fila:
        x, y = fila.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in vistas or n in evitar or not (0 <= n[0] < r.map_w and 0 <= n[1] < r.map_h):
                continue
            porta = r.tiles[n[1]][n[0]] == S.DOOR
            if r._blocks_tile(*n) and not porta:
                continue
            vistas.add(n)
            fila.append(n)
    return vistas


def sem_portas(r, inicio):
    """Como `alcance`, mas porta fechada barra."""
    vistas, fila = {tuple(inicio)}, [tuple(inicio)]
    while fila:
        x, y = fila.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in vistas and not r._blocks_tile(*n):
                vistas.add(n)
                fila.append(n)
    return vistas


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
    def test_area_secreta_so_pela_estante(self):
        d = M.masmorra_leonel_2()
        r = sala(d)
        self.assertNotIn((35, 6), alcance(r), "o salão secreto só abre pela estante")
        self.assertEqual({sp["type"] for sp in d["secret_passages"]}, {"mechanism"})
        self.assertEqual({k for sp in d["secret_passages"] for k in sp["key_decor_ids"]}, {"mansao_estante"})
        est = next(o for o in d["decorations"] if o["id"] == "mansao_estante")
        self.assertEqual(est["type"], "estante_livros")
        self.assertFalse(est.get("key_objective"), "acionar a estante não cumpre objetivo nenhum")

    def test_estante_da_passagem_e_a_do_canto_junto_da_parede_secreta(self):
        est = next(o for o in M.masmorra_leonel_2()["decorations"] if o["id"] == "mansao_estante")
        self.assertEqual(est["pos"], [24, 2])
        fala = next(f for f in M.masmorra_leonel_2()["falas"] if f["id"] == "mansao_estante")["texto"]
        self.assertIn("canto", fala)
        self.assertNotIn("salão", fala)

    def test_escrivaninha_junto_do_trono(self):
        d = M.masmorra_leonel_2()
        mesa = next(o for o in d["decorations"] if o["id"] == "mansao_mesa_cadeiras_10")
        self.assertEqual(mesa["pos"], [21, 3])

    def test_leonel_no_palco_e_elara_na_cela(self):
        d = M.masmorra_leonel_2()
        leo = next(m for m in d["monsters"] if m["type"] == M.TIPO_LEONEL)
        self.assertTrue(leo["target"])
        self.assertEqual(leo["pos"], [39, 6])
        self.assertEqual(d["elevacoes"]["39,6"], 1)
        self.assertEqual(d["prisoner"]["pos"], [45, 31])
        self.assertEqual(d["prisoner"]["nome"], "Elara")

    def test_calabouco_e_de_pedra_negra_e_a_cozinha_nao(self):
        d = M.masmorra_leonel_2()
        for casa in ("35,15", "30,6", "40,28"):
            self.assertEqual(d["materiais"].get(casa), "pedra_negra", casa)
        self.assertEqual(d["materiais"].get("25,27"), "madeira_escura")

    def test_plateia_da_cobertura_sem_tapar_a_visao(self):
        d = M.masmorra_leonel_2()
        sofas = [o for o in d["decorations"] if o["id"].startswith("salao_sofa")]
        self.assertGreaterEqual(len(sofas), 6)
        self.assertTrue(all(o["visao"] == "baixo" for o in sofas))

    def test_o_corredor_das_celas_passa_pelas_guilhotinas(self):
        d = M.masmorra_leonel_2()
        r = sala(d)
        guilhotinas = {tuple(t["pos"]) for t in d["traps"] if t["id"].startswith("salao_guilhotina")}
        self.assertEqual(guilhotinas, {(41, 19), (42, 19), (43, 19)})
        self.assertNotIn((42, 21), alcance(r, inicio=(42, 15), evitar=guilhotinas))
        self.assertIn((42, 21), alcance(r, inicio=(42, 15)))

    def test_celas_tem_o_que_achar(self):
        d = M.masmorra_leonel_2()
        com_loot = [o for o in d["decorations"] if o.get("loot")]
        self.assertGreaterEqual(len(com_loot), 3)
        self.assertTrue(all(o["type"] == "gaiola" for o in com_loot))

    def test_mapa_valido(self):
        ok, msg = S.validar_dungeon(M.masmorra_leonel_2())
        self.assertTrue(ok, msg)

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


def cena(destino, etapa, fatos=(), classe="warrior"):
    """Os textos que o jogador lê, pelo mesmo filtro de slides do jogo."""
    r = S.GameRoom("CENA")
    r.players["p0"] = S.make_player("p0", "H0", classe, 0)
    r.fatos = set(fatos)
    beat = S._story_beat("k", [GG.destinos()[destino]["dungeons"][etapa]["intro"]], r._requisito_do_slide)
    return [s["text"] for s in beat["slides"]]


class CenasTests(unittest.TestCase):
    def test_abertura_lembra_o_que_o_grupo_viveu(self):
        viu = " ".join(cena("elara_leonel_casa", 0, {"elara_viu_gilo_morrer"}))
        self.assertIn("A culpa é do Leonel", viu)
        self.assertNotIn("bilhete", viu)
        tarde = " ".join(cena("elara_leonel_casa", 0))
        self.assertIn("bilhete", tarde)
        self.assertNotIn("A culpa é do Leonel", tarde)

    def test_abertura_e_transicao_do_mago(self):
        self.assertNotIn("irmã", " ".join(cena("elara_leonel_casa", 0)))
        self.assertIn("irmã", " ".join(cena("elara_leonel_casa", 0, classe="mage")))
        self.assertNotIn("conhece esse choro", " ".join(cena("elara_leonel_casa", 1)))
        self.assertIn("conhece esse choro", " ".join(cena("elara_leonel_casa", 1, classe="mage")))

    def test_alerta_diz_quem_avisou(self):
        normal = " ".join(cena("elara_leonel_casa", 0))
        self.assertIn("Ninguém espera", normal)
        self.assertNotIn("tochas", normal)
        morto = " ".join(cena("elara_leonel_casa_alerta", 0, {"elara_bardo_morto"}))
        traiu = " ".join(cena("elara_leonel_casa_alerta", 0, {"elara_bardo_traiu"}))
        self.assertIn("bardo executado", morto); self.assertNotIn("assobio", morto)
        self.assertIn("assobio", traiu); self.assertNotIn("bardo executado", traiu)
        self.assertNotIn("Ninguém espera", morto)
        self.assertIn("sino", " ".join(cena("elara_leonel_casa_alerta", 1)))
        self.assertNotIn("sino", " ".join(cena("elara_leonel_casa", 1)))

    def test_transicao_entra_na_casa_e_prepara_a_passagem(self):
        t = " ".join(cena("elara_leonel_casa", 1))
        self.assertIn("porta de serviço", t)
        self.assertIn("atrás das paredes", t)

    def test_gravado_igual_ao_gerador_e_aceito_pelo_jogo(self):
        with open(os.path.join(RAIZ, "world_adventures.json"), encoding="utf-8") as f:
            gravado = json.load(f)
        for k in ("elara_leonel_casa", "elara_leonel_casa_alerta"):
            for i in (0, 1):
                intro = GG.destinos()[k]["dungeons"][i]["intro"]
                self.assertEqual(gravado[k]["dungeons"][i]["intro"], intro)
                self.assertEqual(S._clean_story_field(intro), intro)

    def test_falas_nao_repetem_as_cenas(self):
        chegada = next(f for f in M.masmorra_leonel_2()["falas"] if f["id"] == "mansao_chegada")["texto"]
        self.assertNotIn("chora", chegada)
        self.assertNotIn("cortinas", chegada)


class ObjetivoTests(unittest.IsolatedAsyncioTestCase):
    async def test_estante_abre_a_passagem_de_verdade(self):
        r = sala(M.masmorra_leonel_2())
        self.assertTrue(r._blocks_tile(27, 6))
        r.players["p0"]["pos"] = [24, 3]
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


class SalaoFluxoTests(unittest.IsolatedAsyncioTestCase):
    def preparar(self):
        r = sala(M.masmorra_leonel_2())
        r._is_turn = lambda pid: True
        self.leonel = next(m for m in r.monsters.values() if m["type"] == M.TIPO_LEONEL)
        return r

    async def test_sino_desliga_as_guilhotinas(self):
        r = self.preparar()
        r.players["p0"]["pos"] = [41, 5]
        await r.handle_activate_decor_mechanism("p0", "salao_sino")
        guil = [a for a in r.armadilhas if str(a.get("autoral_id", "")).startswith("salao_guilhotina")]
        self.assertEqual(len(guil), 3)
        self.assertTrue(all(a.get("desativada") for a in guil))

    async def test_portao_da_cela_barra_ate_abrir(self):
        r = self.preparar()
        self.assertEqual(r.door_styles.get((41, 29)), "portao_levadico")
        self.assertNotIn((44, 30), sem_portas(r, (40, 29)))
        r.players["p0"]["pos"] = [40, 29]
        await r.handle_toggle_portcullis("p0", 41, 29)
        self.assertFalse(r._is_closed_door(41, 29))
        self.assertIn((44, 30), sem_portas(r, (40, 29)))

    async def test_levar_a_elara_depois_do_leonel_conclui(self):
        r = self.preparar()
        r.prisoner["freed"] = True
        r.prisoner["pos"] = [40, 30]
        await r._check_objectives()
        self.assertFalse(r._objetivo_concluido, "o Leonel ainda está de pé")
        self.leonel["hp"] = 0
        await r._check_objectives()
        self.assertTrue(r._objetivo_concluido)
        self.assertIn("elara_leonel_vencido", r.fatos)
        self.assertIn("elara_elara_salva", r.fatos)
        self.assertNotIn("elara_morta", r.fatos)

    async def test_matar_o_leonel_nao_basta_com_a_elara_presa(self):
        r = self.preparar()
        self.leonel["hp"] = 0
        await r._check_objectives()
        self.assertFalse(r._objetivo_concluido)

    async def test_elara_morta_ainda_permite_encerrar_com_o_leonel_morto(self):
        r = self.preparar()
        await r._prisioneiro_morre()
        await r._check_objectives()
        self.assertFalse(r._objetivo_concluido, "falta o Leonel")
        self.leonel["hp"] = 0
        await r._check_objectives()
        self.assertTrue(r._objetivo_concluido)
        self.assertIn("elara_morta", r.fatos)
        self.assertIn("elara_leonel_vencido", r.fatos)
        self.assertNotIn("elara_elara_salva", r.fatos)


class PrisioneiroNomeTests(unittest.TestCase):
    def test_nome_do_mapa_vale_e_sem_nome_segue_prisioneiro(self):
        d = M.masmorra_leonel_2()
        self.assertEqual(sala(d).prisoner["nome"], "Elara")
        d["prisoner"].pop("nome")
        self.assertEqual(sala(d).prisoner["nome"], "Prisioneiro")

    def test_nome_invalido_e_recusado(self):
        d = M.masmorra_leonel_2()
        d["prisoner"]["nome"] = 7
        self.assertFalse(S.validar_dungeon(d)[0])


class FinalTests(unittest.TestCase):
    def fim(self, fatos=(), classe="warrior"):
        r = S.GameRoom("FIM")
        r.players["p0"] = S.make_player("p0", "H0", classe, 0)
        r.fatos = set(fatos)
        beat = S._story_beat("k", [GG.destinos()["elara_leonel_casa"]["outro_rota"]], r._requisito_do_slide)
        return " ".join(s["text"] for s in beat["slides"])

    def test_elara_salva(self):
        t = self.fim({"elara_elara_salva"}, "mage")
        self.assertIn("abraça a irmã", t)
        self.assertNotIn("não saiu", t)

    def test_elara_morta_muda_o_final(self):
        t = self.fim({"elara_morta"}, "mage")
        self.assertNotIn("abraça a irmã", t)
        self.assertNotIn("magra e furiosa", t)
        self.assertIn("não saiu", t)

    def test_final_gravado_igual_ao_gerador(self):
        with open(os.path.join(RAIZ, "world_adventures.json"), encoding="utf-8") as f:
            gravado = json.load(f)
        for k in ("elara_leonel_casa", "elara_leonel_casa_alerta"):
            self.assertEqual(gravado[k]["outro_rota"], GG.destinos()[k]["outro_rota"])


if __name__ == "__main__":
    unittest.main()
