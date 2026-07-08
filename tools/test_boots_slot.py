"""Slot de bota (9º slot de equipamento) — infraestrutura apenas, sem itens novos.
  • GEAR_SLOTS inclui "boots"; make_player já nasce com gear["boots"]=None.
  • Equipar um item item_slot="boots" da bolsa vai para gear["boots"].
  • Desequipar bota devolve à bolsa (mesmo fluxo de handle_unequip).
  • Trocar a bota equipada por outra devolve a antiga à bolsa.
  • Conflito de arma de 2 mãos continua intacto com o slot novo (não-regressão).
Roda da raiz: python tools/test_boots_slot.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, GEAR_SLOTS, GEAR_BONUS_SLOTS

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
    print("\n[1] GEAR_SLOTS inclui boots")
    check("9 slots ao todo", len(GEAR_SLOTS) == 9)
    check("boots está em GEAR_SLOTS", "boots" in GEAR_SLOTS)

    print("\n[2] make_player nasce com boots vazio")
    p = make_player("p1", "Richard", "paladin", 0)
    check("gear tem a chave boots", "boots" in p["gear"])
    check("boots começa vazio", p["gear"]["boots"] is None)

    print("\n[3] Equipar bota")
    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    bota = {"id": "boots_leather", "name": "Botas de Couro", "emoji": "👢",
            "item_slot": "boots", "ac_bonus": 1}
    w["bag"] = [bota]
    await r.handle_equip_from_bag("p1", 0)
    check("equipou (gear.boots=boots_leather)", (w["gear"].get("boots") or {}).get("id") == "boots_leather")
    check("saiu da bolsa", len(w["bag"]) == 0)
    check("sem erro", len(r._errs) == 0)

    print("\n[4] Desequipar bota")
    await r.handle_unequip("p1", "boots")
    check("boots vazio após desequipar", w["gear"].get("boots") is None)
    check("item voltou p/ bolsa", any((it or {}).get("id") == "boots_leather" for it in w["bag"]))

    print("\n[5] Trocar bota equipada por outra")
    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    bota1 = {"id": "boots_leather", "name": "Botas de Couro", "emoji": "👢", "item_slot": "boots", "ac_bonus": 1}
    bota2 = {"id": "boots_ferro", "name": "Botas de Ferro", "emoji": "👢", "item_slot": "boots", "ac_bonus": 2}
    w["gear"]["boots"] = bota1
    w["bag"] = [bota2]
    await r.handle_equip_from_bag("p1", 0)
    check("bota nova equipada", (w["gear"].get("boots") or {}).get("id") == "boots_ferro")
    check("bota antiga voltou p/ bolsa", any((it or {}).get("id") == "boots_leather" for it in w["bag"]))

    print("\n[6] Não-regressão: arma de 2 mãos x escudo continua bloqueando")
    r = setup("city")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gear"]["off_hand"] = {"id": "shield1", "name": "Escudo", "kind": "shield", "item_slot": "off_hand"}
    arma2m = {"id": "espada2m", "name": "Espada de Duas Mãos", "die": "2d6",
              "item_slot": "weapon", "two_handed": True}
    w["bag"] = [arma2m]
    await r.handle_equip_from_bag("p1", 0)
    check("bloqueou (weapon não mudou)", (w["gear"].get("weapon") or {}).get("id") != "espada2m")
    check("erro de 2 mãos enviado", any("2 mãos" in e for e in r._errs))

    print("\n[7] Não-regressão: 'Botas Velozes' com item_slot explícito não vira boots")
    # CHEST_ITEMS: item_slot="accessory" (cai no branch "item"); SHOP_MERCHANT:
    # item_slot="item" (idem) — ambos têm "bota" no nome; item_slot explícito
    # deve vencer o fallback de nome (name-sniffing só vale quando s é vazio).
    check("CHEST_ITEMS 'Botas Velozes' → item (não boots)",
          S.GameRoom._slot_category_for_item(
              {"id": "boots", "name": "Botas Velozes", "item_slot": "accessory",
               "effect": "spd", "value": 1}) == "item")
    check("SHOP_MERCHANT 'Botas Velozes' → item (não boots)",
          S.GameRoom._slot_category_for_item(
              {"id": "boots", "name": "Botas Velozes", "item_slot": "item",
               "effect": "spd", "value": 1}) == "item")
    check("item sem item_slot com 'bota' no nome ainda cai no fallback → boots",
          S.GameRoom._slot_category_for_item(
              {"id": "loot_bota_solta", "name": "Bota Surrada"}) == "boots")

    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    botas_velozes = {"id": "boots", "name": "Botas Velozes", "emoji": "👢",
                      "item_slot": "item", "effect": "spd", "value": 1}
    w["bag"] = [botas_velozes]
    await r.handle_equip_from_bag("p1", 0)
    check("Botas Velozes foi p/ item1/item2 (não gear.boots)", w["gear"].get("boots") is None)
    check("Botas Velozes equipou em item1 ou item2",
          (w["gear"].get("item1") or {}).get("id") == "boots" or (w["gear"].get("item2") or {}).get("id") == "boots")

    print("\n[8] Outras enumerações de slot (achadas na revisão de código) também incluem boots")
    check("boots está em GEAR_BONUS_SLOTS (recalculo de CA)", "boots" in GEAR_BONUS_SLOTS)

    r = setup("city")
    w = make_player("p1", "Richard", "paladin", 0); r.players["p1"] = w
    w["gold"] = 0
    w["gear"]["boots"] = {"id": "boots_leather", "name": "Botas de Couro", "emoji": "👢",
                           "item_slot": "boots", "ac_bonus": 1, "buy_price": 9}
    await r.handle_shop_sell("p1", "boots")
    check("venda de bota não deu erro (slot reconhecido)", len(r._errs) == 0)
    check("bota vendida saiu do gear", w["gear"].get("boots") is None)
    check("recebeu ouro pela venda", w["gold"] == 3)   # 9 // 3

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
