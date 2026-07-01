"""Testes do sistema de magias conhecidas + slots com regeneração (Pedro/Lewis).
Roda da raiz: python tools/test_magias_slots.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, SLOTS_POR_NIVEL, SLOT_REGEN, slots_max_para

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.round_num = 1
    r.phase = "playing"                     # _is_turn exige phase=="playing"
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]   # piso vazio
    r._tem_linha_de_visao = lambda *a, **k: True    # sem paredes nos testes
    return r

def mk_mage(r, level=1):
    p = make_player("p1", "Pedro", "mage", 0)
    p["level"] = level
    r.players["p1"] = p
    return p

async def main():
    print("\n[1] Tabela de slots por nível + helpers")
    r = setup(); p = mk_mage(r, 1)
    check("nível 1 → 2 slots de 1º", slots_max_para(p)["primeiro"] == 2)
    check("nível 1 → 0 de 2º", slots_max_para(p)["segundo"] == 0)
    check("init cooldown vazio", p["slots_cooldown"] == {"primeiro": [], "segundo": [], "terceiro": []})
    check("disponíveis 1º = 2", r._slots_disponiveis(p, "primeiro") == 2)

    print("\n[2] Gastar slot adiciona cooldown correto")
    r.round_num = 5
    r._gastar_slot(p, "primeiro")
    check("1 cooldown registrado", len(p["slots_cooldown"]["primeiro"]) == 1)
    check("ready_at = round + 10", p["slots_cooldown"]["primeiro"][0] == 15)
    check("disponíveis caiu p/ 1", r._slots_disponiveis(p, "primeiro") == 1)

    print("\n[3] Regeneração após REGEN rodadas")
    r.round_num = 14
    check("ainda indisponível na rodada 14", r._slots_disponiveis(p, "primeiro") == 1)
    r.round_num = 15
    check("volta na rodada 15", r._slots_disponiveis(p, "primeiro") == 2)
    check("cooldown podado", p["slots_cooldown"]["primeiro"] == [])

    print("\n[4] Recarga total (descanso)")
    r.round_num = 1
    r._gastar_slot(p, "primeiro"); r._gastar_slot(p, "primeiro")
    check("2 gastos", r._slots_disponiveis(p, "primeiro") == 0)
    r._recarregar_slots(p)
    check("recarga zera cooldown", r._slots_disponiveis(p, "primeiro") == 2)

    print("\n[5] handle_magia: exige magia conhecida e gasta slot")
    r = setup(); p = mk_mage(r, 1)
    r.round_num = 1
    erros = []
    async def cap_send(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_send
    r.player_order = ["p1"]; r.turn_index = 0
    p["action_done"] = False; p["fome"] = 10; p["sede"] = 10
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("recusa magia não conhecida", any("conhece" in e.lower() for e in erros))
    # conhecendo a magia, lança e gasta slot
    p["magias_conhecidas"] = ["bola_fogo"]
    p["action_done"] = False; erros.clear()
    disp_antes = r._slots_disponiveis(p, "primeiro")
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("gastou 1 slot de 1º", r._slots_disponiveis(p, "primeiro") == disp_antes - 1)
    # sem slots → recusa
    p["action_done"] = False; erros.clear()
    p["slots_cooldown"]["primeiro"] = [r.round_num + 10, r.round_num + 10]  # 2 gastos (max no nv1)
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("recusa sem slot livre", any("slot" in e.lower() for e in erros))

    print("\n[6] Recarga total ao voltar para a cidade")
    r = setup(); p = mk_mage(r, 1)
    r.player_order = ["p1"]
    r.round_num = 3
    r._gastar_slot(p, "primeiro")
    check("1 slot gasto antes da cidade", r._slots_disponiveis(p, "primeiro") == 1)
    r._gerar_loja_pergaminhos = lambda: None     # evita dependências da loja
    r._cancelar_timer_turno  = lambda: None
    await r._voltar_para_cidade()
    check("slots recarregados na cidade", r._slots_disponiveis(p, "primeiro") == 2)

    print("\n[7] Level-up concede slot cheio + enfileira escolha; bloqueia end_turn")
    r = setup(); p = mk_mage(r, 1)
    r.player_order = ["p1"]; r.turn_index = 0
    prompts = []
    async def cap_send2(pid, m):
        if m.get("type") == "spell_pick_prompt": prompts.append(m)
    r.send_to = cap_send2
    p["xp"] = 999   # garante subir de nível
    await r._check_level_up(p)
    check("subiu para nível 2", p["level"] == 2)
    check("slot novo de 1º entra cheio (3)", r._slots_disponiveis(p, "primeiro") == 3)
    check("fila de escolha tem 1 círculo", p["pending_spell_pick"] == ["primeiro"])
    check("enviou spell_pick_prompt", len(prompts) == 1 and prompts[0]["circulo"] == "primeiro")
    # end_turn bloqueado enquanto há escolha pendente
    erros = []
    async def cap_err(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err
    r.animados_phase_pid = None
    await r.handle_end_turn("p1")
    check("end_turn bloqueado com escolha pendente", any("magia" in e.lower() for e in erros))

    print("\n[8] set_known_spells: validação e persistência")
    r = setup(); r.phase = "lobby"
    p = make_player("p1", "Pedro", "mage", 0); p["level"] = 1
    r.players["p1"] = p
    async def noop_lobby(*a, **k): pass
    r.broadcast_lobby = noop_lobby
    erros = []
    async def cap_err3(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err3
    await r.handle_set_known_spells("p1", ["bola_fogo"])       # contagem errada
    check("recusa != 2 magias", any("2 magias" in e or "exatamente" in e.lower() for e in erros))
    erros.clear()
    await r.handle_set_known_spells("p1", ["bola_fogo", "relampago"])
    check("aceita 2 magias de 1º da classe", p["magias_conhecidas"] == ["bola_fogo", "relampago"])

    print("\n[9] escolher_magia_nivel adiciona magia e esvazia a fila")
    r = setup(); p = mk_mage(r, 2)
    p["magias_conhecidas"] = ["bola_fogo", "relampago"]
    p["pending_spell_pick"] = ["primeiro"]
    erros = []
    async def cap_err4(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err4
    await r.handle_escolher_magia_nivel("p1", "id_que_nao_existe")
    check("recusa magia inválida", len(erros) >= 1)
    nova = next(mid for mid, m in server.GRIMORIO.items()
                if "mage" in m.get("classe", []) and m.get("circulo") == "primeiro"
                and mid not in p["magias_conhecidas"])
    await r.handle_escolher_magia_nivel("p1", nova)
    check("magia adicionada às conhecidas", nova in p["magias_conhecidas"])
    check("fila esvaziada", p["pending_spell_pick"] == [])

    print(f"\n{'='*40}\nPASS: {PASS}  FAIL: {FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
