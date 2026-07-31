"""Sistema de maldições. Roda da raiz: python tools/test_maldicoes.py

Cobre a trava de item amaldiçoado (`maldicao_prende`): um item preso não pode
sair do slot por NENHUMA via — desequipar, largar no chão, vender, ou ser
empurrado por outro item equipado no mesmo slot.
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala():
    """Sala em masmorra, com grid livre — o largar precisa de casa adjacente."""
    r = S.GameRoom("MALD")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.push_state_or_city = noop; r.broadcast_city_state = noop
    r._checkpoint_savegame = lambda *a, **k: None
    r.phase = "playing"
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.grid_w = r.grid_h = 12
    r.rooms = [{"id": "r1", "x": 0, "y": 0, "w": 12, "h": 12, "locked": False, "doors": []}]
    p = S.make_player("p1", "Victor", "warrior", 0)
    p["pos"] = [5, 5]; p["gold"] = 500
    r.players["p1"] = p
    r.erros = []
    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r.erros.append(msg["msg"])
    r.send_to = cap
    return r, p

def anel(prende=True, mid="maos_tremulas", iid="anel_maldito"):
    return {"id": iid, "name": "Anel Maldito", "emoji": "💍", "item_slot": "ring",
            "kind": "ring", "bonuses": [], "buy_price": 100,
            "maldicao_id": mid, "maldicao_prende": prende}

def equipar(r, p, item, slot="ring1"):
    p["gear"][slot] = item
    r._apply_gear_effect(p, item, True)

def test_desequipar():
    print("\n[1] Desequipar item preso")
    r, p = sala()
    equipar(r, p, anel())
    asyncio.run(r.handle_unequip("p1", "ring1"))
    check("recusado", bool(r.erros) and p["gear"]["ring1"] is not None)

def test_largar():
    print("\n[2] Largar item preso no chão")
    r, p = sala()
    equipar(r, p, anel())
    asyncio.run(r.handle_drop_item("p1", "gear", None, "ring1"))
    check("recusado", p["gear"]["ring1"] is not None)
    check("nada foi para o chão", not r.ground_items)
    check("avisou o jogador", any("maldi" in e.lower() for e in r.erros))

def test_vender():
    print("\n[3] Vender item preso")
    r, p = sala()
    r.phase = "city"
    # acessório
    equipar(r, p, anel())
    ouro = p["gold"]
    asyncio.run(r.handle_shop_sell("p1", "ring1"))
    check("acessório: recusado", p["gear"]["ring1"] is not None and p["gold"] == ouro)
    # arma
    r2, p2 = sala(); r2.phase = "city"
    arma = {"id": "lamina_maldita", "name": "Lâmina Maldita", "item_slot": "weapon",
            "kind": "weapon", "die": "1d8", "stat": "str_", "buy_price": 90,
            "maldicao_id": "maos_tremulas", "maldicao_prende": True}
    equipar(r2, p2, arma, "weapon"); p2["weapon"] = dict(arma)
    asyncio.run(r2.handle_shop_sell("p1", "weapon"))
    check("arma: recusada", (p2["gear"]["weapon"] or {}).get("id") == "lamina_maldita")
    # armadura
    r3, p3 = sala(); r3.phase = "city"
    couro = {"id": "couro_maldito", "name": "Couro Maldito", "item_slot": "armor",
             "kind": "armor", "ac_bonus": 2, "bonuses": [], "buy_price": 80,
             "maldicao_id": "maos_tremulas", "maldicao_prende": True}
    equipar(r3, p3, couro, "armor")
    asyncio.run(r3.handle_shop_sell("p1", "armor"))
    check("armadura: recusada", p3["gear"]["armor"] is not None)

def test_empurrar():
    print("\n[4] Equipar outro item por cima do preso")
    r, p = sala()
    equipar(r, p, anel())
    equipar(r, p, anel(prende=False, mid="corpo_exausto", iid="anel_comum"), "ring2")
    outro = anel(prende=False, mid=None, iid="anel_simples")
    outro["maldicao_id"] = None; outro["name"] = "Anel Simples"
    p["bag"].append(outro)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("os dois anéis cheios: recusado",
          (p["gear"]["ring1"] or {}).get("id") == "anel_maldito")
    check("o anel novo continua na bolsa",
          any(i.get("id") == "anel_simples" for i in p["bag"]))

def test_nao_bloqueia_demais():
    print("\n[5] A trava não pode bloquear o que é legítimo")
    # slot livre no par: equipar não empurra ninguém
    r, p = sala()
    equipar(r, p, anel())
    novo = anel(prende=False, iid="anel_simples"); novo["maldicao_id"] = None
    p["bag"].append(novo)
    asyncio.run(r._executar_equip_from_bag("p1", len(p["bag"]) - 1))
    check("com ring2 livre, equipar funciona", p["gear"]["ring2"] is not None)

    # item amaldiçoado SEM prender sai normalmente
    r2, p2 = sala()
    equipar(r2, p2, anel(prende=False))
    asyncio.run(r2.handle_unequip("p1", "ring1"))
    check("maldição sem trava: desequipa normal", p2["gear"]["ring1"] is None)

    # curada a maldição, o item destrava
    r3, p3 = sala()
    it = anel()
    equipar(r3, p3, it)
    r3._remover_maldicao(p3, "maos_tremulas")
    check("sem a maldição, o item não prende mais",
          not r3._item_maldicao_vinculante(p3, it))
    asyncio.run(r3.handle_unequip("p1", "ring1"))
    check("depois de curar, desequipa", p3["gear"]["ring1"] is None)

    # item comum nunca é afetado
    r4, p4 = sala()
    comum = {"id": "anel_vita", "name": "Anel", "item_slot": "ring", "kind": "ring",
             "bonuses": [], "buy_price": 50}
    equipar(r4, p4, comum)
    asyncio.run(r4.handle_drop_item("p1", "gear", None, "ring1"))
    check("item comum é largado normalmente", p4["gear"]["ring1"] is None)

def main():
    test_desequipar(); test_largar(); test_vender()
    test_empurrar(); test_nao_bloqueia_demais()
    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
