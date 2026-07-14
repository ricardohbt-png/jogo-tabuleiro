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

    print("\n[11] mestre cai: janela Manual aberta é fechada")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"
    r.master_manual_mid = "g1"
    r.master_manual_event = asyncio.Event()
    await r._on_master_disconnect()
    check("event setado ao cair", r.master_manual_event.is_set())

    print("\n[11b] _on_master_disconnect sem janela aberta é seguro")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"
    r.master_manual_mid = None
    r.master_manual_event = None
    await r._on_master_disconnect()   # não deve lançar exceção
    check("no-op sem janela", r.master_manual_mid is None)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
