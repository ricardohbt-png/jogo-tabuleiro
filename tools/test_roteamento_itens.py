"""Teste do roteamento unificado de compra/loot — Sub-projeto B.

Modelo "bolsa-primeiro com resgate-equipar":
  1) bolsa tem espaço            → bolsa (NÃO auto-equipa, mesmo com slot livre);
  2) bolsa cheia + slot livre    → auto-equipa como resgate ('equipped');
  3) bolsa cheia + slots cheios  → recusa ('full'): compra estorna ouro, loot fica.

Exceções: munição (empilha) e consumíveis (só bolsa) seguem seus caminhos.
Roda da raiz: python tools/test_roteamento_itens.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, sys, os
from copy import deepcopy
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, WEAPONS, SHOP_WEAPONS, SHOP_ARMORS, SHOP_MERCHANT, SHOP_AMMO

def setup(city=True):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = "city" if city else "playing"
    r._errs = errs
    return r

def full_bag():
    return [deepcopy(next(i for i in SHOP_MERCHANT if i["id"] == "health_potion")) for _ in range(6)]

def bag_has(p, iid):
    return any(it and it.get("id") == iid for it in p["bag"])

def armor_item(iid):
    return deepcopy(next(a for a in SHOP_ARMORS if a["id"] == iid))

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # ── [1] Bolsa com espaço + slot livre → BOLSA (não auto-equipa) ──────────────
    print("\n[1] Compra com bolsa livre NÃO auto-equipa (vai pra bolsa)")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = []; w["gear"]["armor"] = None
    await r.handle_shop_buy("p1", "ferreiro_armor", "leather")
    check("armadura foi pra bolsa", bag_has(w, "leather"))
    check("slot de armadura continua vazio", w["gear"].get("armor") is None)
    check("sem erro", not r._errs)
    # arma com a mão vazia também vai pra bolsa (mudança de comportamento)
    w["gear"]["weapon"] = None; w["weapon"] = deepcopy(WEAPONS["unarmed"]); w["bag"] = []
    await r.handle_shop_buy("p1", "ferreiro_weapon", "longsword")
    check("arma com mão vazia foi pra bolsa", bag_has(w, "longsword"))
    check("mão principal continua vazia", w["gear"].get("weapon") is None)

    # ── [2] Bolsa cheia + slot de armadura livre → RESGATE-EQUIPA ────────────────
    print("\n[2] Bolsa cheia + slot livre → resgate-equipa (armadura)")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag(); w["gear"]["armor"] = None
    ac0 = w["ac"]
    await r.handle_shop_buy("p1", "ferreiro_armor", "leather")
    check("armadura resgate-equipada no slot", (w["gear"].get("armor") or {}).get("id") == "leather")
    check("CA aumentou (efeito aplicado)", w["ac"] > ac0)
    check("bolsa continua cheia (6)", len(w["bag"]) == 6)
    check("sem erro", not r._errs)

    # ── [2b] Bolsa cheia + mão vazia → resgate-equipa ARMA + sincroniza combate ──
    print("\n[2b] Bolsa cheia + mão vazia → resgate-equipa arma (sincroniza p['weapon'])")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag()
    w["gear"]["weapon"] = None; w["weapon"] = deepcopy(WEAPONS["unarmed"])
    await r.handle_shop_buy("p1", "ferreiro_weapon", "longsword")
    check("arma resgate-equipada na mão", (w["gear"].get("weapon") or {}).get("id") == "longsword")
    check("p['weapon'] sincronizado p/ combate", w["weapon"]["id"] == "longsword")

    # ── [3] Bolsa cheia + slot ocupado → RECUSA + estorna ouro ──────────────────
    print("\n[3] Bolsa cheia + slot ocupado → recusa + estorna ouro")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag(); w["gear"]["armor"] = armor_item("leather")
    gold0 = w["gold"]
    await r.handle_shop_buy("p1", "ferreiro_armor", "plate")
    check("compra recusada (armadura antiga permanece)", (w["gear"].get("armor") or {}).get("id") == "leather")
    check("ouro estornado", w["gold"] == gold0)
    check("erro de cheio enviado", any("cheio" in e.lower() for e in r._errs))
    check("não entrou na bolsa", not bag_has(w, "plate"))

    # ── [4] Anel: bolsa cheia + ring1 livre → resgate-equipa ────────────────────
    print("\n[4] Anel com bolsa cheia + slot de anel livre → resgate-equipa")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag()
    w["gear"]["ring1"] = None; w["gear"]["ring2"] = None
    await r.handle_shop_buy("p1", "mercador", "ring_str")
    check("anel resgate-equipado em ring1/ring2",
          (w["gear"].get("ring1") or {}).get("id") == "ring_str" or (w["gear"].get("ring2") or {}).get("id") == "ring_str")

    # ── [5] Anel: bolsa cheia + ambos anéis ocupados → recusa ───────────────────
    print("\n[5] Anel com bolsa cheia + ambos anéis ocupados → recusa")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag()
    w["gear"]["ring1"] = {"id": "ring_a", "name": "Anel A", "item_slot": "ring"}
    w["gear"]["ring2"] = {"id": "ring_b", "name": "Anel B", "item_slot": "ring"}
    gold0 = w["gold"]
    await r.handle_shop_buy("p1", "mercador", "ring_str")
    check("anel recusado (não entrou em nenhum slot)",
          (w["gear"].get("ring1") or {}).get("id") == "ring_a" and (w["gear"].get("ring2") or {}).get("id") == "ring_b")
    check("ouro estornado", w["gold"] == gold0)

    # ── [6] Consumível: bolsa cheia → recusa (sem resgate possível) ─────────────
    print("\n[6] Consumível (poção) com bolsa cheia → recusa")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = full_bag()
    gold0 = w["gold"]
    await r.handle_shop_buy("p1", "mercador", "health_potion")
    check("poção recusada", not bag_has(w, "health_potion") or len(w["bag"]) == 6)
    check("ouro estornado", w["gold"] == gold0)
    check("erro de cheio enviado", any("cheio" in e.lower() for e in r._errs))

    # ── [7] Arma de 2 mãos comprada com escudo equipado + bolsa livre → BOLSA ────
    print("\n[7] Arma 2 mãos + escudo equipado + bolsa livre → vai pra bolsa (não bloqueia)")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = []
    w["gear"]["off_hand"] = {"id": "escudo_p", "name": "Escudo Pequeno", "kind": "shield", "item_slot": "shield"}
    await r.handle_shop_buy("p1", "ferreiro_weapon", "espada2m")
    check("espada de 2 mãos foi pra bolsa", bag_has(w, "espada2m"))
    check("escudo permanece na mão esquerda", (w["gear"].get("off_hand") or {}).get("id") == "escudo_p")
    check("sem erro de '2 mãos'", not any("2 mãos" in e or "duas mãos" in e.lower() for e in r._errs))

    # ── [8] Loot de baú: bolsa cheia + slot livre → resgate-equipa ──────────────
    print("\n[8] Loot de baú com bolsa cheia + slot livre → resgate-equipa")
    r = setup(city=False)
    p = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["alive"] = True; p["pos"] = [5, 5]; p["bag"] = full_bag(); p["gear"]["armor"] = None
    cid = r._spawn_chest([5, 5], 0, [armor_item("leather")])
    await r.handle_take_from_chest("p1", cid, "item", 0)
    check("armadura do baú resgate-equipada", (p["gear"].get("armor") or {}).get("id") == "leather")
    check("baú esvaziado (item removido)", cid not in r.chests or len(r.chests[cid]["items"]) == 0)

    # ── [9] Loot de baú: bolsa cheia + slot ocupado → recusa, item fica no baú ───
    print("\n[9] Loot de baú com bolsa cheia + slot ocupado → recusa (item fica)")
    r = setup(city=False)
    p = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["alive"] = True; p["pos"] = [5, 5]; p["bag"] = full_bag(); p["gear"]["armor"] = armor_item("leather")
    cid = r._spawn_chest([5, 5], 0, [armor_item("plate")])
    await r.handle_take_from_chest("p1", cid, "item", 0)
    check("armadura permanece no baú", any(it.get("id") == "plate" for it in r.chests[cid]["items"]))
    check("erro de cheio enviado", any("cheio" in e.lower() for e in r._errs))

    # ── [10] Munição não regride (empilha na mão esquerda com off_hand livre) ────
    print("\n[10] Munição segue caminho próprio (não regride)")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 9999; w["bag"] = []; w["gear"]["off_hand"] = None
    ammo_id = SHOP_AMMO[0]["id"]
    await r.handle_shop_buy("p1", "ferreiro_ammo", ammo_id)
    check("munição equipou na mão esquerda (não foi pra bolsa)",
          (w["gear"].get("off_hand") or {}).get("effect") == "ammo")

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
