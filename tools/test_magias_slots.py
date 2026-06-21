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

    print(f"\n{'='*40}\nPASS: {PASS}  FAIL: {FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
