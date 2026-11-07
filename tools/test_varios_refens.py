"""Lista de reféns por mapa, com compatibilidade com o refém único."""
import ast
import asyncio
import copy
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as S
from test_decor_roundtrip import _defn_base
from test_elara_leonel_mansao import sala
from test_handler_smoke import FakeWS


def mapa(**extra):
    d = _defn_base()
    d.pop("prisoner", None)
    d.update(extra)
    return d


class VariosRefensTests(unittest.TestCase):
    def test_mapa_antigo_vira_lista_de_um(self):
        r = sala(mapa(prisoner={"pos": [3, 3], "room_id": None}))
        self.assertEqual([p["id"] for p in r.prisoners], ["refem_0"])
        self.assertIs(r.prisoner, r.prisoners[0])
        self.assertEqual(r.prisoner["nome"], "Prisioneiro")
        self.assertEqual(r.prisoner["modo"], "guiar")
        self.assertFalse(r.prisoner["salvo"])

    def test_varios_com_ids_e_nomes(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3], "nome": "Tico"}, {"pos": [4, 3]}]))
        self.assertEqual([p["id"] for p in r.prisoners], ["refem_0", "refem_1"])
        self.assertEqual(r.prisoners[0]["nome"], "Tico")
        self.assertEqual(r.prisoners[1]["nome"], "Prisioneiro")

    def test_setter_de_compatibilidade(self):
        r = sala(mapa())
        r.prisoner = {"pos": [1, 1], "alive": True}
        self.assertEqual(r.prisoners[0]["id"], "refem_0")
        r.prisoner = None
        self.assertEqual(r.prisoners, [])
        self.assertIsNone(r.prisoner)

    def test_ajudantes(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [4, 3]}]))
        a, b = r.prisoners
        self.assertIs(r._refem_por_id("refem_1"), b)
        self.assertIs(r._refem_por_id(None), a)
        self.assertIs(r._refem_por_id("__prisioneiro__"), a)
        self.assertIsNone(r._refem_por_id("refem_9"))
        self.assertTrue(r._eh_refem(b))
        self.assertFalse(r._eh_refem(dict(b)))
        a["salvo"] = True
        self.assertIs(r.prisoner, b)
        self.assertEqual(r._refens_no_mapa(), [b])

    def test_validador(self):
        faixas = {"primary": {"type": "rescue_prisoner", "meta": 1,
                              "faixas": [{"de": 0, "ate": 2}]}, "secondary": []}
        ok, _ = S.validar_dungeon(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [4, 3]}],
                                       objectives=faixas))
        self.assertTrue(ok)
        treze = [{"pos": [x % 12, 2 + x // 12]} for x in range(13)]
        self.assertFalse(S.validar_dungeon(mapa(prisoners=treze))[0])
        self.assertFalse(S.validar_dungeon(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [3, 3]}]))[0])
        self.assertFalse(S.validar_dungeon(
            mapa(prisoner={"pos": [3, 3]}, prisoners=[{"pos": [4, 3]}]))[0])
        self.assertFalse(S.validar_dungeon(mapa(prisoners={"pos": [3, 3]}))[0])

    def test_foto_antiga_e_nova(self):
        defn = mapa()
        r = sala(defn)
        antigo = {"pos": [2, 2], "hp": 5, "alive": True, "freed": True, "nome": "Zé"}
        corpo = r._foto_aplicar_sala({"sala": {"prisoner": antigo}, "pids": {}}, {}, defn)
        self.assertEqual(len(r.prisoners), 1)
        p = r.prisoners[0]
        self.assertEqual((p["id"], p["modo"], p["salvo"], p["hp"], p["nome"]),
                         ("refem_0", "guiar", False, 5, "Zé"))
        self.assertIs(r.prisoner, p)
        novo = [{"pos": [2, 2], "id": "refem_0", "modo": "guiar", "salvo": True},
                {"pos": [3, 2], "id": "refem_1", "modo": "ficar", "salvo": False}]
        r._foto_aplicar_sala({"sala": {"prisoners": copy.deepcopy(novo)}, "pids": {}}, {}, defn)
        self.assertEqual([(p["id"], p["modo"], p["salvo"]) for p in r.prisoners],
                         [("refem_0", "guiar", True), ("refem_1", "ficar", False)])

    def test_game_state_manda_as_duas_chaves(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3]}]))
        est = r._game_state_payload()
        self.assertEqual(len(est["prisoners"]), 1)
        self.assertIs(est["prisoner"], est["prisoners"][0])


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quem ainda pode ler `self.prisoner` diretamente: (arquivo, função).
PERMITIDOS = {
    # A própria propriedade e o ajudante que a tem como definição.
    ("server.py", "prisoner"),
    ("server.py", "_refem_por_id"),
    # Compatibilidade com o cliente, que só migra na Task 5.
    ("server.py", "_refem_chave_cliente"),
    ("server.py", "_refem_chave_entidade"),
    ("server.py", "_game_state_payload"),
    # Tutorial do Paladino: um refém só, por construção.
    ("tutorial_training.py", "_training_prisoner_dialogue"),
    ("tutorial_training.py", "_training_init"),
    ("tutorial_training.py", "_dispensar_prisioneiro"),
    ("tutorial_training.py", "_training_end_turn"),
    ("tutorial_training.py", "handle_repetir_tutorial"),
}


def usos_de_prisoner(arquivo):
    """(função, linha) de cada `self.prisoner` do arquivo."""
    with open(os.path.join(RAIZ, arquivo), encoding="utf-8") as f:
        arvore = ast.parse(f.read())
    achados = []

    def visita(no, funcao):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcao = no.name
        if (isinstance(no, ast.Attribute) and no.attr == "prisoner"
                and isinstance(no.value, ast.Name) and no.value.id == "self"):
            achados.append((funcao, no.lineno))
        for filho in ast.iter_child_nodes(no):
            visita(filho, funcao)

    visita(arvore, None)
    return achados


def dois_libertos():
    r = sala(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [5, 3]}]))
    for pr in r.prisoners:
        pr.update(freed=True, rescuer_pid="p0", rescuer_original="p0")
    return r


def tem(lista, alvo):
    return any(x is alvo for x in lista)


class MigracaoDoServidorTests(unittest.IsolatedAsyncioTestCase):
    def test_sem_uso_direto_de_prisoner_no_servidor(self):
        fora = [(arq, fn, linha)
                for arq in ("server.py", "tutorial_training.py")
                for fn, linha in usos_de_prisoner(arq)
                if (arq, fn) not in PERMITIDOS]
        self.assertEqual(fora, [])

    def test_area_atinge_cada_refem_liberto(self):
        r = dois_libertos()
        a, b = r.prisoners
        for pr in (a, b):
            self.assertTrue(tem(r._alvos_na_area(4, 3, 1), pr))
            self.assertTrue(tem(r._alvos_na_area_quadrada(4, 3, 4), pr))
            self.assertTrue(tem(r._alvos_no_inverno([(3, 3), (5, 3)]), pr))
            self.assertTrue(tem(r._tempestade_entidades(), pr))
            self.assertTrue(tem(r._prisao_chamas_entidades(), pr))
        a["freed"] = False
        self.assertFalse(tem(r._alvos_na_area(4, 3, 1), a))
        self.assertTrue(tem(r._alvos_na_area(4, 3, 1), b))

    async def test_casa_ocupada_por_qualquer_refem(self):
        r = dois_libertos()
        p = r.players["p0"]
        p.update(pos=[5, 2], moves_left=6)
        r._is_turn = lambda pid: True
        r._intro_masmorra_bloqueada = lambda: False
        await r.handle_move("p0", 0, 1)
        self.assertEqual(p["pos"], [5, 2])
        self.assertTrue(r._ocupante_do_grupo_em(5, 3, p))
        self.assertFalse(r._tile_livre_para_animado(5, 3, "qualquer"))
        self.assertTrue(r._tile_livre_para_animado(6, 3, "qualquer"))
        r.prisoners[1]["salvo"] = True
        self.assertTrue(r._tile_livre_para_animado(5, 3, "qualquer"))
        self.assertFalse(r._ocupante_do_grupo_em(5, 3, p))

    async def test_dano_nao_confunde_refens(self):
        r = dois_libertos()
        a, b = r.prisoners
        await r._aplicar_dano_alvo(b, 99, S.DMG_PHYSICAL, None)
        self.assertFalse(b["alive"])
        self.assertTrue(a["alive"])
        self.assertEqual(a["hp"], S.PRIS_HP)
        self.assertEqual(a["rescuer_pid"], "p0")
        self.assertTrue(r.rescue_failed)

    async def test_dano_no_segundo_por_todas_as_vias(self):
        for via in ("_dano_em_alvo", "_aplicar_dano_alvo"):
            r = dois_libertos()
            a, b = r.prisoners
            await getattr(r, via)(b, 2, S.DMG_PHYSICAL, None)
            self.assertEqual((a["hp"], b["hp"]), (S.PRIS_HP, S.PRIS_HP - 2), via)

    async def test_protetor_no_segundo_refem(self):
        r = dois_libertos()
        a, b = r.prisoners
        p = r.players["p0"]
        p.update(class_id="paladin", pos=[5, 2], fome=100, sede=100, bonus_action_used=False)
        r._is_turn = lambda pid: True
        await r.handle_protetor("p0", {"target_id": "refem_1"})
        self.assertEqual(p["protetor_alvo"], "refem_1")
        self.assertIs(r._protetor_target("refem_1"), b)
        self.assertEqual(r._protetor_target_id(b), "refem_1")
        hp_heroi = p["hp"]
        await r._aplicar_dano_alvo(a, 2, S.DMG_PHYSICAL, None, is_attack=True)
        self.assertEqual(p["hp"], hp_heroi)            # refem_0 não está protegido
        self.assertEqual(a["hp"], S.PRIS_HP - 2)
        dano_alvo, transferencia = await r._processar_dano_protetor(b, 10, is_attack=True)
        self.assertLess(dano_alvo, 10)
        self.assertIs(transferencia[0], p)

    async def test_protetor_de_foto_antiga_segue_valendo(self):
        r = dois_libertos()
        a, _ = r.prisoners
        p = r.players["p0"]
        p.update(class_id="paladin", pos=[3, 2], protetor_ativo=True, protetor_alvo="__prisioneiro__")
        self.assertIs(r._protetor_target("__prisioneiro__"), a)
        dano_alvo, transferencia = await r._processar_dano_protetor(a, 10, is_attack=True)
        self.assertLess(dano_alvo, 10)
        self.assertIs(transferencia[0], p)

    def test_cliente_antigo_reconhece_o_primeiro_refem(self):
        """Até a Task 5 o cliente casa o literal com `state.prisoner`."""
        r = dois_libertos()
        a, b = r.prisoners
        p = r.players["p0"]
        self.assertEqual(r._refem_chave_cliente(a), "__prisioneiro__")
        self.assertEqual(r._refem_chave_cliente(b), "refem_1")
        self.assertEqual(r._refem_chave_entidade(a), "pr:singleton")
        self.assertEqual(r._refem_chave_entidade(b), "pr:refem_1")
        p.update(protetor_ativo=True, protetor_alvo="refem_0")
        est = r._game_state_payload()
        self.assertEqual(est["players"][0]["protetor_alvo"], "__prisioneiro__")
        self.assertEqual(p["protetor_alvo"], "refem_0")
        p["protetor_alvo"] = "refem_1"
        self.assertEqual(r._game_state_payload()["players"][0]["protetor_alvo"], "refem_1")

    async def test_evento_de_dano_usa_a_chave_de_cada_refem(self):
        r = dois_libertos()
        a, b = r.prisoners
        r._combat_damage_events = []
        r._registrar_dano_combate(a, 1, [S.DMG_PHYSICAL])
        r._registrar_dano_combate(b, 1, [S.DMG_PHYSICAL])
        self.assertEqual([e["entity_key"] for e in r._combat_damage_events],
                         ["pr:singleton", "pr:refem_1"])

    async def test_armadilha_marca_o_refem_certo(self):
        r = dois_libertos()
        a, b = r.prisoners
        msgs = []

        async def broadcast(msg, **k):
            msgs.append(msg)
        r.broadcast = broadcast
        await r._avisar_armadilha("mina_terrestre", [4, 3], [a, b])
        await r._avisar_impacto_armadilha("buraco", b, False)
        self.assertEqual(msgs[0]["alvos"], ["refem_0", "refem_1"])
        self.assertEqual((msgs[1]["alvo_id"], msgs[1]["alvo_tipo"]), ("refem_1", "prisioneiro"))

    async def test_efeito_progressivo_acha_o_refem_pelo_id(self):
        r = dois_libertos()
        a, b = r.prisoners
        r.armadilhas = [{"id": "t", "tipo": "armadilha_incendiaria", "pos": [9, 9],
                         "efeitos_ativos": [{"alvo_id": "refem_1", "valor": "1", "elemento": "fogo",
                                             "rodadas_restantes": 1}]}]
        await r._processar_efeitos_armadilha_turno()
        self.assertEqual((a["hp"], b["hp"]), (S.PRIS_HP, S.PRIS_HP - 1))

    async def test_turno_de_cada_refem_liberto(self):
        """Só o liberto ao lado do monstro é ferido; o outro e o cativo ficam intactos."""
        r = sala(mapa(prisoners=[{"pos": [2, 2]}, {"pos": [8, 8]}, {"pos": [8, 2]}]))
        a, b, c = r.prisoners
        a.update(freed=True)
        b.update(freed=True)
        ficha = next(d for d in S.MONSTER_DEFS if d["type"] == "goblin")
        m = S.make_monster(ficha, {"id": 1, "cx": 8, "cy": 7})
        m.update(pos=[8, 7], hp=10, damage="1")
        n = S.make_monster(ficha, {"id": 2, "cx": 8, "cy": 3})
        n.update(pos=[8, 3], hp=10, damage="1")
        r.monsters = {1: m, 2: n}
        with mock.patch.object(S, "d20_attack", lambda *x, **k: (True, 10, 99, False)):
            await r._processar_prisioneiro_turno()
        self.assertEqual((a["hp"], c["hp"]), (S.PRIS_HP, S.PRIS_HP))
        self.assertLess(b["hp"], S.PRIS_HP)

    async def test_refem_preso_no_redemoinho_nao_anda(self):
        """O refém é achado pelo id: sem isso as travas dele não valem."""
        r = dois_libertos()
        a, b = r.prisoners
        b["rodamoinho_preso"] = True
        self.assertFalse(r._tile_livre_para_animado(6, 3, "refem_1", [5, 3]))
        self.assertTrue(r._tile_livre_para_animado(2, 3, "refem_0", [3, 3]))
        a["rodamoinho_preso"] = True
        a["moves_left"] = 6

        async def na_vez(*x):
            return False
        r._is_turn_servos = lambda pid: True
        r._fora_da_vez_do_servo = na_vez
        await r.handle_mover_prisioneiro("p0", -1, 0)
        self.assertEqual(a["pos"], [3, 3])

    async def test_voltar_a_cidade_limpa_cada_refem(self):
        r = dois_libertos()
        for pr in r.prisoners:
            pr["rodamoinho_profundo_preso"] = True
        r._gerar_loja_pergaminhos = lambda: None
        await r._voltar_para_cidade()
        self.assertFalse(any(pr.get("rodamoinho_profundo_preso") for pr in r.prisoners))


def dono_e_janela(prisoners, heroi=(5, 5), **extra):
    """Sala com o herói em `heroi` e o fim do turno sem avançar a iniciativa."""
    r = sala(mapa(prisoners=prisoners, **extra))
    p = r.players["p0"]
    p["pos"] = list(heroi)
    r._is_turn = lambda pid: True

    async def nada(*a, **k):
        pass
    r._advance_initiative = nada
    return r, p


def livres(r, *refens, modo="guiar", dono="p0"):
    for pr in refens:
        pr.update(freed=True, rescuer_pid=dono, rescuer_original=dono, modo=modo)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def com_faixas(r, destino="entrada"):
    r.objectives = {"primary": {"type": "rescue_prisoner", "destino": destino,
                                "faixas": [{"de": 0, "ate": 99}]}, "secondary": []}


class LibertarJanelaSeguirTests(unittest.IsolatedAsyncioTestCase):
    async def test_libertar_escolhe_e_gasta_acao(self):
        r, p = dono_e_janela([{"pos": [4, 5]}, {"pos": [6, 5]}])
        a, b = r.prisoners
        await r.handle_libertar_prisioneiro("p0", "refem_1")
        self.assertTrue(b["freed"])
        self.assertFalse(a["freed"])
        self.assertEqual(b["rescuer_pid"], "p0")
        self.assertTrue(p["action_done"])
        await r.handle_libertar_prisioneiro("p0", "refem_0")
        self.assertFalse(a["freed"])

    async def test_libertar_sem_id_pega_o_adjacente(self):
        r, p = dono_e_janela([{"pos": [9, 9]}, {"pos": [6, 5]}])
        a, b = r.prisoners
        await r.handle_libertar_prisioneiro("p0")
        self.assertTrue(b["freed"])
        self.assertFalse(a["freed"])

    async def test_libertar_longe_recusado(self):
        r, p = dono_e_janela([{"pos": [9, 9]}])
        await r.handle_libertar_prisioneiro("p0", "refem_0")
        self.assertFalse(r.prisoners[0]["freed"])
        self.assertFalse(p["action_done"])

    async def test_janela_so_com_guiados_em_ordem(self):
        r, p = dono_e_janela([{"pos": [2, 2]}, {"pos": [2, 4]}, {"pos": [9, 9]}])
        a, b, c = r.prisoners
        livres(r, a, b)
        livres(r, c, modo="seguir")
        await r.handle_end_turn("p0")
        self.assertEqual(r.animados_phase_pid, "p0")
        self.assertEqual(r._animados_atual("p0"), "refem_0")
        self.assertEqual((a["moves_left"], b["moves_left"]), (6, 6))
        await r.handle_mover_prisioneiro("p0", 1, 0, refem_id="refem_1")
        self.assertEqual(b["pos"], [2, 4])                     # fora da vez
        await r.handle_mover_prisioneiro("p0", 1, 0)           # sem id: o da vez
        self.assertEqual(a["pos"], [3, 2])
        await r.handle_encerrar_animado("p0", "refem_0")
        self.assertEqual(a["moves_left"], 0)
        self.assertEqual(r._animados_atual("p0"), "refem_1")
        await r.handle_mover_prisioneiro_caminho("p0", [[1, 0], [1, 0]], "refem_1")
        self.assertEqual(b["pos"], [4, 4])
        await r.handle_encerrar_animado("p0", "refem_1")
        self.assertIsNone(r.animados_phase_pid)
        self.assertEqual(r.prisioneiros_done, set())

    async def test_cliente_antigo_ve_o_primeiro_como_prisoner(self):
        r, p = dono_e_janela([{"pos": [2, 2]}, {"pos": [2, 4]}])
        a, b = r.prisoners
        livres(r, a, b)
        await r.handle_end_turn("p0")
        est = r._game_state_payload()
        self.assertEqual(est["animados_atual"]["p0"], "prisoner")
        await r.handle_encerrar_animado("p0", "prisoner")      # alias aponta o da vez
        est = r._game_state_payload()
        self.assertEqual(est["animados_atual"]["p0"], "refem_1")
        self.assertEqual(est["animados_done"], ["prisoner"])
        await r.handle_encerrar_animado("p0", "prisoner")
        self.assertIsNone(r.animados_phase_pid)

    async def test_modo_so_do_dono(self):
        r, p = dono_e_janela([{"pos": [2, 2]}])
        pr = r.prisoners[0]
        livres(r, pr)
        r.players["p1"] = S.make_player("p1", "H1", "mage", 1)
        r._is_turn = lambda pid: False
        await r.handle_set_modo_refem("p1", "refem_0", "seguir")
        self.assertEqual(pr["modo"], "guiar")
        await r.handle_set_modo_refem("p0", "refem_0", "inventado")
        self.assertEqual(pr["modo"], "guiar")
        await r.handle_set_modo_refem("p0", "refem_0", "seguir")
        self.assertEqual(pr["modo"], "seguir")
        self.assertFalse(p["action_done"])
        self.assertFalse(p["bonus_action_used"])

    async def test_modo_do_cativo_recusado(self):
        r, p = dono_e_janela([{"pos": [2, 2]}])
        await r.handle_set_modo_refem("p0", "refem_0", "seguir")
        self.assertEqual(r.prisoners[0]["modo"], "guiar")

    async def test_seguir_na_janela_fecha_se_nao_sobra_ninguem(self):
        r, p = dono_e_janela([{"pos": [2, 2]}])
        pr = r.prisoners[0]
        livres(r, pr)
        await r.handle_end_turn("p0")
        self.assertEqual(r.animados_phase_pid, "p0")
        await r.handle_set_modo_refem("p0", "refem_0", "seguir")
        self.assertIsNone(r.animados_phase_pid)

    async def test_voltar_a_guiar_na_janela_nao_da_outra_vez(self):
        """Quem já seguiu neste turno não ganha a vez de andar à mão."""
        r, p = dono_e_janela([{"pos": [2, 2]}, {"pos": [9, 9]}])
        a, b = r.prisoners
        livres(r, a)
        livres(r, b, modo="seguir")
        await r.handle_end_turn("p0")
        await r.handle_set_modo_refem("p0", "refem_1", "guiar")
        await r.handle_encerrar_animado("p0", "refem_0")
        self.assertIsNone(r.animados_phase_pid)

    async def test_seguir_anda_sem_abrir_janela(self):
        r, p = dono_e_janela([{"pos": [1, 5]}], heroi=(5, 5))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        passos = []

        async def broadcast(msg, **k):
            if msg.get("type") == "entity_step":
                passos.append(msg)
        r.broadcast = broadcast
        await r.handle_end_turn("p0")
        self.assertIsNone(r.animados_phase_pid)
        self.assertEqual(cheb(pr["pos"], p["pos"]), 1)
        self.assertEqual(len(passos), 3)
        self.assertEqual({(m["kind"], m["id"]) for m in passos}, {("prisoner", "refem_0")})
        self.assertEqual(passos[-1]["to"], pr["pos"])

    async def test_seguir_limita_a_seis_casas(self):
        r, p = dono_e_janela([{"pos": [0, 5]}], heroi=(10, 5))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        await r.handle_end_turn("p0")
        self.assertEqual(pr["pos"], [6, 5])
        self.assertEqual(pr["moves_left"], 0)

    async def test_seguir_nao_empilha(self):
        r, p = dono_e_janela([{"pos": [1, 4]}, {"pos": [1, 5]}, {"pos": [1, 6]}], heroi=(4, 5))
        livres(r, *r.prisoners, modo="seguir")
        await r.handle_end_turn("p0")
        casas = [tuple(pr["pos"]) for pr in r.prisoners]
        self.assertEqual(len(set(casas)), 3)
        self.assertNotIn(tuple(p["pos"]), casas)
        for pr in r.prisoners:
            self.assertEqual(cheb(pr["pos"], p["pos"]), 1)

    async def test_seguir_em_corredor(self):
        """Corredor de uma casa: os seguidores fazem fila atrás do herói."""
        d = mapa(prisoners=[{"pos": [1, 5]}, {"pos": [2, 5]}, {"pos": [3, 5]}])
        for y in range(12):
            if y != 5:
                d["tiles"][y] = [S.WALL] * 12
        r = sala(d)
        p = r.players["p0"]
        p["pos"] = [10, 5]
        r._is_turn = lambda pid: True

        async def nada(*a, **k):
            pass
        r._advance_initiative = nada
        antes = [list(pr["pos"]) for pr in r.prisoners]
        livres(r, *r.prisoners, modo="seguir")
        await r.handle_end_turn("p0")
        depois = [pr["pos"] for pr in r.prisoners]
        for a, b in zip(antes, depois):
            self.assertGreater(b[0], a[0])
        self.assertEqual(len({tuple(c) for c in depois}), 3)
        self.assertNotIn(p["pos"], depois)
        self.assertEqual(cheb(r.prisoners[2]["pos"], p["pos"]), 1)

    async def test_seguir_sem_caminho_fica_parado(self):
        d = mapa(prisoners=[{"pos": [1, 5]}])
        for y in range(12):
            d["tiles"][y][3] = S.WALL
        r = sala(d)
        p = r.players["p0"]
        p["pos"] = [8, 5]
        r._is_turn = lambda pid: True

        async def nada(*a, **k):
            pass
        r._advance_initiative = nada
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        await r.handle_end_turn("p0")
        self.assertEqual(pr["pos"], [1, 5])
        self.assertIsNone(r.animados_phase_pid)

    async def test_seguir_dispara_armadilha(self):
        r, p = dono_e_janela([{"pos": [1, 5]}], heroi=(5, 5))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        arm = S.make_authored_trap({"tipo": "buraco", "pos": [2, 5]})
        r.armadilhas = [arm]
        disparos = []

        async def disparar(alvo, a):
            disparos.append((alvo, a))
        r._disparar_armadilha = disparar
        await r.handle_end_turn("p0")
        self.assertEqual(len(disparos), 1)
        self.assertIs(disparos[0][0], pr)

    async def test_seguidor_morto_na_armadilha_para(self):
        r, p = dono_e_janela([{"pos": [1, 5]}], heroi=(5, 5))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        r.armadilhas = [S.make_authored_trap({"tipo": "buraco", "pos": [2, 5]})]

        async def disparar(alvo, a):
            await r._prisioneiro_morre(alvo)
        r._disparar_armadilha = disparar
        await r.handle_end_turn("p0")
        self.assertEqual(pr["pos"], [2, 5])

    async def test_chegada_tira_do_mapa(self):
        r, p = dono_e_janela([{"pos": [3, 1]}, {"pos": [9, 9]}], heroi=(8, 8))
        a, b = r.prisoners
        com_faixas(r)
        livres(r, a, b)
        await r.handle_end_turn("p0")
        await r.handle_mover_prisioneiro("p0", -1, 0)          # a escada é (1,1)
        self.assertTrue(a["salvo"])
        self.assertEqual(a["pos"], [-1, -1])
        self.assertEqual(r._refens_no_mapa(), [b])
        self.assertEqual(r._animados_atual("p0"), "refem_1")
        self.assertFalse(tem(r._alvos_na_area(2, 1, 3), a))
        self.assertTrue(r._tile_livre_para_animado(2, 1, "qualquer"))
        self.assertIsNone(r._refem_por_id("refem_0"))
        self.assertIsNone(r._protetor_target("refem_0"))
        hp = a["hp"]
        r.armadilhas = [{"id": "t", "tipo": "armadilha_incendiaria", "pos": [9, 9],
                         "efeitos_ativos": [{"alvo_id": "refem_0", "valor": "1", "elemento": "fogo",
                                             "rodadas_restantes": 1}]}]
        await r._processar_efeitos_armadilha_turno()
        self.assertEqual(a["hp"], hp)

    async def test_chegada_no_modo_seguir_e_na_saida(self):
        r, p = dono_e_janela([{"pos": [6, 5]}], heroi=(10, 10), exit={"x": 9, "y": 9})
        pr = r.prisoners[0]
        com_faixas(r, "saida")
        livres(r, pr, modo="seguir")
        self.assertEqual(r._destino_resgate(), r.exit_pos)
        await r.handle_end_turn("p0")
        self.assertTrue(pr["salvo"])
        self.assertEqual(pr["pos"], [-1, -1])

    async def test_libertar_ao_lado_do_destino_ja_conta(self):
        r, p = dono_e_janela([{"pos": [2, 2]}], heroi=(3, 3))
        com_faixas(r)
        await r.handle_libertar_prisioneiro("p0", "refem_0")
        self.assertTrue(r.prisoners[0]["salvo"])

    async def test_ultima_chegada_fecha_a_janela(self):
        r, p = dono_e_janela([{"pos": [4, 1]}], heroi=(8, 8))
        pr = r.prisoners[0]
        com_faixas(r)
        livres(r, pr)
        await r.handle_end_turn("p0")
        await r.handle_mover_prisioneiro_caminho("p0", [[-1, 0], [-1, 0], [-1, 0]])
        self.assertTrue(pr["salvo"])
        self.assertIsNone(r.animados_phase_pid)

    async def test_mapa_sem_faixas_nao_some(self):
        r, p = dono_e_janela([{"pos": [3, 1]}], heroi=(8, 8))
        pr = r.prisoners[0]
        r.objectives = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
        livres(r, pr)
        await r.handle_end_turn("p0")
        await r.handle_mover_prisioneiro("p0", -1, 0)
        self.assertEqual(pr["pos"], [2, 1])
        self.assertFalse(pr["salvo"])

    def test_destino_padrao_sem_campo(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3]}]))
        r.objectives = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
        self.assertEqual(r._destino_resgate(), r.stairs_pos)
        r.objectives = {"primary": {"type": "rescue_prisoner", "destino": "saida"}, "secondary": []}
        self.assertIsNone(r._destino_resgate())

    async def test_controle_passa_ao_mais_proximo(self):
        r, p = dono_e_janela([{"pos": [1, 5]}], heroi=(10, 10))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        p["alive"] = False
        q = r.players["p1"] = S.make_player("p1", "H1", "mage", 1)
        q.update(alive=True, pos=[5, 5])
        await r.handle_end_turn("p1")
        self.assertEqual(pr["rescuer_pid"], "p1")
        self.assertEqual(cheb(pr["pos"], q["pos"]), 1)

    async def test_solo_grupo_refem_do_extra(self):
        r, p = dono_e_janela([{"pos": [2, 2]}, {"pos": [9, 2]}])
        a, b = r.prisoners
        x = r.players["x1"] = S.make_player("x1", "Extra", "mage", 1)
        x.update(alive=True, pos=[3, 2], controlador="p0")
        await r.handle_libertar_prisioneiro("x1", "refem_0")
        self.assertEqual(a["rescuer_pid"], "x1")
        await r.handle_end_turn("p0")                          # não é dele: nada abre
        self.assertIsNone(r.animados_phase_pid)
        await r.handle_end_turn("x1")
        self.assertEqual(r.animados_phase_pid, "x1")
        self.assertEqual(r._animados_atual("x1"), "refem_0")
        await r.handle_set_modo_refem("x1", "refem_0", "seguir")
        self.assertIsNone(r.animados_phase_pid)
        x["pos"] = [8, 8]
        await r.handle_end_turn("x1")
        self.assertEqual(a["moves_left"], 0)
        self.assertEqual(cheb(a["pos"], x["pos"]), 1)

    async def test_refem_de_treino_nao_troca_de_modo(self):
        r, p = dono_e_janela([{"pos": [2, 2]}])
        pr = r.prisoners[0]
        livres(r, pr)
        pr["training_refem"] = True
        await r.handle_set_modo_refem("p0", "refem_0", "seguir")
        self.assertEqual(pr["modo"], "guiar")

    async def test_turno_nao_processa_refem_que_morreu_no_laco(self):
        r = dois_libertos()
        a, b = r.prisoners
        vistos = []

        async def turno(pr):
            vistos.append(pr)
            b["alive"] = False
        r._processar_turno_do_refem = turno
        await r._processar_prisioneiro_turno()
        self.assertEqual(vistos, [a])

    async def test_seguir_nao_atravessa_objeto_solido(self):
        r, p = dono_e_janela([{"pos": [1, 5]}], heroi=(5, 5))
        pr = r.prisoners[0]
        livres(r, pr, modo="seguir")
        r._decor_block_tiles = {(3, y) for y in range(12)}
        await r.handle_end_turn("p0")
        self.assertEqual(pr["pos"], [1, 5])

    async def test_mensagens_passam_pelo_handler(self):
        """`refem_id` e `set_modo_refem` chegam aos handlers pelo laço de conexão real."""
        asyncio.get_running_loop().slow_callback_duration = 5   # o laço real é lento em modo debug
        salas = {}

        def preparar():
            r = next(x for x in S.rooms.values() if "Refem" in [p["name"] for p in x.players.values()])
            salas["r"] = r
            p = next(iter(r.players.values()))
            p.update(class_id="warrior", alive=True)
            r.load_authored_dungeon(mapa(prisoners=[{"pos": [4, 5]}, {"pos": [6, 5]}]))
            r.phase = "playing"
            p["pos"] = [5, 5]
            r._is_turn = lambda pid: True
            return {"type": "libertar_prisioneiro", "refem_id": "refem_1"}

        ws = FakeWS([{"type": "create_room", "name": "Refem"}, preparar,
                     {"type": "set_modo_refem", "refem_id": "refem_1", "modo": "seguir"}])
        await S.handler(ws)
        a, b = salas["r"].prisoners
        self.assertFalse(a["freed"])
        self.assertTrue(b["freed"])
        self.assertEqual(b["modo"], "seguir")
        self.assertEqual(ws.erros(), [])


# Tabela dos Charcos (spec): salvas → (renome, xp, ouro, fato).
FAIXAS_CHARCOS = [
    {"de": 6, "ate": 6, "renome": 8, "xp": 225, "gold": 90, "fato": "charcos_criancas_todas"},
    {"de": 4, "ate": 5, "renome": 5, "xp": 150, "gold": 60, "fato": "charcos_criancas_salvas"},
    {"de": 3, "ate": 3, "renome": 0, "xp": 90, "gold": 36, "fato": "charcos_criancas_perdidas"},
    {"de": 2, "ate": 2, "renome": -2, "xp": 60, "gold": 24, "fato": "charcos_criancas_perdidas"},
    {"de": 1, "ate": 1, "renome": -4, "xp": 30, "gold": 12, "fato": "charcos_criancas_perdidas"},
    {"de": 0, "ate": 0, "renome": -8, "xp": 0, "gold": 0, "fato": "charcos_criancas_mortas"},
]
ESPERADO = {6: (8, 225, 90, "charcos_criancas_todas"), 5: (5, 150, 60, "charcos_criancas_salvas"),
            4: (5, 150, 60, "charcos_criancas_salvas"), 3: (0, 90, 36, "charcos_criancas_perdidas"),
            2: (-2, 60, 24, "charcos_criancas_perdidas"), 1: (-4, 30, 12, "charcos_criancas_perdidas"),
            0: (-8, 0, 0, "charcos_criancas_mortas")}
SEIS = [{"pos": [2 + i, 6]} for i in range(6)]


def objetivo_charcos(**extra):
    prim = {"type": "rescue_prisoner", "destino": "entrada", "meta": 4,
            "faixas": copy.deepcopy(FAIXAS_CHARCOS)}
    prim.update(extra)
    return {"primary": prim, "secondary": []}


def resgate(secundarios=()):
    r = sala(mapa(prisoners=copy.deepcopy(SEIS), objectives=objetivo_charcos()))
    r.objectives["secondary"] = list(secundarios)
    r.renome = 10
    r.fim = False

    async def fim(*a, **k):
        r.fim = True
    r.end_game = fim
    return r


def salvar(r, n, mortos=0):
    for pr in r.prisoners[:n]:
        pr.update(freed=True, salvo=True, pos=[-1, -1])
    for pr in r.prisoners[n:n + mortos]:
        pr["alive"] = False


def goblin_alvo(hp):
    ficha = next(d for d in S.MONSTER_DEFS if d["type"] == "goblin")
    m = S.make_monster(ficha, {"id": 1, "cx": 9, "cy": 9})
    m.update(pos=[9, 9], hp=hp, authored_target=True)
    return m


class FaixasTests(unittest.IsolatedAsyncioTestCase):
    async def test_faixas_pagam_o_valor_certo(self):
        for n in range(7):
            with self.subTest(salvos=n):
                r = resgate()
                p = r.players["p0"]
                salvar(r, n, mortos=6 - n)
                await r._check_objectives()
                self.assertTrue(r.mission_complete_pending)
                xp, ouro = p["xp"], p.get("gold", 0)
                await r.handle_encerrar_missao("p0")
                renome, dxp, dgold, fato = ESPERADO[n]
                self.assertEqual(p["xp"] - xp, dxp)
                self.assertEqual(p.get("gold", 0) - ouro, dgold)
                self.assertEqual(r.renome, 10 + renome)
                self.assertIn(fato, r.fatos)
                self.assertTrue(r.fim)

    async def test_botao_na_meta(self):
        r = resgate()
        p = r.players["p0"]
        ouro, xp = p.get("gold", 0), p["xp"]
        salvar(r, 3)
        await r._check_objectives()
        self.assertFalse(r.mission_complete_pending)
        salvar(r, 4)
        await r._check_objectives()
        self.assertTrue(r.mission_complete_pending)
        self.assertEqual((p.get("gold", 0), p["xp"]), (ouro, xp))
        self.assertEqual(r.renome, 10)
        self.assertEqual(r.fatos, set())

    async def test_quinta_depois_da_meta_conta(self):
        r = resgate()
        p = r.players["p0"]
        salvar(r, 4)
        await r._check_objectives()
        salvar(r, 6)
        await r._check_objectives()
        xp = p["xp"]
        await r.handle_encerrar_missao("p0")
        self.assertEqual(p["xp"] - xp, 225)
        self.assertIn("charcos_criancas_todas", r.fatos)

    async def test_sem_vivos_no_mapa_abre_encerrar(self):
        r = resgate()
        p = r.players["p0"]
        salvar(r, 2, mortos=4)
        await r._check_objectives()
        self.assertTrue(r.mission_complete_pending)
        xp = p["xp"]
        await r.handle_encerrar_missao("p0")
        self.assertEqual(p["xp"] - xp, 60)
        self.assertEqual(r.renome, 8)

    async def test_morte_nao_falha_o_resgate(self):
        r = sala(mapa(prisoners=copy.deepcopy(SEIS),
                      objectives=objetivo_charcos(se_falhar={"renome": -5, "fato": "falhou"})))
        r.renome = 10
        await r._prisioneiro_morre(r.prisoners[2])
        self.assertFalse(r.prisoners[2]["alive"])
        self.assertFalse(r.rescue_failed)
        self.assertEqual(r.renome, 10)
        self.assertNotIn("falhou", r.fatos)
        self.assertEqual(r._objetivo_payload(r.objectives["primary"])["status"], "pending")

    async def test_secundario_depois_da_meta(self):
        ferrao = {"type": "kill_target", "xp": 0,
                  "reward": {"gold": 25, "items": [{"id": "health_potion"}]}}
        r = resgate([ferrao])
        p = r.players["p0"]
        m = goblin_alvo(10)
        r.monsters = {m["id"]: m}
        salvar(r, 4)
        await r._check_objectives()
        ouro, baus = p.get("gold", 0), len(r.chests)
        m["hp"] = 0
        await r._check_objectives()
        self.assertEqual(p.get("gold", 0) - ouro, 25)
        self.assertEqual(len(r.chests), baus + 1)
        self.assertEqual(r._secundarios_pagos, {0})
        await r._check_objectives()
        self.assertEqual(p.get("gold", 0) - ouro, 25)
        self.assertEqual(len(r.chests), baus + 1)
        await r.handle_encerrar_missao("p0")
        self.assertEqual(p.get("gold", 0) - ouro, 25 + 60)

    async def test_secundario_antes_da_meta(self):
        r = resgate([{"type": "kill_all", "reward": {"gold": 7}}])
        p = r.players["p0"]
        ouro = p.get("gold", 0)
        await r._check_objectives()
        self.assertEqual(p.get("gold", 0) - ouro, 7)
        self.assertFalse(r.mission_complete_pending)

    async def test_renome_negativo_tem_piso_zero(self):
        r = resgate()
        r.renome = 3
        salvar(r, 0, mortos=6)
        await r._check_objectives()
        await r.handle_encerrar_missao("p0")
        self.assertEqual(r.renome, 0)
        self.assertIn("charcos_criancas_mortas", r.fatos)

    async def test_encerrar_paga_uma_vez(self):
        r = resgate()
        p = r.players["p0"]
        salvar(r, 4)
        await r._check_objectives()
        xp = p["xp"]
        await r.handle_encerrar_missao("p0")
        await r.handle_encerrar_missao("p0")
        self.assertEqual(p["xp"] - xp, 150)

    def test_contagem_no_game_state(self):
        r = resgate()
        salvar(r, 2, mortos=1)
        esperado = {"salvos": 2, "mortos": 1, "total": 6, "meta": 4, "destino": "entrada"}
        self.assertEqual(r._resgate_contagem(), esperado)
        self.assertEqual(r._game_state_payload()["resgate"], esperado)
        self.assertEqual(r._faixa_atual()["xp"], 60)
        sem = sala(mapa(prisoners=[{"pos": [3, 3]}],
                        objectives={"primary": {"type": "rescue_prisoner"}, "secondary": []}))
        self.assertIsNone(sem._game_state_payload()["resgate"])

    def test_validador_de_faixas(self):
        tres = [{"pos": [3, 3]}, {"pos": [4, 3]}, {"pos": [5, 3]}]

        def obj(faixas, **extra):
            prim = {"type": "rescue_prisoner", "meta": 2, "faixas": faixas}
            prim.update(extra)
            return {"primary": prim, "secondary": []}
        bom = [{"de": 0, "ate": 1, "xp": 0},
               {"de": 2, "ate": 3, "xp": 10, "gold": 5, "renome": -1, "fato": "x"}]
        ok, msg = S.validar_dungeon(mapa(prisoners=tres, objectives=obj(bom)))
        self.assertTrue(ok, msg)
        ok, msg = S.validar_dungeon(mapa(prisoners=tres, objectives=obj(bom, destino="entrada")))
        self.assertTrue(ok, msg)
        ok, msg = S.validar_dungeon(mapa(prisoners=tres, objectives=obj(bom, destino="saida"),
                                         exit={"x": 9, "y": 9}))
        self.assertTrue(ok, msg)
        ruins = {
            "buraco": obj([{"de": 0, "ate": 0}, {"de": 2, "ate": 3}]),
            "sobreposição": obj([{"de": 0, "ate": 2}, {"de": 2, "ate": 3}]),
            "falta o topo": obj([{"de": 0, "ate": 2}]),
            "passa do total": obj([{"de": 0, "ate": 4}]),
            "meta > total": obj(bom, meta=4),
            "meta zero": obj(bom, meta=0),
            "vazia": obj([]),
            "faixa não é objeto": obj(["x"]),
            "de > ate": obj([{"de": 3, "ate": 0}]),
            "xp negativo": obj([{"de": 0, "ate": 3, "xp": -1}]),
            "destino sem exit": obj(bom, destino="saida"),
            "destino inventado": obj(bom, destino="lua"),
            "2 reféns sem faixas": {"primary": {"type": "rescue_prisoner"}, "secondary": []},
            "2 reféns e kill_all": {"primary": {"type": "kill_all"}, "secondary": []},
        }
        for nome, objetivos in ruins.items():
            with self.subTest(nome):
                ok, _ = S.validar_dungeon(mapa(prisoners=tres, objectives=objetivos))
                self.assertFalse(ok)
        um = mapa(prisoner={"pos": [3, 3]},
                  objectives={"primary": {"type": "rescue_prisoner"}, "secondary": []})
        self.assertTrue(S.validar_dungeon(um)[0])

    async def test_foto_com_salvos(self):
        ferrao = {"type": "kill_target", "reward": {"gold": 25}}
        r = resgate([ferrao])
        m = goblin_alvo(0)
        r.monsters = {m["id"]: m}
        salvar(r, 4, mortos=1)
        await r._check_objectives()
        self.assertEqual(r._secundarios_pagos, {0})
        corpo = S.foto_desempacotar(S.foto_empacotar(r._montar_foto(), onde="masmorra"))
        r2 = resgate([ferrao])
        r2._foto_aplicar_sala(corpo, {"warrior": "p0"}, r2.dungeon_def)
        self.assertEqual(r2._resgate_contagem(), r._resgate_contagem())
        self.assertEqual(r2._secundarios_pagos, {0})
        p2 = r2.players["p0"]
        ouro = p2.get("gold", 0)
        await r2._check_objectives()
        self.assertEqual(p2.get("gold", 0), ouro)
        self.assertTrue(r2.mission_complete_pending)
        xp = p2["xp"]
        await r2.handle_encerrar_missao("p0")
        self.assertEqual(p2["xp"] - xp, 150)
        self.assertEqual(p2.get("gold", 0) - ouro, 60)


if __name__ == "__main__":
    unittest.main()
