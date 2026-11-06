"""Lista de reféns por mapa, com compatibilidade com o refém único."""
import ast
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
        ok, _ = S.validar_dungeon(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [4, 3]}]))
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
    # Janela de movimento e libertar: saem na Task 3.
    ("server.py", "_animados_atual"),
    ("server.py", "_zerar_turno_da_peca"),
    ("server.py", "handle_encerrar_animado"),
    ("server.py", "handle_end_turn"),
    ("server.py", "handle_libertar_prisioneiro"),
    ("server.py", "handle_mover_prisioneiro_caminho"),
    ("server.py", "handle_mover_prisioneiro"),
    # Objetivo de resgate: sai na Task 4.
    ("server.py", "_objetivo_cumprido"),
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


if __name__ == "__main__":
    unittest.main()
