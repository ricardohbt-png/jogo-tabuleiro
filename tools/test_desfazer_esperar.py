"""Desfazer movimento e Esperar (spec 2026-11-25-desfazer-esperar)."""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []
def check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond: FALHAS.append(name)

async def nada(*a, **k): return None
def run(c): return asyncio.run(c)


def sala(n_herois=3, explorada=True):
    r = S.GameRoom("TURNO")
    r.errs = []
    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r.errs.append(msg)
    r.gm_say = nada; r.push_state = nada; r.send_to = cap; r.broadcast = nada
    r._broadcast_dado = nada; r.broadcast_city_state = nada
    r.phase = "playing"; r.map_w = r.map_h = 16
    r.tiles = [[S.FLOOR] * 16 for _ in range(16)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 16, "h": 16, "cx": 8, "cy": 8, "locked": False, "doors": [], "cleared": True, "role": "normal", "looted": True}]
    r.round_num = 1
    r.player_order = []
    for i in range(n_herois):
        pid = f"p{i+1}"
        p = S.make_player(pid, f"H{i+1}", "warrior", i)
        p["pos"] = [2 + i * 3, 2]; p["hp"] = p["max_hp"] = 100; p["alive"] = True; p["connected"] = True
        p["moves_left"] = 6; p["fome"] = 80; p["sede"] = 80
        r.players[pid] = p; r.player_order.append(pid); r.connections[pid] = object()
    r.initiative_active = True
    r._rebuild_initiative()
    # p1 age primeiro (ordem fixa para o teste)
    r.initiative_order.sort(key=lambda e: e["id"])
    r.initiative_index = 0
    if explorada:
        r.explored = {(x, y) for x in range(16) for y in range(16)}
    return r


def pode(r, pid="p1"):
    return r._pode_desfazer(r.players[pid])


def main():
    print("\n[1] Desfazer um comando de movimento")
    r = sala(); p = r.players["p1"]
    antes = {k: p[k] for k in ("pos", "moves_left", "fome", "sede")}
    antes["facing"] = p.get("facing")
    run(r.handle_move_path("p1", [[1, 0], [1, 0], [0, 1]]))
    check("andou", p["pos"] == [4, 3] and p["moves_left"] == 3)
    check("pode desfazer depois de andar", pode(r))
    run(r.handle_desfazer_movimento("p1"))
    check("volta à posição, movimento, fome, sede e direção de antes",
          p["pos"] == antes["pos"] and p["moves_left"] == antes["moves_left"]
          and p["fome"] == antes["fome"] and p["sede"] == antes["sede"] and p.get("facing") == antes["facing"])
    check("nada a desfazer depois", not pode(r))
    run(r.handle_desfazer_movimento("p1")); check("desfazer sem nada que desfazer não muda e responde erro", p["pos"] == antes["pos"] and bool(r.errs))

    print("\n[2] Vários comandos voltam na ordem inversa")
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0], [1, 0]]))
    run(r.handle_move_path("p1", [[0, 1], [0, 1]]))
    check("dois comandos: pos final [4,4]", p["pos"] == [4, 4])
    run(r.handle_desfazer_movimento("p1")); check("1º desfazer volta ao fim do 1º comando", p["pos"] == [4, 2])
    run(r.handle_desfazer_movimento("p1")); check("2º desfazer volta ao início do turno", p["pos"] == [2, 2] and p["moves_left"] == 6)
    check("3º não há", not pode(r))
    r = sala(); p = r.players["p1"]
    run(r.handle_move("p1", 1, 0)); run(r.handle_move("p1", 1, 0))
    run(r.handle_desfazer_movimento("p1")); run(r.handle_desfazer_movimento("p1"))
    check("passo a passo (move) também desfaz", p["pos"] == [2, 2] and p["moves_left"] == 6)

    print("\n[3] Bloqueios: tudo o que torna o movimento irreversível")
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]])); p["action_done"] = True
    check("depois de gastar a ação principal", not pode(r))
    run(r.handle_desfazer_movimento("p1")); check("e o servidor recusa sem mudar nada", p["pos"] == [3, 2])
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]])); p["bonus_action_used"] = True
    check("depois de gastar a ação bônus", not pode(r))
    r = sala(explorada=False); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    check("movimento que revelou névoa nova não se desfaz", not pode(r))
    r = sala(); p = r.players["p1"]
    original = r._aplicar_lava_se_pisar
    async def dano(pp, *a, **k):
        pp["hp"] -= 5
    r._aplicar_lava_se_pisar = dano
    run(r.handle_move_path("p1", [[1, 0]]))
    check("movimento que causou dano (armadilha/lava) não se desfaz", not pode(r))
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    p["bag"].append({"id": "x", "name": "Item"})
    check("depois de mexer na bolsa", not pode(r))
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    r.rooms[0]["locked"] = True
    check("mundo mudou (sala trancada → aberta/fechada)", not pode(r))
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    r.monsters["m"] = {"id": "m", "type": "goblin", "pos": [9, 9], "hp": 5, "alertado": True}
    check("um monstro foi alertado", not pode(r))

    print("\n[4] Quem pode e quando")
    r = sala(); p2 = r.players["p2"]
    run(r.handle_move_path("p2", [[1, 0]]))
    check("fora da minha vez não desfaz", p2["pos"] == [5, 2] and not r._pode_desfazer(p2))
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    p["alive"] = False
    check("herói morto não desfaz", not pode(r))
    r = sala(); p = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    run(r.handle_end_turn("p1"))
    check("o fim do turno apaga os pontos de retorno", r._desfazer_pilhas.get("p1", []) == [])

    print("\n[5] Esperar")
    r = sala(); p1 = r.players["p1"]
    check("no começo da vez pode esperar", r._pode_esperar(p1))
    run(r.handle_esperar_vez("p1"))
    ordem = [e["id"] for e in r.initiative_order]
    check(f"p1 foi para o fim da fila {ordem}", ordem == ["p2", "p3", "p1"])
    check("a vez passa a p2", r.current_pid() == "p2")
    check("p1 não pode esperar de novo na mesma rodada", p1.get("esperou_rodada") == 1 and not r._pode_esperar(p1))
    r = sala(); p1 = r.players["p1"]
    run(r.handle_move_path("p1", [[1, 0]]))
    check("depois de andar não pode esperar", not r._pode_esperar(p1))
    r = sala(); p1 = r.players["p1"]; p1["action_done"] = True
    check("depois de agir não pode esperar", not r._pode_esperar(p1))
    r = sala(); r.initiative_index = 2
    check("o último a agir não tem como esperar", not r._pode_esperar(r.players["p3"]))
    run(r.handle_esperar_vez("p3")); check("e o servidor recusa sem mudar a fila", [e["id"] for e in r.initiative_order] == ["p1", "p2", "p3"])
    r = sala()
    check("fora da vez não pode esperar", not r._pode_esperar(r.players["p2"]))

    print("\n[6] A vez que volta não repete o preparo de início de turno")
    r = sala(); chamadas = []
    original = r._start_initiative_player_turn
    async def conta(pp):
        chamadas.append(pp["id"]); return await original(pp)
    r._start_initiative_player_turn = conta
    run(r._activate_initiative_actor())                 # p1 abre a vez
    run(r.handle_esperar_vez("p1"))                     # p2 abre a vez
    run(r.handle_end_turn("p2"))
    run(r.handle_end_turn("p3"))                        # volta p1 (retomada)
    check(f"p1 só rodou o preparo uma vez {chamadas}", chamadas.count("p1") == 1)
    check("p1 é o ator de novo, com o movimento cheio", r.current_pid() == "p1" and r.players["p1"]["moves_left"] == 6)
    check("a rodada ainda é a 1", r.round_num == 1)

    print("\n[7] O game_state informa os botões")
    r = sala()
    snap = r._game_state_payload()
    j = next(pp for pp in snap["players"] if pp["id"] == "p1")
    check("pode_esperar verdadeiro e pode_desfazer falso no início da vez", j["pode_esperar"] is True and j["pode_desfazer"] is False)
    run(r.handle_move_path("p1", [[1, 0]]))
    j = next(pp for pp in r._game_state_payload()["players"] if pp["id"] == "p1")
    check("depois de andar: pode_desfazer verdadeiro e pode_esperar falso", j["pode_desfazer"] is True and j["pode_esperar"] is False)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
