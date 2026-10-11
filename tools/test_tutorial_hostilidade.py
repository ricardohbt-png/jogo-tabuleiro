"""Fatia 18: a ala 46-48 do Campo de Treinamento (hostilidade entre monstros) e a integração com a trilha comum."""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as S
import gerar_guia_comum as G
D = S.carregar_dungeon("campo_de_treinamento.json")

ID = "fala_hostilidade"
PORTA = [33, 15]
SALAS = {r["id"]: r for r in D["rooms"]}
FALAS = {f["id"]: f for f in D["falas"]}
# salas ORIGINAIS: nenhuma pode ter se mexido quando a ala da hostilidade entrou
ORIGINAIS = {18: (1, 13, 6, 6), 19: (13, 13, 6, 6), 20: (20, 13, 6, 6), 21: (27, 13, 6, 6),
             35: (31, 4, 7, 5), 38: (32, 23, 7, 5), 40: (19, 1, 6, 6), 41: (21, 22, 6, 6),
             42: (8, 5, 6, 6), 43: (9, 21, 6, 6)}


def sala_de(pos):
    return next(r for r in D["rooms"] if r["x"] <= pos[0] < r["x"] + r["w"] and r["y"] <= pos[1] < r["y"] + r["h"])


class LayoutTests(unittest.TestCase):
    def test_salas_originais_nao_se_mexeram(self):
        for rid, (x, y, w, h) in ORIGINAIS.items():
            r = SALAS[rid]
            self.assertEqual((r["x"], r["y"], r["w"], r["h"]), (x, y, w, h), rid)

    def test_ala_46_47_48_e_a_saida(self):
        self.assertEqual([SALAS[i]["x"] for i in (46, 47, 48)], [34, 41, 48])
        self.assertEqual([SALAS[i]["doors"] for i in (46, 47)], [[PORTA], [[40, 15]]])
        self.assertEqual(SALAS[48]["doors"], [[47, 15], [51, 19]])
        self.assertEqual(D["exit"], {"x": 51, "y": 24})
        self.assertEqual(S.validar_dungeon(D), (True, "ok"))
        for rid in (46, 47, 48):
            self.assertTrue(SALAS[rid]["locked"])

    def test_porta_de_cada_sala_da_ala_e_porta_no_mapa(self):
        for rid in (46, 47, 48):
            x, y = SALAS[rid]["doors"][0]
            self.assertEqual(D["tiles"][y][x], 2)

    def test_conteudo_da_ala(self):
        tipos_de = lambda rid: sorted(m["type"] for m in D["monsters"] if m["room_id"] == rid)
        self.assertEqual(tipos_de(46), ["escorpiao_pedra", "esqueleto_animal", "rato_gigante"])
        self.assertEqual(sum(t == "boneco_palha" for t in tipos_de(47)), 2)
        self.assertEqual(sum(t == "boneco_treino_veneno" for t in tipos_de(47)), 3)
        self.assertEqual(tipos_de(48), ["boneco_treino"])
        baus = {tuple(c["pos"]): [i["id"] for i in c["items"]] for c in D["chests"]}
        self.assertEqual(baus[(35, 16)], ["granada_superior"])
        self.assertEqual(sala_de([35, 16])["id"], 46)
        self.assertEqual(baus[(49, 17)], ["cajado_madeira"])
        self.assertEqual(sala_de([49, 17])["id"], 48)

    def test_lutadores_hostis_a_todos(self):
        for m in D["monsters"]:
            if m["room_id"] == 46 and m.get("autonomous_hostility"):
                self.assertEqual(m["hostility_override"]["rules"]["all_monsters"], True)
                self.assertTrue(m["autonomous_hostility"])

    def test_ordens_comuns_unicas_e_hostilidade_esta_na_trilha(self):
        comuns = [f for f in D["falas"] if f.get("ordem") is not None and not f.get("classe")]
        ordens = [f["ordem"] for f in comuns]
        self.assertEqual(len(ordens), len(set(ordens)))
        self.assertIn(FALAS[ID]["ordem"], ordens)

    def test_licao_nasce_na_sala_vizinha_da_porta(self):
        # lição plantada numa sala só dispara com o herói nela: dentro da 46 a porta já estaria aberta
        f = FALAS[ID]
        self.assertEqual(sala_de(f["pos"])["id"], 21)
        self.assertLessEqual(max(abs(f["pos"][0] - PORTA[0]), abs(f["pos"][1] - PORTA[1])), 1)
        self.assertEqual(f["guia"][0]["conclui_com"], {"tipo": "abrir_porta", "alvo": PORTA})
        self.assertEqual(f["tarefa"]["alvo"], "granada_superior")

    def test_verbo_ja_existe_no_servidor_e_o_guia_guia_ate_a_granada(self):
        self.assertIn(FALAS[ID]["tarefa"]["tipo"], S.LICAO_VERBOS)
        passos = G.guia_todos()[ID]
        self.assertEqual([p["id"] for p in passos], [
            "abrir", "observar", "usar", "enfraquecer", "granada", "sobreviventes", "parabens"])
        self.assertEqual(passos[2]["conclui"], {"tipo": "encerrar_turno"})
        self.assertEqual(passos[3]["conclui"], {"tipo": "encerrar_turno"})
        self.assertEqual(passos[4]["conclui"], {"tipo": "arremessar_item", "alvo": "granada_superior"})
        self.assertEqual(FALAS[ID]["tarefa"].get("requer_sala_limpa"), 46)


async def _sala(cls="warrior"):
    r = S.GameRoom("HOST_" + cls)
    p = S.make_player("hero", "Aluno", cls, 0)
    r.players[p["id"]] = p
    r.player_order = [p["id"]]
    r.load_authored_dungeon(deepcopy(D))
    r.phase = "playing"
    r.msgs = []

    async def send(pid, msg):
        r.msgs.append(msg)

    async def bc(msg, **k):
        r.msgs.append(msg)

    async def noop(*a, **k):
        pass
    r.send_to = send
    r.broadcast = bc
    r.gm_say = noop
    r._intro_masmorra_bloqueada = lambda: False
    r._rebuild_initiative()
    r.initiative_active = True
    # a fila real pula monstro dormente; aqui ninguém a roda, então a vez começa no herói
    r.initiative_index = next(i for i, a in enumerate(r.initiative_order) if a["id"] == p["id"])
    feitas = [f["id"] for f in r.licoes if not f.get("classe") and f["ordem"] < FALAS[ID]["ordem"]]
    p["licoes_feitas"] = feitas
    p["licao_progresso"] = {i: 1 for i in feitas}
    p["pos"] = [28, 15]
    p["moves_left"] = 6
    return r, p


def tipos(r, t):
    return [m for m in r.msgs if m.get("type") == t]


class FluxoTests(unittest.IsolatedAsyncioTestCase):
    async def test_dispara_antes_da_porta_e_o_passo_abrir_recebe_o_evento(self):
        r, p = await _sala()
        await r.handle_move(p["id"], 1, 0)                           # 28 -> 29, ainda na sala 21
        self.assertEqual(p["licao_atual"], ID)
        self.assertEqual(p["licao_passo"], 0)
        self.assertNotIn(tuple(PORTA), r.opened_doors)
        r.msgs.clear()
        p["pos"] = [32, 15]
        await r.handle_open_door(p["id"], *PORTA)
        self.assertEqual(p["licao_passo"], 1, "abrir a porta avança o passo 1")
        self.assertTrue(tipos(r, "licao_passo_ok"))
        await r.handle_avancar_passo(p["id"])                        # observar cuidadosamente
        self.assertEqual(p["licao_passo"], 2)
        r.msgs.clear()
        await r._licao_evento(p, "encerrar_turno")
        self.assertEqual(p["licao_passo"], 3, "primeiro fim de turno deixa os monstros começarem a luta")
        await r._licao_evento(p, "encerrar_turno")
        self.assertEqual(p["licao_passo"], 4, "granada aparece após um ciclo para observar os PV")
        self.assertTrue(tipos(r, "licao_passo"))
        self.assertEqual(sum(m["hp"] for m in r.monsters.values() if m.get("room_id") == 46),
                         sum(m["max_hp"] for m in r.monsters.values() if m.get("room_id") == 46),
                         "a instrução da granada aparece antes da primeira luta dos monstros")
        await r.handle_avancar_passo(p["id"])
        self.assertEqual(p["licao_passo"], 4, "o passo da granada só avança ao arremessá-la")
        self.assertEqual(p["licao_atual"], ID)

    async def test_granada_avanca_para_sobreviventes_e_so_conclui_ao_limpar_a_sala(self):
        r, p = await _sala()
        await r.handle_move(p["id"], 1, 0)
        p["pos"] = [34, 15]
        p["action_done"] = False
        p["licao_atual"] = ID
        p["licao_passo"] = 4
        p["bag"].append({"id": "granada_superior", "name": "Granada Superior", "emoji": "💥",
                         "item_slot": "bag", "effect": "throwable"})
        # Mantém um sobrevivente para provar que o objetivo não conclui com o arremesso.
        vivos_antes = [m for m in r.monsters.values() if m.get("room_id") == 46]
        for m in vivos_antes:
            m["max_hp"] = 500
            m["hp"] = 500
        await r.handle_throw_item(p["id"], {"item_id": "granada_superior", "tx": 38, "ty": 15})
        vivos = [m for m in r.monsters.values() if m.get("room_id") == 46 and m.get("hp", 0) > 0]
        self.assertTrue(vivos, "o teste precisa manter sobrevivente após a granada")
        self.assertEqual(p["licao_atual"], ID)
        self.assertEqual(p["licao_passo"], 5)
        self.assertNotIn(ID, p["licoes_feitas"])
        # A morte final dispara o parabéns e a conclusão da missão.
        for m in vivos:
            m["hp"] = 0
            await r._monster_dies(m, None, force=True)
        self.assertIn(ID, p["licoes_feitas"])
        self.assertIn(ID, p["tutorial_history"])
        self.assertEqual(p["licao_passo"], 0)
        passo_final = [m for m in r.msgs if m.get("type") == "licao_passo"][-1]
        self.assertEqual(passo_final["passo"]["id"], "parabens")
        self.assertEqual(len(tipos(r, "licao_concluida")), 1)
        p["pos"] = [43, 15]
        p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_29")
        self.assertEqual(p.get("licoes_puladas", []), [])

    async def test_seguir_para_a_sala_47_sem_terminar_nao_trava(self):
        r, p = await _sala()
        await r.handle_move(p["id"], 1, 0)
        self.assertEqual(p["licao_atual"], ID)
        p["pos"] = [43, 15]
        p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertIn(ID, p["licoes_puladas"])
        self.assertEqual(p["licao_atual"], "fala_29")

    async def test_abrir_a_porta_acorda_os_lutadores_e_eles_se_atacam(self):
        r, p = await _sala()
        await r.handle_move(p["id"], 1, 0)
        p["pos"] = [32, 15]
        await r.handle_open_door(p["id"], *PORTA)
        lutadores = [m for m in r.monsters.values()
                     if m["room_id"] == 46 and m.get("autonomous_hostility")]
        self.assertTrue(all(m["alertado"] and m["control_mode"] == "auto" for m in lutadores))
        antes = sum(m["hp"] for m in lutadores)
        for _ in range(4):
            await r.handle_end_turn(p["id"])
            for _ in range(300):
                if r.current_pid() == p["id"]:
                    break
                await asyncio.sleep(0.02)
        self.assertLess(sum(m["hp"] for m in lutadores), antes,
                        "os monstros hostis entre si se feriram sem o herói chegar perto")


if __name__ == "__main__":
    unittest.main()
