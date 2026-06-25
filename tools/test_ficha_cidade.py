"""Ficha na cidade — equipar/desequipar/reordenar com broadcast ciente da fase.
  • Equipar na fase 'city' move bag→gear e emite city_state (não game_state).
  • Desequipar na cidade devolve à bolsa e emite city_state.
  • reorder_bag reordena a bolsa (com clamp de índices fora do intervalo).
  • Equipar na masmorra ('playing') continua emitindo game_state (não regrediu).
Roda da raiz: python tools/test_ficha_cidade.py"""
import asyncio, sys, os
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, SHOP_WEAPONS

def shop_w(wid):
    return deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == wid))

def setup(phase="city"):
    r = GameRoom("TEST")
    calls = {"push_state": 0, "city": 0}
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    async def cap_push(*a, **k): calls["push_state"] += 1
    async def cap_city(*a, **k): calls["city"] += 1
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.push_state = cap_push; r.broadcast_city_state = cap_city
    r.send_to = cap_send
    r.phase = phase
    r._calls = calls; r._errs = errs
    return r

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # [1] Equipar na cidade → city_state, item em gear
    print("\n[1] Equipar na fase city")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = [shop_w("longsword")]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou (gear.weapon=longsword)", (w["gear"].get("weapon") or {}).get("id") == "longsword")
    check("emitiu city_state", r._calls["city"] >= 1)
    check("NÃO emitiu game_state", r._calls["push_state"] == 0)

    # [2] Desequipar na cidade → volta p/ bolsa
    print("\n[2] Desequipar na fase city")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = []
    w["gear"]["head"] = {"id": "helm", "name": "Elmo", "emoji": "⛑", "item_slot": "head"}
    await r.handle_unequip("p1", "head")
    check("head vazio após desequipar", w["gear"].get("head") is None)
    check("item voltou p/ bolsa", any((it or {}).get("id") == "helm" for it in w["bag"]))
    check("emitiu city_state", r._calls["city"] >= 1 and r._calls["push_state"] == 0)

    # [3] reorder_bag (incl. clamp)
    print("\n[3] reorder_bag")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    a = {"id": "a"}; b = {"id": "b"}; c = {"id": "c"}
    w["bag"] = [a, b, c]
    await r.handle_reorder_bag("p1", 0, 2)
    check("moveu A para o fim", [it["id"] for it in w["bag"]] == ["b", "c", "a"])
    await r.handle_reorder_bag("p1", 2, 0)
    check("voltou A p/ início", [it["id"] for it in w["bag"]] == ["a", "b", "c"])
    await r.handle_reorder_bag("p1", 10, 0)
    check("from inválido = no-op", [it["id"] for it in w["bag"]] == ["a", "b", "c"])
    await r.handle_reorder_bag("p1", 0, 99)
    check("to clampa p/ o fim", [it["id"] for it in w["bag"]] == ["b", "c", "a"])
    check("emitiu city_state", r._calls["city"] >= 1)

    # [4] Não-regressão: equipar na masmorra → game_state
    print("\n[4] Equipar na fase playing (não-regressão)")
    r = setup("playing")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = [shop_w("longsword")]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou na masmorra", (w["gear"].get("weapon") or {}).get("id") == "longsword")
    check("emitiu game_state", r._calls["push_state"] >= 1)
    check("NÃO emitiu city_state", r._calls["city"] == 0)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
