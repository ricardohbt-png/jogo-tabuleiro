"""Modo Mestre Jogador — Fase A. Roda da raiz: python tools/test_modo_mestre.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

class FakeWS:
    """WebSocket falso: .send é um no-op assíncrono (add_player usa ws.send no reject)."""
    async def send(self, *a, **k): pass

def lobby_room():
    """Sala em fase de lobby com send_to/broadcast capturados."""
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_lobby = noop; r.broadcast_city_state = noop; r.send_to = cap_send
    r._errs = errs
    r.phase = "lobby"
    return r

def playing_room_com_mestre():
    """Sala em fase 'playing' com um mestre conectado e mapa mínimo."""
    r = lobby_room()
    r.phase = "playing"
    r.master_pid = "m1"; r.master_name = "Mestre"
    r.connections["m1"] = object()   # mestre conectado → _mestre_ativo() True
    r.map_w = 10; r.map_h = 10
    r.tiles = [[S.FLOOR]*10 for _ in range(10)]
    r.rooms = []
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    return r

async def add(r, pid, name):
    """Adiciona um jogador sem depender de websocket real."""
    r.connections[pid] = object()   # sentinela: 'conectado'
    r.players[pid] = {"id": pid, "name": name, "class_id": None,
                      "ready": False, "connected": True, "slot": len(r.players)}
    if not r.host_pid: r.host_pid = pid

async def main():
    S.CHARACTERS_IN_USE.clear()

    print("\n[1] claim_role cria e solta o mestre")
    r = lobby_room()
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    check("m1 é mestre", r.players["m1"].get("is_master") is True)
    check("mestre sem classe", r.players["m1"]["class_id"] is None)
    check("mestre ready", r.players["m1"]["ready"] is True)
    await add(r, "m2", "Intruso")
    await r.claim_role("m2", "master")
    check("2º mestre recusado", r.players["m2"].get("is_master") is not True)
    check("erro de 2º mestre emitido", any("mestre" in e.lower() for e in r._errs))
    await r.claim_role("m1", "hero")
    check("m1 deixou de ser mestre", not r.players["m1"].get("is_master"))
    check("m1 volta a não-ready", r.players["m1"]["ready"] is False)

    print("\n[1b] claim_role hero em quem nunca foi mestre é no-op")
    r = lobby_room()
    await add(r, "h1", "Victor")
    r.players["h1"]["ready"] = True   # herói já escolheu classe
    r.players["h1"]["class_id"] = "warrior"
    await r.claim_role("h1", "hero")
    check("ready preservado (no-op)", r.players["h1"]["ready"] is True)
    check("class_id preservado (no-op)", r.players["h1"]["class_id"] == "warrior")

    print("\n[1c] claim_role fora do lobby é no-op")
    r = lobby_room(); r.phase = "playing"
    await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    check("não vira mestre fora do lobby", not r.players["m1"].get("is_master"))

    print("\n[1d] role inválido é no-op")
    r = lobby_room()
    await add(r, "m1", "Mestre")
    await r.claim_role("m1", "banana")
    check("role inválido ignorado", not r.players["m1"].get("is_master"))
    check("master_pid não setado", r.master_pid is None)

    print("\n[2] mestre não escolhe classe")
    r = lobby_room()
    await add(r, "m1", "Mestre"); await r.claim_role("m1", "master")
    r._errs.clear()
    await r.select_class("m1", "warrior")
    check("select_class recusado p/ mestre", r.players["m1"]["class_id"] is None)
    check("erro emitido", len(r._errs) >= 1)

    print("\n[3] can_start ignora o mestre")
    r = lobby_room()
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    await r.select_class("h1", "warrior")
    check("can_start com herói pronto + mestre", r._can_start() is True)

    print("\n[4] teto 6 heróis + 1 mestre")
    r = lobby_room()
    for i in range(6):
        ok = await r.add_player(FakeWS(), f"h{i}", f"Heroi{i}")
        check(f"herói {i} entra", ok is True)
    ok7 = await r.add_player(FakeWS(), "m7", "Setimo")
    check("7º entrante aceito como MESTRE (sala sem mestre)", ok7 is True)
    check("7º virou mestre", r.players.get("m7", {}).get("is_master") is True
          and r.master_pid == "m7" and r.master_name == "Setimo")
    check("mestre auto-assentado sem classe e ready",
          r.players.get("m7", {}).get("class_id") is None
          and r.players.get("m7", {}).get("ready") is True)
    ok8 = await r.add_player(FakeWS(), "h8", "Oitavo")
    check("8º barrado (6 heróis + mestre)", ok8 is False)
    # o mestre auto-assentado não pode largar o papel com a sala já cheia de heróis
    r._errs.clear()
    await r.claim_role("m7", "hero")
    check("mestre não vira 7º herói (sala cheia)",
          r.players["m7"].get("is_master") is True)
    check("erro de sala cheia ao soltar o papel", any("cheia" in e.lower() for e in r._errs))
    # sala que JÁ tem mestre assentado: 7º entrante continua barrado
    r2 = lobby_room()
    await add(r2, "m1", "Mestre"); await r2.claim_role("m1", "master")
    for i in range(6):
        await r2.add_player(FakeWS(), f"x{i}", f"H{i}")
    check("6 heróis entram com mestre assentado",
          sum(1 for p in r2.players.values() if not p.get("is_master")) == 6)
    ok7b = await r2.add_player(FakeWS(), "y7", "Setimo")
    check("7º barrado quando já há mestre", ok7b is False)

    print("\n[5] start_game extrai o mestre de self.players")
    r = lobby_room()
    cap = {}
    async def cap_city2():
        cap["master_pid"] = getattr(r, "master_pid", None)
    r.broadcast_city_state = cap_city2
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    await r.select_class("h1", "warrior")
    r.host_pid = "h1"
    await r.start_game("h1")
    check("mestre fora de self.players", "m1" not in r.players)
    check("herói continua em self.players", "h1" in r.players)
    check("master_pid preservado", r.master_pid == "m1")
    check("master_name preservado", r.master_name == "Mestre")
    check("player_order sem o mestre", "m1" not in r.player_order)
    check("conexão do mestre preservada", "m1" in r.connections)

    print("\n[5b] start_game exige ao menos 1 herói (só mestre não inicia)")
    r = lobby_room()
    await add(r, "m1", "Mestre"); await r.claim_role("m1", "master")
    r.host_pid = "m1"; r._errs.clear()
    await r.start_game("m1")
    check("start recusado só com mestre", r.phase == "lobby")
    check("erro de herói mínimo", any("herói" in e.lower() for e in r._errs))

    print("\n[6] modo de controle e alvo dos monstros")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    r.monsters = {"g1": {"id": "g1", "hp": 8, "pos": [2, 2]},
                  "g2": {"id": "g2", "hp": 8, "pos": [3, 3]}}
    check("_mestre_ativo True", r._mestre_ativo() is True)
    await r.handle_mestre_set_modo("m1", ["g1", "g2"], "semi")
    check("g1 semi", r.monsters["g1"]["control_mode"] == "semi")
    check("g2 semi", r.monsters["g2"]["control_mode"] == "semi")
    await r.handle_mestre_set_alvo("m1", ["g1"], "h1")
    check("g1 alvo h1", r.monsters["g1"]["master_target_id"] == "h1")
    r._errs.clear()
    await r.handle_mestre_set_modo("h1", ["g1"], "manual")
    check("não-mestre recusado", r.monsters["g1"]["control_mode"] == "semi")
    del r.connections["m1"]
    check("_mestre_ativo False sem conexão", r._mestre_ativo() is False)

    print("\n[6b] modo inválido e fase != playing são no-op")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    r.monsters = {"g1": {"id": "g1", "hp": 8, "pos": [1, 1], "control_mode": "auto"}}
    await r.handle_mestre_set_modo("m1", ["g1"], "invalido")
    check("modo inválido ignorado", r.monsters["g1"]["control_mode"] == "auto")
    r.phase = "city"
    await r.handle_mestre_set_modo("m1", ["g1"], "manual")
    check("set_modo fora de playing ignorado", r.monsters["g1"]["control_mode"] == "auto")
    await r.handle_mestre_set_alvo("m1", ["g1"], "hX")
    check("set_alvo fora de playing ignorado", "master_target_id" not in r.monsters["g1"])

    print("\n[7] modo Semi força o alvo do monstro")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    m = {"id": "g1", "hp": 8, "pos": [5, 5], "control_mode": "semi", "master_target_id": "hB"}
    r.monsters = {"g1": m}
    pA = {"id": "hA", "pos": [5, 6], "alive": True}   # mais próximo
    pB = {"id": "hB", "pos": [9, 9], "alive": True}   # alvo forçado (mais longe)
    targets = [{"kind": "player", "obj": pA}, {"kind": "player", "obj": pB}]
    escolha = r._get_monster_primary_target(m, targets)
    check("Semi escolhe o alvo forçado", escolha["obj"] is pB)
    m["master_target_id"] = "hZ"
    escolha2 = r._get_monster_primary_target(m, targets)
    check("alvo inválido cai no mais próximo", escolha2["obj"] is pA)
    del r.connections["m1"]
    m["master_target_id"] = "hB"
    escolha3 = r._get_monster_primary_target(m, targets)
    check("sem mestre → padrão", escolha3["obj"] is pA)

    print("\n[8] mover_para caminha até a casa alcançável e gasta o orçamento")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 5}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    passos = {"n": 0}
    async def fake_commit_ok(mm, nx, ny):
        mm["pos"] = [nx, ny]; passos["n"] += 1; return True
    r._commit_monster_step = fake_commit_ok
    await r.handle_mestre_mover_monstro_para("m1", "g1", 4, 1)   # 3 casas para cima
    check("chegou ao destino", m["pos"] == [4, 1])
    check("gastou 3 de movimento", m["master_moves_left"] == 2)
    check("comitou 3 passos", passos["n"] == 3)

    print("\n[8b] mover_para recusa fora da janela e destino inalcançável")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "size": [1, 1], "master_moves_left": 5}
    r.monsters = {"g1": m}; r.master_manual_mid = "g9"   # outra janela
    r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 4, 1)
    check("mover fora da janela recusado", m["pos"] == [4, 4])
    r.master_manual_mid = "g1"; r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 9, 9)   # longe demais p/ 5 passos
    check("destino inalcançável recusado", m["pos"] == [4, 4])
    check("erro de inalcançável emitido", any("alcanç" in e.lower() for e in r._errs))

    print("\n[8d] mover_para para no orçamento (destino além do alcance não anda)")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [0, 0], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 2}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    async def commit_track(mm, nx, ny): mm["pos"] = [nx, ny]; return True
    r._commit_monster_step = commit_track
    r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 5, 0)   # 5 casas, só 2 de orçamento
    check("não moveu além do alcance", m["pos"] == [0, 0])

    print("\n[8c] ataque manual melee exige adjacência")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    ataques2 = {"n": 0}
    async def fake_atk2(m, atk_def, target_obj): ataques2["n"] += 1; return True
    r._execute_one_monster_attack = fake_atk2
    m = {"id": "g1", "hp": 8, "pos": [1, 1], "control_mode": "manual", "attacks": [{"name": "garra"}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"; m["_master_acted"] = False
    r.players = {"hA": {"id": "hA", "pos": [8, 8], "alive": True}}
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("ataque melee longe recusado", ataques2["n"] == 0)
    check("não marcou acted", m.get("_master_acted") is False)

    print("\n[9] sem mestre: dispatch cai em auto")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = None
    m = {"id": "g1", "hp": 8, "pos": [1, 1], "control_mode": "manual"}
    r.monsters = {"g1": m}
    mode = m.get("control_mode", "auto") if r._mestre_ativo() else "auto"
    check("sem mestre → auto", mode == "auto")

    print("\n[10] rejoin do mestre: invariante de conexão")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.master_name = "Mestre"
    check("mestre inativo desconectado", r._mestre_ativo() is False)
    r.connections["m1"] = object()
    check("mestre ativo após religar", r._mestre_ativo() is True)

    print("\n[11] mestre cai: janela Manual resolve via IA e fecha")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"
    gm_calls = {"n": 0}
    async def fake_gm(only_monster=None): gm_calls["n"] += 1
    r.gm_phase = fake_gm
    m = {"id": "g1", "hp": 8, "pos": [2, 2]}
    r.monsters = {"g1": m}
    r.players = {"hA": {"id": "hA", "pos": [3, 3], "alive": True, "connected": True}}
    r.master_manual_mid = "g1"
    r.master_manual_event = asyncio.Event()
    await r._on_master_disconnect()
    check("event setado ao cair", r.master_manual_event.is_set())
    check("janela limpa", r.master_manual_mid is None)
    check("monstro interrompido agiu via IA", gm_calls["n"] == 1)

    print("\n[11b] _on_master_disconnect sem janela aberta é seguro")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"
    r.master_manual_mid = None
    r.master_manual_event = None
    await r._on_master_disconnect()   # não deve lançar exceção
    check("no-op sem janela", r.master_manual_mid is None)

    print("\n[12] _monstro_ativo_em_combate — sem mestre = sala-trancada (byte-idêntico)")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = None   # sem mestre
    r.rooms = [{"id": 1, "locked": True}, {"id": 2, "locked": False}]
    m_trancado = {"id": "g1", "hp": 8, "pos": [1, 1], "room_id": 1}
    m_aberto   = {"id": "g2", "hp": 8, "pos": [2, 2], "room_id": 2}
    m_sem_sala = {"id": "g3", "hp": 8, "pos": [3, 3]}
    check("sem mestre: monstro em sala trancada NÃO ativo", r._monstro_ativo_em_combate(m_trancado) is False)
    check("sem mestre: monstro em sala aberta ativo", r._monstro_ativo_em_combate(m_aberto) is True)
    check("sem mestre: monstro sem sala ativo", r._monstro_ativo_em_combate(m_sem_sala) is True)

    print("\n[12b] _monstro_ativo_em_combate — com mestre = flag alertado")
    r.master_pid = "m1"; r.connections["m1"] = object()
    check("com mestre: não-alertado NÃO ativo", r._monstro_ativo_em_combate(m_aberto) is False)
    m_aberto["alertado"] = True
    check("com mestre: alertado ativo", r._monstro_ativo_em_combate(m_aberto) is True)

    print("\n[13] _verificar_avistamento acorda a sala e seta Manual (só com mestre)")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    r.players = {"hA": {"id": "hA", "pos": [0, 0], "alive": True, "connected": True}}
    m1 = {"id": "g1", "hp": 8, "pos": [5, 5], "room_id": 7}
    m2 = {"id": "g2", "hp": 8, "pos": [6, 5], "room_id": 7}   # mesma sala
    m3 = {"id": "g3", "hp": 8, "pos": [9, 9], "room_id": 8}   # outra sala
    r.monsters = {"g1": m1, "g2": m2, "g3": m3}
    # stub do avistamento: o herói só enxerga g1
    r._heroi_enxerga_monstro = lambda hero, m: (m["id"] == "g1")
    await r._verificar_avistamento()
    check("g1 alertado", m1.get("alertado") is True)
    check("g2 (mesma sala) alertado", m2.get("alertado") is True)
    check("g3 (outra sala) NÃO alertado", m3.get("alertado") is not True)
    check("g1 vira Manual", m1.get("control_mode") == "manual")
    check("g2 vira Manual", m2.get("control_mode") == "manual")

    print("\n[13b] idempotente + só-mestre")
    chamadas = {"n": 0}
    _orig = r.gm_say
    async def _cnt(*a, **k): chamadas["n"] += 1
    r.gm_say = _cnt
    await r._verificar_avistamento()   # tudo já alertado → não re-narra
    check("não re-narra sala já acordada", chamadas["n"] == 0)
    r.gm_say = _orig
    # sem mestre: no-op
    r.master_pid = None
    m4 = {"id": "g4", "hp": 8, "pos": [1, 1], "room_id": 9}
    r.monsters["g4"] = m4
    r._heroi_enxerga_monstro = lambda hero, m: True
    await r._verificar_avistamento()
    check("sem mestre: não acorda", m4.get("alertado") is not True)

    print("\n[14] monstro não-alertado (com mestre) é pulado no despacho")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    m = {"id": "g1", "hp": 8, "pos": [1, 1], "room_id": 5, "control_mode": "manual"}
    r.monsters = {"g1": m}
    check("dormente não é ativo", r._monstro_ativo_em_combate(m) is False)
    m["alertado"] = True
    check("acordado é ativo", r._monstro_ativo_em_combate(m) is True)

    print("\n[16] Reforços — carga da reserva")
    r = playing_room_com_mestre()
    defn = {"master_reinforcements": [{"type": "goblin", "count": 2},
                                      {"type": "orc", "count": 1},
                                      {"type": "goblin", "count": 3}]}
    r._carregar_master_reserve(defn)
    check("goblin soma 2+3=5", r.master_reserve.get("goblin") == 5)
    check("orc = 1", r.master_reserve.get("orc") == 1)
    r._carregar_master_reserve({"master_reinforcements": [{"type": "tipo_inexistente", "count": 9}]})
    check("tipo inválido é ignorado", "tipo_inexistente" not in r.master_reserve)
    r._carregar_master_reserve({})
    check("sem campo → reserva vazia", r.master_reserve == {})

    print("\n[17] Reforços — validar_dungeon")
    base = {"schema_version": 1, "grid": {"w": 8, "h": 8},
            "tiles": [[1]*8 for _ in range(8)],
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": "r1", "role": "entrance"}]}
    def _com_reinf(rf):
        d = dict(base); d["master_reinforcements"] = rf; return d
    ok, _ = S.validar_dungeon(_com_reinf([{"type": "goblin", "count": 2}]))
    check("reforço válido aceito", ok is True)
    ok, msg = S.validar_dungeon(_com_reinf([{"type": "naoexiste", "count": 1}]))
    check("tipo inexistente rejeitado", ok is False and "desconhecido" in msg.lower())
    ok, msg = S.validar_dungeon(_com_reinf([{"type": "goblin", "count": 0}]))
    check("count < 1 rejeitado", ok is False)
    ok, _ = S.validar_dungeon(_com_reinf("naoelista"))
    check("não-lista rejeitada", ok is False)

    print("\n[18] Reforços — implante")
    r = playing_room_com_mestre()
    r.master_reserve = {"goblin": 2}
    await r.handle_mestre_implantar_reforco("m1", "goblin", 4, 4)
    novos = [m for m in r.monsters.values() if m["pos"] == [4, 4]]
    check("monstro criado na casa", len(novos) == 1)
    check("nasce alertado", novos[0].get("alertado") is True)
    check("nasce em manual", novos[0].get("control_mode") == "manual")
    check("reserva decrementou", r.master_reserve.get("goblin") == 1)
    r._rebuild_initiative()
    check("entra no rebuild de iniciativa",
          any(e["id"] == novos[0]["id"] for e in r.initiative_order))

    # esgotar remove a chave
    await r.handle_mestre_implantar_reforco("m1", "goblin", 5, 5)
    check("reserva zerada remove a chave", "goblin" not in r.master_reserve)

    # recusas
    r2 = playing_room_com_mestre(); r2.master_reserve = {"goblin": 1}
    r2.monsters["x"] = {"id": "x", "pos": [4, 4], "hp": 5}   # casa ocupada
    await r2.handle_mestre_implantar_reforco("m1", "goblin", 4, 4)
    check("recusa casa ocupada (não decrementa)", r2.master_reserve.get("goblin") == 1)
    await r2.handle_mestre_implantar_reforco("m1", "orc", 6, 6)
    check("recusa tipo fora da reserva", "orc" not in [m.get("type") for m in r2.monsters.values()])
    await r2.handle_mestre_implantar_reforco("naomestre", "goblin", 6, 6)
    check("recusa quem não é mestre", r2.master_reserve.get("goblin") == 1)

    # sem mestre conectado → no-op
    r3 = playing_room_com_mestre(); r3.master_reserve = {"goblin": 1}
    del r3.connections["m1"]   # mestre não conectado → _mestre_ativo() False
    await r3.handle_mestre_implantar_reforco("m1", "goblin", 6, 6)
    check("sem mestre ativo → não implanta", r3.master_reserve.get("goblin") == 1)

    print("\n[19] ND unificado — monster_cr")
    check("cr explícito é usado", S.monster_cr({"cr": 1.5, "tier": 1}) == 1.5)
    check("fallback por tier sem cr", S.monster_cr({"tier": 3}) == 2.0)
    check("sem cr nem tier → trata como tier 1 (0.5)", S.monster_cr({}) == 0.5)
    check("tier desconhecido → fallback 1.0", S.monster_cr({"tier": 9}) == 1.0)
    _by = lambda t: next(d for d in S.MONSTER_DEFS if d["type"] == t)
    check("goblin legado cr 0.25", S.monster_cr(_by("goblin")) == 0.25)
    check("skeleton legado cr 0.5", S.monster_cr(_by("skeleton")) == 0.5)
    check("orc legado cr 0.75", S.monster_cr(_by("orc")) == 0.75)
    check("dark_mage legado cr 0.5", S.monster_cr(_by("dark_mage")) == 0.5)
    # O troll deixou de ser stub legado e ganhou ficha completa (tier 4, cr 4).
    check("troll (ficha completa) cr 4", S.monster_cr(_by("troll")) == 4)
    check("dragon legado cr 5", S.monster_cr(_by("dragon")) == 5.0)
    # As formas animais da Metamorfose (pombo/rato/gato/ovelha) tem cr 0 DE
    # PROPOSITO: sao criaturas ambientais de ND zero, nao aparecem em encontro
    # (spawn_min/max 0) e nao devem somar nada no termometro nem no minimapa.
    # O que a invariante protege e o cr NEGATIVO e o cr que nao resolve.
    _crs = [(d.get("type"), S.monster_cr(d)) for d in S.MONSTER_DEFS]
    check("todos MONSTER_DEFS resolvem um cr >= 0",
          all(cr is not None and cr >= 0 for _t, cr in _crs))
    check("so as formas ambientais tem cr 0",
          {t for t, cr in _crs if cr == 0} <= {"pombo", "rato", "gato", "ovelha"})

    print("\n[20] expected_party — normalização/validação")
    check("default sem campo", S.GameRoom._norm_expected_party(None) == {"heroes": 4, "level": 1})
    check("valores válidos preservados", S.GameRoom._norm_expected_party({"heroes": 6, "level": 3}) == {"heroes": 6, "level": 3})
    check("clampa heroes p/ 6", S.GameRoom._norm_expected_party({"heroes": 99, "level": 1})["heroes"] == 6)
    check("clampa heroes p/ 1", S.GameRoom._norm_expected_party({"heroes": 0, "level": 1})["heroes"] == 1)
    check("level mínimo 1", S.GameRoom._norm_expected_party({"heroes": 4, "level": 0})["level"] == 1)
    check("default no __init__", playing_room_com_mestre().expected_party == {"heroes": 4, "level": 1})
    def _com_ep(ep):
        d = dict(base); d["expected_party"] = ep; return d
    ok, _ = S.validar_dungeon(_com_ep({"heroes": 4, "level": 2}))
    check("ep válido aceito", ok is True)
    ok, msg = S.validar_dungeon(_com_ep({"heroes": 7, "level": 1}))
    check("heroes>6 rejeitado", ok is False and "heroes" in msg.lower())
    ok, _ = S.validar_dungeon(_com_ep({"heroes": 4, "level": 0}))
    check("level<1 rejeitado", ok is False)
    ok, _ = S.validar_dungeon(_com_ep("naoobj"))
    check("não-objeto rejeitado", ok is False)

    print("\n[21] ND/XP de armadilha — trap_cr/trap_xp")
    check("cr explícito", S.trap_cr({"cr": 0.5}) == 0.5)
    check("fallback por dificuldade (>0)", S.trap_cr({"dificuldade": 14}) > 0)
    check("fallback default sem nada", S.trap_cr({}) == 0.3)
    check("trap_xp deriva do cr", S.trap_xp(0.5) == round(0.5 * S.TRAP_XP_POR_CR))
    check("mina cr 0.75", S.trap_cr(S.ARMADILHAS["mina_terrestre"]) == 0.75)
    check("buraco cr 0.1", S.trap_cr(S.ARMADILHAS["buraco"]) == 0.1)
    check("todas ARMADILHAS resolvem cr>0", all(S.trap_cr(m) > 0 for m in S.ARMADILHAS.values()))

    print("\n[22] ND/XP de armadilha — concessão")
    r = playing_room_com_mestre()
    r.players["h"] = {"id":"h","name":"H","class_id":"warrior","alive":True,"hp":10,
                      "max_hp":10,"pos":[1,1],"xp":0,"level":1,"str_":14,"dex":12,
                      "con_":12,"int_":10}
    arm = {"id":"a1","tipo":"mina_terrestre","pos":[2,2]}
    await r._conceder_xp_armadilha(arm)
    check("XP concedido no 1º (mina cr .75 → 15)", r.players["h"]["xp"] == 15)
    check("marca xp_concedido", arm.get("xp_concedido") is True)
    x1 = r.players["h"]["xp"]; await r._conceder_xp_armadilha(arm)
    check("não concede 2ª vez", r.players["h"]["xp"] == x1)
    arm2 = {"id":"a2","tipo":"buraco","pos":[3,3],"aliada":True}
    xb = r.players["h"]["xp"]; await r._conceder_xp_armadilha(arm2)
    check("armadilha aliada não concede", r.players["h"]["xp"] == xb)
    arm3 = {"id":"a3","tipo":"tipo_inexistente","pos":[4,4]}
    await r._conceder_xp_armadilha(arm3)
    check("tipo inválido não concede", r.players["h"]["xp"] == xb)

    print("\n[23] Salas obrigatórias")
    r = playing_room_com_mestre()
    r.rooms = [{"id":0,"x":0,"y":0,"w":3,"h":3,"required":True,"required_mode":"clear"},
               {"id":1,"x":5,"y":0,"w":3,"h":3,"required":True,"required_mode":"visit"},
               {"id":2,"x":0,"y":5,"w":3,"h":3}]
    r.salas_visitadas = set()
    r.monsters = {"m":{"id":"m","hp":5,"room_id":0,"pos":[1,1]}}
    obj = {"type":"salas_obrigatorias"}
    check("pendente: sala 0 com monstro vivo", r._objetivo_cumprido(obj) is False)
    check("progresso 0/2", r._salas_obrigatorias_progresso() == (0, 2))
    r.monsters["m"]["hp"] = 0; r.salas_visitadas.add(1)
    check("cumprido quando todas atendem", r._objetivo_cumprido(obj) is True)
    check("progresso 2/2", r._salas_obrigatorias_progresso() == (2, 2))
    r2 = playing_room_com_mestre()
    r2.rooms = [{"id":0,"x":0,"y":0,"w":3,"h":3,"required":True,"required_mode":"clear"}]
    r2.salas_visitadas = set(); r2.monsters = {}
    check("clear de sala vazia = cumprida", r2._objetivo_cumprido({"type":"salas_obrigatorias"}) is True)
    base_sr = dict(base); base_sr["objectives"] = {"primary": {"type":"salas_obrigatorias"}, "secondary": []}
    ok, msg = S.validar_dungeon(base_sr)
    check("obj sem salas marcadas rejeitado", ok is False and "salas" in msg.lower())
    base_rm = dict(base); base_rm["rooms"] = [{"id":9,"x":1,"y":1,"w":2,"h":2,"required_mode":"xyz"}]
    ok, _ = S.validar_dungeon(base_rm)
    check("required_mode inválido rejeitado", ok is False)

    print("\n[24] Falas de NPC")
    r = playing_room_com_mestre()
    r.rooms = [{"id":0,"x":0,"y":0,"w":5,"h":5,"cleared":True}]
    r.falas = [
        {"id":"f1","pos":[3,3],"falante":{"nome":"Velho","emoji":"🧙"},"texto":"Cuidado!","trigger":{"tipo":"proximidade","raio":2},"disparada":False},
        {"id":"f2","pos":[1,1],"falante":{},"texto":"Bem-vindos.","trigger":{"tipo":"sala"},"disparada":False},
        {"id":"f3","pos":[4,4],"falante":{},"texto":"Tolos!","trigger":{"tipo":"manual"},"disparada":False},
    ]
    ditas = []
    async def cap_bc(msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "fala": ditas.append(msg["texto"])
    r.broadcast = cap_bc
    p = {"id":"h","name":"H","alive":True,"pos":[10,10]}; r.players["h"] = p
    await r._verificar_falas(p, None)
    check("proximidade longe não dispara", "Cuidado!" not in ditas)
    p["pos"] = [3,4]; await r._verificar_falas(p, None)
    check("proximidade perto dispara", "Cuidado!" in ditas)
    check("marca disparada", r.falas[0]["disparada"] is True)
    n = len(ditas); await r._verificar_falas(p, None)
    check("proximidade não repete", len(ditas) == n)
    await r._verificar_falas(p, r.rooms[0])
    check("sala dispara ao entrar", "Bem-vindos." in ditas)
    await r.handle_disparar_fala("m1", "f3")
    check("manual dispara (mestre)", "Tolos!" in ditas)
    r.falas.append({"id":"f4","pos":[0,0],"texto":"x","trigger":{"tipo":"proximidade"},"disparada":False})
    await r.handle_disparar_fala("m1", "f4")
    check("manual recusa fala não-manual", r.falas[-1]["disparada"] is not True)
    r.falas[2]["disparada"] = False
    await r.handle_disparar_fala("naomestre", "f3")
    check("manual recusa não-mestre", r.falas[2]["disparada"] is not True)

    print("\n[25] _master_reach_bfs / _master_monster_reach respeitam orçamento e paredes")
    r = playing_room_com_mestre()
    # parede vertical em x=3 (coluna toda), abre um vão em y=2
    for y in range(10):
        r.tiles[y][3] = S.WALL
    r.tiles[2][3] = S.FLOOR
    m = {"id": "g1", "hp": 8, "pos": [1, 2], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 2}
    r.monsters = {"g1": m}
    reach = r._master_monster_reach(m)
    reach_set = {tuple(c) for c in reach}
    check("alcança a 2 passos ortogonais", (1, 0) in reach_set and (1, 4) in reach_set)
    check("não inclui a casa atual", (1, 2) not in reach_set)
    check("não atravessa parede (x=4 fora de 2 passos)", (4, 2) not in reach_set)
    check("respeita orçamento (3 passos fora)", (1, 5) not in reach_set)
    # com orçamento maior, cruza o vão em (3,2) e chega em (4,2)
    m["master_moves_left"] = 3
    reach2 = {tuple(c) for c in r._master_monster_reach(m)}
    check("com 3 passos cruza o vão", (3, 2) in reach2 and (4, 2) in reach2)
    check("orçamento 0 → vazio", r._master_monster_reach({"id":"g2","pos":[1,2],"master_moves_left":0}) == [])

    print("\n[26] mestre_usar_habilidade — ativa via _use_monster_ability e consome a ação")
    r = playing_room_com_mestre()
    usada = {"ab": None, "alvo": None}
    async def fake_use(mm, ability, target_obj):
        usada["ab"] = ability["id"]; usada["alvo"] = target_obj["obj"]["id"]; return True
    r._use_monster_ability = fake_use
    ab_ok = {"id": "petrificar", "name": "Petrificar", "action_type": "acao",
             "save": "fort", "dc": 13}
    ab_passiva = {"id": "sem_dor", "name": "Sem Dor", "action_type": "passiva"}
    ab_ia = {"id": "turbilhao", "name": "Turbilhão", "action_type": "acao"}   # sem save/dc
    m = {"id": "g1", "hp": 20, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "attacks": [{"name": "garra"}], "_master_acted": False,
         "special_abilities": [ab_ok, ab_passiva, ab_ia]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("habilidade ativada", usada["ab"] == "petrificar" and usada["alvo"] == "hA")
    check("consumiu a ação", m["_master_acted"] is True)

    print("\n[26b] recusa passiva / IA-apenas / já-agiu / alvo fora de alcance")
    r = playing_room_com_mestre()
    r._use_monster_ability = fake_use
    m = {"id": "g1", "hp": 20, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "special_abilities": [ab_ok, ab_passiva, ab_ia]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True},
                 "hB": {"id": "hB", "name": "Bea", "pos": [9, 9], "alive": True}}
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "sem_dor", "hA")
    check("passiva recusada", m["_master_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "turbilhao", "hA")
    check("IA-apenas (sem save/dc) recusada", m["_master_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hB")
    check("alvo fora de alcance (melee) recusado", m["_master_acted"] is False)
    m["_master_acted"] = True; r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("já-agiu recusado", any("agiu" in e.lower() for e in r._errs))

    print("\n[27] mestre_usar_item — heal (bônus), throwable (principal), food recusado")
    r = playing_room_com_mestre()
    heal_calls = {"n": 0}
    m = {"id": "g1", "hp": 5, "max_hp": 12, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "attacks": [{"name": "espada"}],
         "equipment_consumables": [
            {"id": "health_potion", "name": "Poção", "effect": "heal", "value": 6},
            {"id": "granada", "name": "Granada", "effect": "throwable"},
            {"id": "cantil_agua", "name": "Cantil", "effect": "food"},
         ]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 10, "max_hp": 10}}
    # heal → cura o monstro, gasta a ação bônus, remove a poção
    await r.handle_mestre_usar_item("m1", "g1", "health_potion", None, None, None)
    check("curou o monstro", m["hp"] == 11)
    check("gastou ação bônus", m["_master_bonus_acted"] is True)
    check("poção removida", not any(i["id"] == "health_potion" for i in m["equipment_consumables"]))
    check("ação principal livre", m["_master_acted"] is False)
    # throwable → chama _monster_throw_item mirando o herói, gasta a ação principal
    throws = {"n": 0}
    async def fake_throw(mm, target_obj, item): throws["n"] += 1
    r._monster_throw_item = fake_throw
    r._tem_linha_de_visao = lambda a, b: True
    await r.handle_mestre_usar_item("m1", "g1", "granada", "hA", None, None)
    check("arremessou no herói", throws["n"] == 1)
    check("gastou ação principal", m["_master_acted"] is True)
    check("granada removida", not any(i["id"] == "granada" for i in m["equipment_consumables"]))
    # food → recusado, sem efeito
    r._errs.clear()
    await r.handle_mestre_usar_item("m1", "g1", "cantil_agua", None, None, None)
    check("food recusado", any("efeito" in e.lower() for e in r._errs))
    check("cantil continua na bolsa", any(i["id"] == "cantil_agua" for i in m["equipment_consumables"]))

    print("\n[28] mestre_usar_habilidade — habilidade de editor (herói/guilda) ativável")
    r = playing_room_com_mestre()
    ab = {"id": "hero_warrior_mira_certeira", "source": "heroi", "name": "Mira Certeira",
          "action_type": "acao", "monster_effect": "vantagem_combate",
          "uses_per_day": 3, "cooldown_turns": 4}
    m = {"id": "g1", "hp": 10, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "special_abilities": [ab],
         "monster_ability_uses": {"hero_warrior_mira_certeira": 3},
         "monster_ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("predicado aceita editor ability", r._habilidade_ativavel_manual(ab) is True)
    await r.handle_mestre_usar_habilidade("m1", "g1", "hero_warrior_mira_certeira", None)
    check("aplicou vantagem", m.get("editor_ability_advantage", 0) >= 1)
    check("gastou 1 uso", m["monster_ability_uses"]["hero_warrior_mira_certeira"] == 2)
    check("entrou em recarga", m["monster_ability_cooldowns"].get("hero_warrior_mira_certeira", 0) > 0)
    check("consumiu a ação", m["_master_acted"] is True)
    m["_master_acted"] = False; m["monster_ability_uses"]["hero_warrior_mira_certeira"] = 0
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "hero_warrior_mira_certeira", None)
    check("sem usos recusado", m["_master_acted"] is False)

    print("\n[29] janela Manual renova o orçamento de passo a cada turno")
    # `_commit_monster_step` debita `_water_moves_left` a cada casa (custo 1 em
    # chão seco). Só `gm_phase` o renovava, e o Manual não passa por lá — sem o
    # reset na janela o gasto acumulava entre turnos e o monstro do mestre
    # travava de vez depois de andar `movement` casas NO TOTAL da partida.
    r = playing_room_com_mestre()
    r.map_w = r.map_h = 20    # espaço para os 3 turnos de caminhada sem bater na borda
    r.tiles = [[S.FLOOR]*r.map_w for _ in range(r.map_h)]
    r.materiais = {}          # mapa 100% seco: cada casa custa 1
    r.decorations = []
    r.players = {}
    mv = 3
    m = {"id": "g1", "type": "goblin", "name": "Goblin", "pos": [1, 1], "hp": 10,
         "max_hp": 10, "ac": 12, "movement": mv, "size": [1, 1], "control_mode": "manual"}
    r.monsters = {"g1": m}

    async def abrir_janela_manual(sala, monstro):
        """Abre a janela Manual e a fecha em seguida — espelha um turno do mestre."""
        task = asyncio.create_task(sala._master_manual_window(monstro))
        await asyncio.sleep(0)               # deixa a janela chegar no await do Event
        sala.master_manual_event.set()
        await task

    andou_por_turno = []
    for _turno in range(3):
        await abrir_janela_manual(r, m)
        check(f"turno {_turno+1}: orçamento de passo renovado", m.get("_water_moves_left") == mv)
        check(f"turno {_turno+1}: _moved_this_turn resetado", m.get("_moved_this_turn") is False)
        r.master_manual_mid = "g1"           # a janela zera o ponteiro ao fechar
        passos = 0
        for _ in range(mv):
            await r.handle_mestre_mover_monstro_para("m1", "g1", m["pos"][0] + 1, m["pos"][1])
            passos = mv - m["master_moves_left"]
        andou_por_turno.append(passos)

    check("andou nos 3 turnos (não trava após o 1º)", andou_por_turno == [mv, mv, mv])
    check("percorreu movement × 3 casas no total", m["pos"][0] == 1 + mv * 3)

    print("\n[30] _custo_acao_ability — traduz action_type em custo")
    r = playing_room_com_mestre()
    check("acao → principal",      r._custo_acao_ability({"action_type": "acao"}) == "principal")
    check("magia → principal",     r._custo_acao_ability({"action_type": "magia"}) == "principal")
    check("ataque → principal",    r._custo_acao_ability({"action_type": "ataque"}) == "principal")
    check("acao_bonus → bonus",    r._custo_acao_ability({"action_type": "acao_bonus"}) == "bonus")
    check("acao_livre → livre",    r._custo_acao_ability({"action_type": "acao_livre"}) == "livre")
    check("desconhecido → principal", r._custo_acao_ability({"action_type": "xyz"}) == "principal")
    check("sem action_type → principal", r._custo_acao_ability({}) == "principal")
    check("None → principal",      r._custo_acao_ability(None) == "principal")

    print("\n[31] cargas de ataque montadas na abertura da janela")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [1, 1],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Garras", "atk_bonus": 5, "damage": "1d4", "num_attacks": 2},
                     {"name": "Mordida", "atk_bonus": 4, "damage": "1d6", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("cargas por índice", m["master_attack_charges"] == {0: 2, 1: 1})
    check("tipo de ação zerado", m.get("_master_acao_tipo") is None)
    r.master_manual_event.set()
    await task

    print("\n[31b] monstro legado (sem attacks[]) ganha 1 carga")
    r = playing_room_com_mestre()
    m2 = {"id": "g2", "name": "Goblin", "hp": 6, "max_hp": 6, "pos": [1, 1],
          "size": [1, 1], "movement": 4, "control_mode": "manual",
          "atk_bonus": 2, "damage": "1d6"}
    r.monsters = {"g2": m2}
    task = asyncio.create_task(r._master_manual_window(m2))
    await asyncio.sleep(0)
    check("legado tem 1 carga no índice 0", m2["master_attack_charges"] == {0: 1})
    r.master_manual_event.set()
    await task

    print("\n[32] ataques granulares — cargas, alvos distintos, recusa da 4ª")
    r = playing_room_com_mestre()
    golpes = []
    async def fake_atk(mm, atk_def, target_obj):
        golpes.append((atk_def.get("name"), target_obj["obj"]["id"])); return True
    r._execute_one_monster_attack = fake_atk
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_bonus_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 2, 1: 1},
         "attacks": [{"name": "Garras", "num_attacks": 2},
                     {"name": "Mordida", "num_attacks": 1}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True},
                 "hB": {"id": "hB", "name": "Bea", "pos": [3, 2], "alive": True}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("1ª garra saiu", golpes == [("Garras", "hA")])
    check("carga 0 debitada", m["master_attack_charges"][0] == 1)
    check("ação comprometida com ataque", m["_master_acao_tipo"] == "ataque")
    check("ação principal marcada", m["_master_acted"] is True)
    await r.handle_mestre_atacar_monstro("m1", "g1", "hB", 0)
    check("2ª garra em outro herói", golpes[-1] == ("Garras", "hB"))
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 1)
    check("mordida saiu", golpes[-1] == ("Mordida", "hA"))
    check("todas as cargas gastas", m["master_attack_charges"] == {0: 0, 1: 0})
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("4ª tentativa recusada", len(golpes) == 3)
    check("erro explica as cargas", any("golpe" in e.lower() for e in r._errs))

    print("\n[32b] attack_index ausente = índice 0 (cliente antigo)")
    r = playing_room_com_mestre()
    golpes2 = []
    async def fake_atk2(mm, atk_def, target_obj):
        golpes2.append(atk_def.get("name")); return True
    r._execute_one_monster_attack = fake_atk2
    m = {"id": "g1", "name": "Orc", "hp": 12, "max_hp": 12, "pos": [2, 2],
         "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 1},
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("sem attack_index usa o 0", golpes2 == ["Machado"])

    print("\n[32b-2] ataque manual aceita qualquer casa de um alvo monstro 2x2")
    r = playing_room_com_mestre()
    r.test_mode = True
    golpes3 = []
    async def fake_atk3(mm, atk_def, target_obj):
        golpes3.append(target_obj["obj"]["id"]); return True
    r._execute_one_monster_attack = fake_atk3
    atacante = {"id": "g1", "name": "Goblin", "hp": 20, "max_hp": 20,
                "pos": [4, 6], "size": [1, 1], "control_mode": "manual",
                "_master_acted": False, "_master_acao_tipo": None,
                "master_attack_charges": {0: 1},
                "attacks": [{"name": "Garra", "num_attacks": 1}]}
    ciclope = {"id": "c1", "name": "Ciclope", "hp": 40, "max_hp": 40,
               "pos": [5, 5], "size": [2, 2], "oriented": False}
    r.monsters = {"g1": atacante, "c1": ciclope}; r.master_manual_mid = "g1"
    await r.handle_mestre_atacar_monstro("m1", "g1", "c1", 0)
    check("aceita alvo pela casa lateral do Ciclope", golpes3 == ["c1"])

    print("\n[32c] Fúria Bestial sob controle Manual")
    r = playing_room_com_mestre()
    async def fake_atk_no_dano(mm, atk_def, target_obj):
        return True
    r._execute_one_monster_attack = fake_atk_no_dano
    m = {"id": "g1", "name": "Grotão", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 1, 1: 2},
         "attacks": [{"name": "Mordida", "num_attacks": 1},
                     {"name": "Garras", "num_attacks": 2}],
         "special_abilities": [{"id": "furia_bestial", "action_type": "passiva"}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 20, "max_hp": 20},
                 "hB": {"id": "hB", "name": "Bea", "pos": [3, 2], "alive": True, "hp": 20, "max_hp": 20}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("grupo 0 sozinho não dá Fúria", r.players["hA"]["hp"] == 20)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 1)
    check("Fúria disparou no 2º grupo do mesmo alvo", r.players["hA"]["hp"] < 20)
    hp_apos_furia = r.players["hA"]["hp"]
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 1)
    check("Fúria não repete no mesmo alvo", r.players["hA"]["hp"] == hp_apos_furia)

    print("\n[32c-2] só o grupo 0 não basta")
    r = playing_room_com_mestre()
    r._execute_one_monster_attack = fake_atk_no_dano
    m = {"id": "g1", "name": "Grotão", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 1, 1: 2},
         "attacks": [{"name": "Mordida", "num_attacks": 1},
                     {"name": "Garras", "num_attacks": 2}],
         "special_abilities": [{"id": "furia_bestial", "action_type": "passiva"}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 20, "max_hp": 20}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("só grupo 0: sem Fúria", r.players["hA"]["hp"] == 20)

    print("\n[32c-3] grupos em alvos diferentes não combinam")
    r = playing_room_com_mestre()
    r._execute_one_monster_attack = fake_atk_no_dano
    m = {"id": "g1", "name": "Grotão", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 1, 1: 2},
         "attacks": [{"name": "Mordida", "num_attacks": 1},
                     {"name": "Garras", "num_attacks": 2}],
         "special_abilities": [{"id": "furia_bestial", "action_type": "passiva"}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 20, "max_hp": 20},
                 "hB": {"id": "hB", "name": "Bea", "pos": [3, 2], "alive": True, "hp": 20, "max_hp": 20}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hB", 1)
    check("alvos diferentes: hA sem Fúria", r.players["hA"]["hp"] == 20)
    check("alvos diferentes: hB sem Fúria", r.players["hB"]["hp"] == 20)

    print("\n[32c-4] ataque recusado não gasta carga nem marca ação")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 2},
         "attacks": [{"name": "Garras", "num_attacks": 2}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [10, 10], "alive": True, "hp": 20, "max_hp": 20}}
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("recusado por distância", any(("adjacente" in e.lower() or "alcanc" in e.lower()) for e in r._errs))
    check("carga intacta após recusa", m["master_attack_charges"] == {0: 2})
    check("ação principal não marcada após recusa", m["_master_acted"] is False)

    print("\n[32c-5] Fúria Bestial: teto de 1 proc por TURNO, não por herói")
    r = playing_room_com_mestre()
    r._execute_one_monster_attack = fake_atk_no_dano
    m = {"id": "g1", "name": "Grotão", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 2, 1: 2},
         "attacks": [{"name": "Mordida", "num_attacks": 2},
                     {"name": "Garras", "num_attacks": 2}],
         "special_abilities": [{"id": "furia_bestial", "action_type": "passiva"}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 20, "max_hp": 20},
                 "hB": {"id": "hB", "name": "Bea", "pos": [3, 2], "alive": True, "hp": 20, "max_hp": 20}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 1)
    check("1º proc do turno em hA", r.players["hA"]["hp"] < 20)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hB", 0)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None
    await r.handle_mestre_atacar_monstro("m1", "g1", "hB", 1)
    check("2º proc do turno em hB é suprimido", r.players["hB"]["hp"] == 20)

    print("\n[33] economia por action_type — bônus e livre não gastam a principal")
    r = playing_room_com_mestre()
    async def fake_use(mm, ability, target_obj): return True
    r._use_monster_ability = fake_use
    ab_bonus = {"id": "grito", "name": "Grito", "action_type": "acao_bonus", "save": "vontade", "dc": 10}
    ab_livre = {"id": "farejar", "name": "Farejar", "action_type": "acao_livre", "save": "fort", "dc": 10}
    ab_acao  = {"id": "petrificar", "name": "Petrificar", "action_type": "acao", "save": "fort", "dc": 13}
    m = {"id": "g1", "name": "Coisa", "hp": 20, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "garra", "num_attacks": 1}],
         "master_attack_charges": {0: 1},
         "special_abilities": [ab_bonus, ab_livre, ab_acao]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g1", "farejar", "hA")
    check("acao_livre não gasta nada", m["_master_acted"] is False and m["_master_bonus_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "grito", "hA")
    check("acao_bonus gasta só a bônus", m["_master_bonus_acted"] is True and m["_master_acted"] is False)
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "grito", "hA")
    check("2ª bônus recusada", any("bônus" in e.lower() or "bonus" in e.lower() for e in r._errs))
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("acao gasta a principal", m["_master_acted"] is True)
    check("tipo registrado", m["_master_acao_tipo"] == "habilidade")

    print("\n[33b] atacar depois de habilidade de ação é recusado")
    r._errs.clear()
    golpes = []
    async def fake_atk(mm, atk_def, target_obj): golpes.append(1); return True
    r._execute_one_monster_attack = fake_atk
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("ataque após magia recusado", golpes == [])
    check("carga preservada", m["master_attack_charges"][0] == 1)

    print("\n[34] magias do mestre — lança, debita usos, respeita recarga")
    r = playing_room_com_mestre()
    lancadas = []
    async def fake_grim(mm, magia, data, *a, **k):
        lancadas.append((magia["id"], data.get("target_id")))
    r._executar_magia_grimorio = fake_grim
    ab_magia = {"id": "silencio", "name": "Silêncio", "action_type": "magia"}
    m = {"id": "g1", "name": "Xamã", "hp": 14, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_magia],
         "monster_spells": [{"id": "silencio", "limit_mode": "encounter", "uses_per_combat": 1}],
         "spell_uses": {"silencio": 1}, "spell_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("predicado aceita magia implementada", r._habilidade_ativavel_manual(ab_magia) is True)
    await r.handle_mestre_usar_habilidade("m1", "g1", "silencio", "hA")
    check("magia lançada no alvo do mestre", lancadas == [("silencio", "hA")])
    check("uso debitado", m["spell_uses"]["silencio"] == 0)
    check("gastou a ação principal", m["_master_acted"] is True)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None; r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "silencio", "hA")
    check("sem usos não lança de novo", len(lancadas) == 1)
    check("ação preservada na recusa", m["_master_acted"] is False)

    print("\n[34b] encantar_* segue não-ativável (não implementada)")
    check("encantar_vampirico barrado",
          r._habilidade_ativavel_manual({"id": "encantar_vampirico", "action_type": "acao",
                                         "dc": 12}) is False)

    print("\n[34c] magia de aliado não mira herói; utilidade/reação segue barrada")
    r = playing_room_com_mestre()
    lancadas34c = []
    async def fake_grim_34c(mm, magia, data, *a, **k):
        lancadas34c.append((magia["id"], data.get("target_id")))
    r._executar_magia_grimorio = fake_grim_34c
    # abencoar_arma: tipo "alvo_aliado", em GRIMORIO_IMPLEMENTADAS.
    ab_aliado = {"id": "abencoar_arma", "name": "Abençoar Arma", "action_type": "magia"}
    m1 = {"id": "g1", "name": "Clérigo Sombrio", "hp": 14, "pos": [2, 2], "size": [1, 1],
          "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
          "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
          "master_attack_charges": {0: 1}, "special_abilities": [ab_aliado],
          "monster_spells": [{"id": "abencoar_arma", "limit_mode": "encounter", "uses_per_combat": 2}],
          "spell_uses": {"abencoar_arma": 2}, "spell_cooldowns": {}}
    m2 = {"id": "g2", "name": "Goblin Aliado", "hp": 8, "pos": [3, 2], "size": [1, 1]}
    r.monsters = {"g1": m1, "g2": m2}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g1", "abencoar_arma", "hA")
    check("magia de aliado não mira herói", lancadas34c and lancadas34c[-1][1] != "hA")
    check("magia de aliado mira um monstro", lancadas34c and lancadas34c[-1][1] in {"g1", "g2"})

    m1["_master_acted"] = False; m1["_master_acao_tipo"] = None
    await r.handle_mestre_usar_habilidade("m1", "g1", "abencoar_arma", "g2")
    check("magia de aliado aceita o monstro escolhido", lancadas34c[-1] == ("abencoar_arma", "g2"))

    # contramagica: tipo "reacao", em GRIMORIO_IMPLEMENTADAS — sem uso manual.
    ab_reacao = {"id": "contramagica", "name": "Contramágica", "action_type": "magia"}
    check("reação barrada no predicado", r._habilidade_ativavel_manual(ab_reacao) is False)
    m3 = {"id": "g3", "name": "Arcanista", "hp": 10, "pos": [4, 2], "size": [1, 1],
          "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
          "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
          "master_attack_charges": {0: 1}, "special_abilities": [ab_reacao],
          "monster_spells": [{"id": "contramagica", "limit_mode": "encounter", "uses_per_combat": 1}],
          "spell_uses": {"contramagica": 1}, "spell_cooldowns": {}}
    r.monsters["g3"] = m3; r.master_manual_mid = "g3"; r._errs.clear()
    lancadas34c.clear()
    await r.handle_mestre_usar_habilidade("m1", "g3", "contramagica", "hA")
    check("reação recusada sem lançar", lancadas34c == [])
    check("reação recusada sem gastar ação", m3["_master_acted"] is False)

    # silencio: tipo "area_fixa" (hostil) — alvo inválido é recusado antes de gastar.
    ab_hostil = {"id": "silencio", "name": "Silêncio", "action_type": "magia"}
    m4 = {"id": "g4", "name": "Xamã", "hp": 14, "pos": [2, 2], "size": [1, 1],
          "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
          "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
          "master_attack_charges": {0: 1}, "special_abilities": [ab_hostil],
          "monster_spells": [{"id": "silencio", "limit_mode": "encounter", "uses_per_combat": 1}],
          "spell_uses": {"silencio": 1}, "spell_cooldowns": {}}
    r.monsters["g4"] = m4; r.master_manual_mid = "g4"; r._errs.clear()
    lancadas34c.clear()
    await r.handle_mestre_usar_habilidade("m1", "g4", "silencio", "hZ_inexistente")
    check("alvo hostil inválido não lança", lancadas34c == [])
    check("alvo hostil inválido não debita uso", m4["spell_uses"]["silencio"] == 1)
    check("alvo hostil inválido não gasta ação", m4["_master_acted"] is False)

    print("\n[34d] teto permissivo de alcance (alcance_base/escala) — silencio")
    r = playing_room_com_mestre()
    lancadas34d = []
    async def fake_grim_34d(mm, magia, data, *a, **k):
        lancadas34d.append((magia["id"], data.get("target_id")))
    r._executar_magia_grimorio = fake_grim_34d
    # silencio: alcance_base 5, alcance_escala 1 — teto a nível 1 (default) = 5.
    ab_silencio = {"id": "silencio", "name": "Silêncio", "action_type": "magia"}
    m5 = {"id": "g5", "name": "Xamã", "hp": 14, "pos": [0, 0], "size": [1, 1],
          "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
          "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
          "master_attack_charges": {0: 1}, "special_abilities": [ab_silencio],
          "monster_spells": [{"id": "silencio", "limit_mode": "encounter", "uses_per_combat": 2}],
          "spell_uses": {"silencio": 2}, "spell_cooldowns": {}}
    r.monsters = {"g5": m5}; r.master_manual_mid = "g5"
    r.players = {"hLonge": {"id": "hLonge", "name": "Longe", "pos": [50, 50], "alive": True},
                 "hPerto": {"id": "hPerto", "name": "Perto", "pos": [1, 0], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g5", "silencio", "hLonge")
    check("fora do teto é recusado sem gastar", lancadas34d == [])
    check("fora do teto não debita uso", m5["spell_uses"]["silencio"] == 2)
    check("fora do teto não gasta ação", m5["_master_acted"] is False)

    await r.handle_mestre_usar_habilidade("m1", "g5", "silencio", "hPerto")
    check("dentro do teto lança", lancadas34d == [("silencio", "hPerto")])
    check("dentro do teto debita uso", m5["spell_uses"]["silencio"] == 1)

    print("\n[34e] _alcance_magia_teto nunca é mais estrito que os executores")
    magia_teste = {"alcance_base": 4, "alcance_escala": 1}
    teto = r._alcance_magia_teto(magia_teste, 5)
    formula_necro = 4 + 1 * (5 - 1)
    formula_silencio = 4 + (5 // 2) * 1
    check("teto >= fórmula do necro/genérico", teto >= formula_necro)
    check("teto >= fórmula do _executar_silencio", teto >= formula_silencio)

    print("\n[35] Golpe Brutal — mesma extração para IA e mestre")
    r = playing_room_com_mestre()
    ab_gb = {"id": "golpe_brutal", "name": "Golpe Brutal", "action_type": "ataque"}
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "Clava", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_gb],
         "ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    ok = await r._ativar_golpe_brutal(m)
    check("ativou", ok is True)
    check("armou o bônus", m.get("_golpe_brutal_ativo") is True)
    check("entrou em recarga 3", m["ability_cooldowns"]["golpe_brutal"] == 3)
    check("bônus de dano é +2", r._golpe_brutal_bonus(m) == 2)
    check("2ª ativação recusada (recarga)", await r._ativar_golpe_brutal(m) is False)
    m2 = {"id": "g2", "name": "Ogro2", "hp": 25, "pos": [5, 5], "size": [1, 1],
          "special_abilities": [], "ability_cooldowns": {}}
    check("sem a habilidade não ativa", await r._ativar_golpe_brutal(m2) is False)

    print("\n[35b] o golpe seguinte consome o bônus armado")
    golpes = []
    async def fake_atk(mm, atk_def, target_obj):
        golpes.append(mm.get("_golpe_brutal_ativo")); return True
    r._execute_one_monster_attack = fake_atk
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("golpe saiu com o bônus ativo", golpes == [True])
    check("bônus limpo após o golpe", m.get("_golpe_brutal_ativo") is None)

    print("\n[35c] Golpe Brutal armado e NÃO consumido não sobrevive à janela")
    m3 = {"id": "g3", "name": "Ogro3", "hp": 25, "pos": [3, 3], "size": [1, 1],
          "control_mode": "manual", "attacks": [{"name": "Clava", "num_attacks": 1}],
          "special_abilities": [ab_gb], "ability_cooldowns": {}}
    r.monsters = {"g3": m3}
    ok = await r._ativar_golpe_brutal(m3)
    check("ativou", ok is True)
    check("armou o bônus", m3.get("_golpe_brutal_ativo") is True)
    cd_antes = m3["ability_cooldowns"]["golpe_brutal"]
    task = asyncio.create_task(r._master_manual_window(m3))
    await asyncio.sleep(0)
    r.master_manual_event.set()
    await task
    check("bônus não consumido some ao abrir nova janela", not m3.get("_golpe_brutal_ativo"))
    # A janela seguinte roda o upkeep de início de turno (Task 8): a recarga
    # anda 1 normalmente (não é resetada nem congelada) — não seria mais
    # "preservada" byte-a-byte, e sim decrementada como o tempo real exige.
    check("recarga anda 1 (upkeep de início de turno)",
          m3["ability_cooldowns"]["golpe_brutal"] == cd_antes - 1)

    print("\n[36] Desaparecer nas Sombras — extração compartilhada")
    r = playing_room_com_mestre()
    r._em_escuridao = lambda mm: True
    ab_ds = {"id": "desaparecer_nas_sombras", "name": "Desaparecer nas Sombras",
             "action_type": "acao_livre"}
    m = {"id": "g1", "name": "Bugbear", "hp": 20, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "maça", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_ds],
         "ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("ativou", await r._ativar_desaparecer_sombras(m) is True)
    check("ficou oculto", m.get("oculto_sombras") is True)
    check("recarga 5", m["ability_cooldowns"]["desaparecer_nas_sombras"] == 5)
    check("2ª ativação recusada", await r._ativar_desaparecer_sombras(m) is False)
    r._em_escuridao = lambda mm: False
    m3 = {"id": "g3", "name": "Bug2", "hp": 20, "pos": [7, 7], "size": [1, 1],
          "special_abilities": [ab_ds], "ability_cooldowns": {}}
    check("fora da escuridão não ativa", await r._ativar_desaparecer_sombras(m3) is False)

    print("\n[36b] pelo mestre é ação livre — a principal segue disponível")
    r._em_escuridao = lambda mm: True
    m["ability_cooldowns"]["desaparecer_nas_sombras"] = 0
    m.pop("oculto_sombras", None)
    await r.handle_mestre_usar_habilidade("m1", "g1", "desaparecer_nas_sombras", None)
    check("oculto de novo", m.get("oculto_sombras") is True)
    check("ação principal intacta", m["_master_acted"] is False)

    print("\n[36c] Upkeep de início de turno no Manual (recarga + oculto)")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Bugbear", "hp": 20, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual",
         "ability_cooldowns": {"golpe_brutal": 3, "desaparecer_nas_sombras": 5},
         "monster_ability_cooldowns": {"algo": 2}}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    r.master_manual_event.set()
    await task
    check("golpe_brutal andou p/ 2", m["ability_cooldowns"]["golpe_brutal"] == 2)
    check("desaparecer_nas_sombras andou p/ 4", m["ability_cooldowns"]["desaparecer_nas_sombras"] == 4)
    check("monster_ability_cooldowns também andou", m["monster_ability_cooldowns"]["algo"] == 1)
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    r.master_manual_event.set()
    await task
    check("golpe_brutal andou p/ 1", m["ability_cooldowns"]["golpe_brutal"] == 1)
    check("desaparecer_nas_sombras andou p/ 3", m["ability_cooldowns"]["desaparecer_nas_sombras"] == 3)

    m2 = {"id": "g2", "name": "Bug2", "hp": 20, "pos": [3, 3], "size": [1, 1],
          "control_mode": "manual", "ability_cooldowns": {"golpe_brutal": 0}}
    r.monsters = {"g2": m2}
    task = asyncio.create_task(r._master_manual_window(m2))
    await asyncio.sleep(0)
    r.master_manual_event.set()
    await task
    check("recarga não fica negativa", m2["ability_cooldowns"]["golpe_brutal"] == 0)

    m3 = {"id": "g3", "name": "Bug3", "hp": 20, "pos": [4, 4], "size": [1, 1],
          "control_mode": "manual", "special_abilities": [ab_ds], "ability_cooldowns": {}}
    r.monsters = {"g3": m3}
    r._em_escuridao = lambda mm: True
    check("ativou p/ testar expiração", await r._ativar_desaparecer_sombras(m3) is True)
    check("oculto setado", m3.get("oculto_sombras") is True)
    task = asyncio.create_task(r._master_manual_window(m3))
    await asyncio.sleep(0)
    r.master_manual_event.set()
    await task
    check("oculto_sombras expira na janela seguinte", "oculto_sombras" not in m3)

    print("\n[36c] _expirar_oculto_sombras — comportamento da IA preservado")
    m4 = {"id": "g4", "name": "Bug4"}
    m4["oculto_sombras"] = True
    await r._expirar_oculto_sombras(m4)
    check("flag some quando presente", "oculto_sombras" not in m4)
    m5 = {"id": "g5", "name": "Bug5"}
    await r._expirar_oculto_sombras(m5)
    check("sem flag não quebra", "oculto_sombras" not in m5)

    print("\n[37] _upkeep_inicio_turno_monstro — devolve se o monstro pode agir")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    # Os processadores de efeito são neutralizados aqui de propósito: esta seção
    # testa a RAMIFICAÇÃO do prólogo (age × perde o turno), não o que cada efeito
    # faz. Sem os stubs, um dict de monstro mínimo pode estourar dentro deles por
    # falta de campos. A seção [39] prova que veneno e Réquiem são de fato
    # chamados pela janela do Manual.
    async def _noop(*a, **k): pass
    r._processar_mare_viva_turno = _noop
    r._processar_venenos_turno = _noop
    r._processar_mods_magia_turno = _noop
    r._processar_requiem_turno = _noop
    async def _sem_status(mm, vivos): return None
    r._status_monstro_turno = _sem_status
    async def _sem_enredo(mm): return False
    r._processar_enredado_turno = _sem_enredo
    def _mon(**kw):
        base = {"id": "g1", "name": "Coisa", "type": "goblin", "hp": 10, "max_hp": 10,
                "pos": [2, 2], "size": [1, 1], "movement": 4}
        base.update(kw); return base
    # saudável → pode agir
    m = _mon()
    check("monstro saudável pode agir", await r._upkeep_inicio_turno_monstro(m, [m]) is True)
    # petrificado → perde o turno
    m = _mon(petrificado=True)
    check("petrificado perde o turno", await r._upkeep_inicio_turno_monstro(m, [m]) is False)
    # preso em rede → perde o turno e o flag é consumido
    m = _mon(perde_turno=True)
    check("rede perde o turno", await r._upkeep_inicio_turno_monstro(m, [m]) is False)
    check("rede consome o flag", m["perde_turno"] is False)
    # inabalavel ignora a rede
    m = _mon(perde_turno=True, special_abilities=[{"id": "inabalavel", "action_type": "passiva"}])
    check("inabalavel ignora a rede", await r._upkeep_inicio_turno_monstro(m, [m]) is True)
    check("inabalavel limpa o flag", "perde_turno" not in m)
    # morto durante o upkeep → não age
    m = _mon(hp=0)
    check("monstro morto não age", await r._upkeep_inicio_turno_monstro(m, [m]) is False)

    print("\n[37b] lobisomem regenera dentro do prólogo")
    # Mesmos stubs de [37] seguem valendo: a regeneração é inline no prólogo.
    m = _mon(type="lobisomem", hp=8, max_hp=30)
    check("regenerou +2", (await r._upkeep_inicio_turno_monstro(m, [m])) is True and m["hp"] == 10)
    check("fúria abaixo de 12 PV", m.get("furia_lobisomem") is True)
    m = _mon(type="lobisomem", hp=8, max_hp=30, regeneracao_bloqueada=True)
    await r._upkeep_inicio_turno_monstro(m, [m])
    check("regeneração bloqueada não cura", m["hp"] == 8)
    check("bloqueio é consumido", "regeneracao_bloqueada" not in m)

    print("\n[38] turno perdido não abre a janela do Manual")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    # petrificado_rodadas > 0: todo call site real (ex.: linha ~17495 e a
    # habilidade de monstro em ~21148) sempre grava os dois campos juntos —
    # sem isso, `_processar_venenos_turno` (chamado dentro do prólogo, ANTES
    # da checagem de petrificado) decrementa o default 0 pra -1, zera pra 0 e
    # já desfaz a petrificação no mesmo upkeep.
    m = {"id": "g1", "name": "Estátua", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "petrificado": True, "petrificado_rodadas": 2}
    r.monsters = {"g1": m}
    await r._master_manual_window(m)          # não bloqueia: o turno foi consumido
    check("não setou master_manual_mid", r.master_manual_mid is None)
    check("não criou a janela", r.master_manual_event is None)
    check("não montou cargas de ataque", "master_attack_charges" not in m)

    print("\n[38b] monstro são abre a janela normalmente")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("abriu a janela", r.master_manual_mid == "g1")
    check("montou cargas", m.get("master_attack_charges") == {0: 1})
    r.master_manual_event.set()
    await task

    print("\n[38c] a janela passa [m] como alive_monsters, igual à gm_phase(monster)")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    visto = {}
    async def espiao(mm, vivos): visto["vivos"] = vivos; return None
    r._status_monstro_turno = espiao
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    outro = {"id": "g2", "name": "Outro", "type": "goblin", "hp": 10, "max_hp": 10,
             "pos": [8, 8], "size": [1, 1], "movement": 4}
    r.monsters = {"g1": m, "g2": outro}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("recebeu só o próprio monstro", visto.get("vivos") == [m])
    r.master_manual_event.set()
    await task

    print("\n[39] veneno e Réquiem alcançam o monstro do mestre")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    ticou = {"veneno": 0, "requiem": 0}
    async def fake_veneno(mm): ticou["veneno"] += 1
    async def fake_requiem(mm): ticou["requiem"] += 1
    r._processar_venenos_turno = fake_veneno
    r._processar_requiem_turno = fake_requiem
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("veneno ticou no Manual", ticou["veneno"] == 1)
    check("Réquiem ticou no Manual", ticou["requiem"] == 1)
    r.master_manual_event.set()
    await task

    print("\n[39b] paridade: recarga NÃO anda no turno perdido")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Estátua", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "petrificado": True, "petrificado_rodadas": 2,
         "ability_cooldowns": {"golpe_brutal": 3},
         "monster_ability_cooldowns": {"hero_warrior_mira_certeira": 2}}
    r.monsters = {"g1": m}
    await r._master_manual_window(m)
    check("ability_cooldowns intacto no turno perdido", m["ability_cooldowns"]["golpe_brutal"] == 3)
    check("monster_ability_cooldowns intacto", m["monster_ability_cooldowns"]["hero_warrior_mira_certeira"] == 2)

    print("\n[39c] recarga anda no turno normal (não regrediu)")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}],
         "ability_cooldowns": {"golpe_brutal": 3}}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("recarga andou no turno normal", m["ability_cooldowns"]["golpe_brutal"] == 2)
    r.master_manual_event.set()
    await task

    print("\n[39d] paridade: rede (perde_turno) também fecha a janela do Manual")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    # Ao contrário do petrificado ([38]/[39b]), o `perde_turno` não é tocado por
    # nenhum processador do prólogo (_processar_venenos_turno só mexe em
    # petrificado_rodadas/cego_rodadas) — então o dict mínimo de [38b]/[39c]
    # já basta, sem campo extra.
    m = {"id": "g1", "name": "Preso na rede", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "perde_turno": True}
    r.monsters = {"g1": m}
    await r._master_manual_window(m)              # não bloqueia: o turno foi consumido
    check("não setou master_manual_mid (rede)", r.master_manual_mid is None)
    check("flag perde_turno consumido", m["perde_turno"] is False)

    print("\n[40] invariante — sem mestre, monstro auto não vê nada do Manual")
    r = playing_room_com_mestre()
    r.connections.pop("m1", None)          # mestre desconectado
    check("_mestre_ativo() falso", r._mestre_ativo() is False)
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "auto", "master_moves_left": 6,
         # ability real (save+dc → ativável) p/ que só a guarda impeça o efeito
         "special_abilities": [{"id": "petrificar", "name": "Petrificar",
                                 "action_type": "acao", "save": "fort", "dc": 13}],
         "ability_cooldowns": {}}
    r.monsters = {"g1": m}
    r.master_manual_mid = None
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("atacar_monstro não age fora da janela",
          "master_attack_charges" not in m and m.get("_master_acted") is None)
    # "petrificar" é save+dc (_habilidade_ativavel_manual aceita) e hA está viva
    # e adjacente ([2,3]×[2,2]) — só a guarda (monster_id != master_manual_mid)
    # impede o efeito; sem isso _master_acted seria setado.
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("usar_habilidade (ability ativável de verdade) não age fora da janela",
          m.get("_master_acted") is None)
    # master_moves_left=6 garante que o orçamento (budget<=0) não mascare a guarda.
    await r.handle_mestre_mover_monstro_para("m1", "g1", 3, 2)
    check("mover_monstro_para (com orçamento de verdade) não move fora da janela",
          m["pos"] == [2, 2] and m["master_moves_left"] == 6)

    print("\n[40b] invariante — mesmo, para usar_item/set_modo/set_alvo/implantar_reforco")
    # Nuance sobre os handlers guardados por `monster_id != master_manual_mid`
    # (usar_item aqui, e atacar/mover/usar_habilidade acima): quem realmente
    # barra o mestre OFFLINE é _on_master_disconnect, que fecha a janela
    # (master_manual_mid vira None) — a guarda em si só recusa um monstro que
    # não é o da janela aberta. Isso fica explícito no subteste dedicado de
    # encerrar_monstro logo abaixo: janela aberta em g1, pedido de encerrar g2.
    r = playing_room_com_mestre()
    r.connections.pop("m1", None)
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "auto", "equipment_consumables": [{"id": "pocao1", "effect": "heal"}]}
    r.monsters = {"g1": m}
    r.master_manual_mid = None
    r._errs.clear()
    await r.handle_mestre_usar_item("m1", "g1", "pocao1", None, None, None)
    check("usar_item não mexeu no monstro (guarda master_manual_mid)",
          m["hp"] == 25 and len(m["equipment_consumables"]) == 1
          and m.get("_master_acted") is None)

    # handle_mestre_encerrar_monstro: contrato real da guarda é recusar um
    # monstro que NÃO é o da janela aberta (não "recusar mestre offline" —
    # isso é papel de _on_master_disconnect). Janela aberta em g1; pedimos
    # para encerrar g2 — precisa ser recusado (evento intocado, mid intocado).
    r2 = playing_room_com_mestre()
    r2.master_manual_mid = "g1"
    r2.master_manual_event = asyncio.Event()
    r2.monsters = {"g1": {"id": "g1", "hp": 10}, "g2": {"id": "g2", "hp": 10}}
    await r2.handle_mestre_encerrar_monstro("m1", "g2")
    check("encerrar_monstro recusa monstro fora da janela aberta",
          r2.master_manual_mid == "g1" and not r2.master_manual_event.is_set())

    # handle_mestre_set_modo: guarda `pid != master_pid or not _mestre_ativo()`.
    # master_pid sobrevive à queda do mestre durante a partida (só
    # self.connections perde a entrada), então sem o `_mestre_ativo()` a
    # checagem de pid sozinha não bastaria — é essa checagem que bloqueia aqui.
    r.monsters["g1"]["control_mode"] = "auto"
    await r.handle_mestre_set_modo("m1", ["g1"], "manual")
    check("set_modo não muda control_mode sem mestre ativo",
          r.monsters["g1"]["control_mode"] == "auto")

    # handle_mestre_set_alvo: mesma guarda; escreve master_target_id no monstro.
    r.monsters["g1"].pop("master_target_id", None)
    await r.handle_mestre_set_alvo("m1", ["g1"], "hA")
    check("set_alvo não seta master_target_id sem mestre ativo",
          "master_target_id" not in r.monsters["g1"])

    # handle_mestre_implantar_reforco: guarda `pid != master_pid or not
    # self._mestre_ativo()` — bloqueia mesmo com pid == master_pid, pois
    # _mestre_ativo() é falso. Reserva com estoque real (>0) garante que a
    # falta de reforço não mascare a guarda.
    r.master_reserve = {"goblin": 2}
    await r.handle_mestre_implantar_reforco("m1", "goblin", 4, 4)
    check("implantar_reforco não criou monstro nem gastou reserva",
          len(r.monsters) == 1 and r.master_reserve["goblin"] == 2)

    print("\n[40c] contraprova — com mestre CONECTADO, set_modo/set_alvo agem de verdade")
    # Sem isto, uma guarda futura que rejeitasse TUDO ainda deixaria [40b] verde.
    r = playing_room_com_mestre()          # mestre "m1" conectado (r.connections["m1"] setado)
    check("_mestre_ativo() verdadeiro", r._mestre_ativo() is True)
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "auto"}
    r.monsters = {"g1": m}
    await r.handle_mestre_set_modo("m1", ["g1"], "manual")
    check("set_modo muda control_mode com mestre ativo", m["control_mode"] == "manual")
    await r.handle_mestre_set_alvo("m1", ["g1"], "hA")
    check("set_alvo seta master_target_id com mestre ativo", m.get("master_target_id") == "hA")

    print("\n[41] relógio de inatividade e ausência de turno duplo")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 0.05
    ia_calls = {"n": 0}
    async def fake_gm_phase(mm): ia_calls["n"] += 1
    r.gm_phase = fake_gm_phase
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [9, 9], "alive": True,
                        "connected": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 12, "max_hp": 12,
         "pos": [1, 1], "size": [1, 1], "movement": 3, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    # (a) mestre não faz nada → IA resolve
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0.15)
    await task
    check("(a) timeout sem ação chama a IA", ia_calls["n"] == 1)
    # (b) mestre agiu → timeout apenas fecha, sem turno duplo
    ia_calls["n"] = 0
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    r.master_manual_mid = "g1"
    await r.handle_mestre_mover_monstro_para("m1", "g1", 2, 1)
    await asyncio.sleep(0.15)
    await task
    check("(b) timeout após ação do mestre NÃO chama a IA", ia_calls["n"] == 0)
    check("(b) o monstro andou", m["pos"] == [2, 1])

    print("\n[41b] deadline é empurrado a cada ação")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 60
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [9, 9], "alive": True,
                        "connected": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 12, "max_hp": 12,
         "pos": [1, 1], "size": [1, 1], "movement": 3, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    d1 = r.master_manual_deadline
    await asyncio.sleep(0.02)
    r.master_manual_mid = "g1"
    await r.handle_mestre_mover_monstro_para("m1", "g1", 2, 1)
    check("deadline empurrado para frente", r.master_manual_deadline > d1)
    r.master_manual_event.set()
    await task

    print("\n[41c] envenenar a arma de graça também conta como o mestre ter agido")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Aranha", "hp": 12, "max_hp": 12, "pos": [1, 1],
         "size": [1, 1], "special_abilities": [{"id": "envenenar_arma"}],
         "attacks": [{"name": "Ferrão", "num_attacks": 1}],
         "equipment_consumables": [{"id": "v1", "effect": "coat_poison",
                                     "veneno_id": "veneno_fraco", "name": "Veneno"}]}
    r.monsters = {"g1": m}
    r.master_manual_mid = "g1"
    async def fake_envenenar(mm): return True
    r._envenenar_arma_do_inventario = fake_envenenar
    m.pop("_master_touched", None)
    await r.handle_mestre_usar_item("m1", "g1", "v1", None, None, None)
    check("veneno_livre marca _master_touched", m.get("_master_touched") is True)

    print("\n[41d] _master_touched marcado mesmo com 0 casas andadas (1º passo bloqueado)")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 12, "max_hp": 12,
         "pos": [1, 1], "size": [1, 1], "movement": 3, "control_mode": "manual",
         "master_moves_left": 3, "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    r.master_manual_mid = "g1"
    async def fake_commit_step(mm, nx, ny): return False
    r._commit_monster_step = fake_commit_step
    await r.handle_mestre_mover_monstro_para("m1", "g1", 2, 1)
    check("_master_touched setado mesmo sem andar", m.get("_master_touched") is True)
    check("posição não mudou (0 casas andadas)", m["pos"] == [1, 1])

    print("\n[42] payload master_manual")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 60
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [9, 9], "alive": True,
                        "connected": True, "hp": 10}}
    m = {"id": "g1", "name": "Lobisomem", "type": "goblin", "hp": 30, "max_hp": 30,
         "pos": [1, 1], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Garras", "num_attacks": 2},
                     {"name": "Mordida", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    check("sem janela, bloco é None", r._master_manual_payload() is None)
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    bloco = r._master_manual_payload()
    check("mid",           bloco["mid"] == "g1")
    check("moves",         bloco["moves_left"] == 4 and bloco["moves_max"] == 4)
    check("acao livre",    bloco["acao"] is None and bloco["bonus"] is False)
    check("cargas",        bloco["attack_charges"] == {"0": 2, "1": 1})
    check("restante > 0",  bloco["restante"] > 0)
    r.master_manual_event.set()
    await task
    check("janela fechada, bloco volta a None", r._master_manual_payload() is None)

    print("\n[43] teste livre: re-selecionar o mesmo monstro devolve o movimento DE VERDADE")
    # Há DOIS contadores de passo: master_moves_left (o que a UI mostra) e
    # _water_moves_left (o que _commit_monster_step debita). Renovar só o
    # primeiro trava o monstro em silêncio — sem erro, com casas azuis na tela.
    r = playing_room_com_mestre()
    r.test_mode = True
    m = {"id": "g1", "name": "Escorpião", "type": "goblin", "hp": 20, "max_hp": 20,
         "pos": [1, 1], "size": [1, 1], "movement": 3, "control_mode": "manual",
         "attacks": [{"name": "Ferrão", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    await r.handle_mestre_selecionar_teste("m1", "g1")
    check("1ª seleção dá movimento", m["master_moves_left"] == 3)
    await r.handle_mestre_mover_monstro_para("m1", "g1", 4, 1)
    check("andou as 3 casas", m["pos"] == [4, 1])
    check("orçamento por terreno zerado", m.get("_water_moves_left") == 0)
    await r.handle_mestre_selecionar_teste("m1", "g1")
    check("2ª seleção devolve master_moves_left", m["master_moves_left"] == 3)
    check("2ª seleção renova _water_moves_left", m.get("_water_moves_left", 0) > 0)
    check("2ª seleção limpa _moved_this_turn", m.get("_moved_this_turn") is False)
    await r.handle_mestre_mover_monstro_para("m1", "g1", 7, 1)
    check("anda de novo após re-selecionar", m["pos"] == [7, 1])

    print("\n[43b] seleção livre também rearma ação, bônus e cargas")
    r = playing_room_com_mestre()
    r.test_mode = True
    m = {"id": "g1", "name": "Lobo", "type": "goblin", "hp": 20, "max_hp": 20,
         "pos": [1, 1], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Garras", "num_attacks": 2}]}
    r.monsters = {"g1": m}
    m["_master_acted"] = True; m["_master_bonus_acted"] = True
    m["_master_acao_tipo"] = "ataque"; m["_ja_executou_acao"] = True
    m["master_attack_charges"] = {0: 0}
    await r.handle_mestre_selecionar_teste("m1", "g1")
    check("ação principal liberada",  m.get("_master_acted") is False)
    check("ação bônus liberada",      m.get("_master_bonus_acted") is False)
    check("tipo de ação limpo",       m.get("_master_acao_tipo") is None)
    check("_ja_executou_acao limpo",  not m.get("_ja_executou_acao"))
    check("cargas remontadas",        m["master_attack_charges"] == {0: 2})

    print("\n[43c] selecionar exige mestre e sessão de teste")
    r = playing_room_com_mestre()   # sem test_mode
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 9, "max_hp": 9,
         "pos": [1, 1], "size": [1, 1], "movement": 3, "control_mode": "auto"}
    r.monsters = {"g1": m}
    await r.handle_mestre_selecionar_teste("m1", "g1")
    check("fora do teste livre não abre janela", r.master_manual_mid is None)
    r.test_mode = True
    await r.handle_mestre_selecionar_teste("h1", "g1")
    check("não-mestre não abre janela", r.master_manual_mid is None)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
