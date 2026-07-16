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
    ok7 = await r.add_player(FakeWS(), "h6", "Setimo")
    check("7º herói barrado", ok7 is False)

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

    print("\n[8] janela Manual: mover, atacar e encerrar")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    ataques = {"n": 0}
    async def fake_atk(m, atk_def, target_obj):
        ataques["n"] += 1; return True
    r._execute_one_monster_attack = fake_atk
    async def fake_commit(m, nx, ny): m["pos"] = [nx, ny]; return True
    r._commit_monster_step = fake_commit
    r._monster_can_occupy = lambda m, nx, ny, facing=None: True
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "control_mode": "manual",
         "attacks": [{"name": "garra", "damage": "1d4"}]}
    r.monsters = {"g1": m}
    r.master_manual_mid = "g1"
    m["master_moves_left"] = r.MASTER_MANUAL_MOVE
    m["_master_acted"] = False
    hero = {"id": "hA", "pos": [6, 4], "alive": True, "hp": 10}
    r.players = {"hA": hero}
    await r.handle_mestre_mover_monstro("m1", "g1", 1, 0)
    check("monstro moveu 1 casa", m["pos"] == [5, 4])
    check("gastou 1 de movimento", m["master_moves_left"] == r.MASTER_MANUAL_MOVE - 1)
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("ataque resolvido", ataques["n"] == 1)
    check("marcou ataque usado", m["_master_acted"] is True)
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("2º ataque recusado", ataques["n"] == 1)
    r.master_manual_event = asyncio.Event()
    await r.handle_mestre_encerrar_monstro("m1", "g1")
    check("Event setado ao encerrar", r.master_manual_event.is_set())
    check("janela limpa", r.master_manual_mid is None)
    r._errs.clear()
    await r.handle_mestre_mover_monstro("m1", "g1", -1, 0)
    check("mover fora da janela recusado", m["pos"] == [5, 4])

    print("\n[8b] mover recusado quando _commit_monster_step falha")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    async def fake_commit_false(m, nx, ny): return False
    r._commit_monster_step = fake_commit_false
    r._monster_can_occupy = lambda m, nx, ny, facing=None: True
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "control_mode": "manual"}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"; m["master_moves_left"] = 3
    r._errs.clear()
    await r.handle_mestre_mover_monstro("m1", "g1", 1, 0)
    check("não moveu (commit False)", m["pos"] == [4, 4])
    check("não gastou movimento", m["master_moves_left"] == 3)

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
    check("troll legado cr 1.5", S.monster_cr(_by("troll")) == 1.5)
    check("dragon legado cr 5", S.monster_cr(_by("dragon")) == 5.0)
    check("todos MONSTER_DEFS resolvem cr>0", all(S.monster_cr(d) > 0 for d in S.MONSTER_DEFS))

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

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
