"""Teste das regras de equipar/arremessar:
  • Equipar é AÇÃO LIVRE (sem custo, sem limite por turno) — duas armas no mesmo turno.
  • Equipar respeita restrição de classe (allowed_classes).
  • Comprar adaga com a mão principal ocupada vai para a BOLSA.
  • Equipar adaga como 2ª arma (off_hand) é ação livre.
  • Arremesso roteia o SLOT certo (mão principal vs 2ª mão).
Roda da raiz: python tools/test_equipar.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, sys, os
from copy import deepcopy
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, make_monster, MONSTER_DEFS, WEAPONS, SHOP_WEAPONS, SHOP_ARMORS

def setup():
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._tem_linha_de_visao = lambda *a, **k: True
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r._errs = errs
    return r

def bag_idx(p, item_id):
    for i, it in enumerate(p["bag"]):
        if it and it.get("id") == item_id:
            return i
    return -1

def shop_w(wid):
    return deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == wid))

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # ── [1] Equipar duas armas no MESMO turno (ação livre) ──────────────────────
    print("\n[1] Equipar é ação livre — duas armas no mesmo turno")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    arma_inicial = w["gear"]["weapon"]["id"]
    w["bag"] = [shop_w("longsword"), shop_w("warhammer")]
    w["bonus_action_used"] = False

    await r.handle_equip_from_bag("p1", bag_idx(w, "longsword"))
    check("1ª arma equipada (longsword)", w["gear"]["weapon"]["id"] == "longsword")
    check("p['weapon'] sincronizado (longsword)", w["weapon"]["id"] == "longsword")
    check("equipar NÃO gastou ação bônus", w.get("bonus_action_used") is False)
    check("arma inicial voltou para a bolsa", bag_idx(w, arma_inicial) >= 0)
    check("sem erro ao equipar a 1ª", not r._errs)

    await r.handle_equip_from_bag("p1", bag_idx(w, "warhammer"))
    check("2ª arma equipada no MESMO turno (warhammer)", w["gear"]["weapon"]["id"] == "warhammer")
    check("p['weapon'] sincronizado (warhammer)", w["weapon"]["id"] == "warhammer")
    check("ainda sem gasto de ação bônus", w.get("bonus_action_used") is False)
    check("nenhum erro 'Ação bônus já usada'", not any("bônus" in e for e in r._errs))

    # mesmo com a ação bônus JÁ usada, ainda equipa (é livre)
    w["bonus_action_used"] = True
    await r.handle_equip_from_bag("p1", bag_idx(w, "longsword"))
    check("equipa mesmo com ação bônus já usada", w["gear"]["weapon"]["id"] == "longsword")

    # ── [2] Restrição de classe ainda bloqueia ──────────────────────────────────
    print("\n[2] Restrição de classe (allowed_classes)")
    r = setup()
    mg = make_player("p1", "Pedro", "mage", 1); r.players["p1"] = mg
    mg["bag"] = [deepcopy(next(a for a in SHOP_ARMORS if a["id"] == "chainmail"))]
    await r.handle_equip_from_bag("p1", 0)
    check("mago NÃO equipa cota de malha", (mg["gear"].get("armor") or {}).get("id") != "chainmail")
    check("cota permanece na bolsa", bag_idx(mg, "chainmail") >= 0)
    check("erro de classe enviado", any("classe" in e.lower() for e in r._errs))

    # ── [3] Compra de arma vai para a BOLSA (modelo bolsa-primeiro) ──────────────
    # Sub-projeto B: comprar NÃO auto-equipa mais — o item vai pra bolsa (o jogador
    # equipa pelo boneco). Auto-equipar só como resgate quando a bolsa está cheia
    # (coberto em tools/test_roteamento_itens.py).
    print("\n[3] Compra de arma vai para a bolsa (bolsa-primeiro)")
    r = setup(); r.phase = "city"
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["gold"] = 100; w["bag"] = []
    arma0 = w["gear"]["weapon"]["id"]
    await r.handle_shop_buy("p1", "ferreiro_weapon", "dagger")
    check("adaga comprada foi para a bolsa", bag_idx(w, "dagger") >= 0)
    check("mão principal inalterada", w["gear"]["weapon"]["id"] == arma0)
    # arma normal (não-adaga) com mão ocupada + bolsa livre → bolsa (não auto-equipa)
    await r.handle_shop_buy("p1", "ferreiro_weapon", "longsword")
    check("arma normal também vai pra bolsa", bag_idx(w, "longsword") >= 0)
    check("mão principal continua com a arma inicial", w["gear"]["weapon"]["id"] == arma0)
    # comprar com a mão VAZIA + bolsa livre → BOLSA (bolsa-primeiro; equipar é manual)
    r2 = setup(); r2.phase = "city"
    w2 = make_player("p2", "Victor", "warrior", 0); r2.players["p2"] = w2
    w2["gold"] = 100; w2["bag"] = []; w2["gear"]["weapon"] = None; w2["weapon"] = deepcopy(WEAPONS["unarmed"])
    await r2.handle_shop_buy("p2", "ferreiro_weapon", "dagger")
    check("compra com mão vazia vai pra bolsa (não auto-equipa)", bag_idx(w2, "dagger") >= 0)
    check("mão principal continua vazia", w2["gear"].get("weapon") is None)

    # ── [4] Equipar 2ª arma (off_hand) é ação livre ─────────────────────────────
    print("\n[4] Equipar adaga como 2ª arma (off_hand) — ação livre")
    r = setup()
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    w["bag"] = [shop_w("dagger")]; w["bonus_action_used"] = True
    await r.handle_equip_offhand("p1", 0)
    check("adaga foi para a mão esquerda (off_hand)", (w["gear"].get("off_hand") or {}).get("id") == "dagger")
    check("equipar 2ª arma não gastou ação bônus", w.get("bonus_action_used") is True)  # já era True; não bloqueou
    check("sem erro ao equipar 2ª arma", not r._errs)

    # ── [5] Arremesso roteia o SLOT correto ─────────────────────────────────────
    print("\n[5] Arremesso por slot (mão principal vs 2ª mão)")
    def dag(slot):
        return {"id": "dagger", "name": "Adaga", "emoji": "🗡️", "die": "1d4",
                "stat": "str_", "throw_range": 3, "finesse": True, "item_slot": slot}
    mdef = next(m for m in MONSTER_DEFS if m["type"] == "urso_negro")

    # arremessar a 2ª mão NÃO deve esvaziar a mão principal
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["pos"] = [5, 5]; r.players["p1"] = p
    p["weapon"] = deepcopy(WEAPONS["dagger"]); p["gear"]["weapon"] = dag("weapon")
    p["gear"]["off_hand"] = dag("off_hand")
    mob = make_monster(mdef, {"id": 1, "cx": 5, "cy": 6}); mob["pos"] = [5, 6]
    mob["hp"] = 99; mob["max_hp"] = 99; r.monsters[mob["id"]] = mob
    _o = S.random.randint; S.random.randint = lambda a, b: 1   # nat1: não dropa baú (sem precisar de mapa)
    await r.handle_throw("p1", mob["id"], "off_hand")
    S.random.randint = _o
    check("arremesso 2ª mão esvaziou a off_hand", r.players["p1"]["gear"].get("off_hand") is None)
    check("arremesso 2ª mão preservou a mão principal", r.players["p1"]["gear"].get("weapon") is not None)

    # arremessar a mão principal esvazia a principal (vira desarmado), off_hand intacta
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["pos"] = [5, 5]; r.players["p1"] = p
    p["weapon"] = deepcopy(WEAPONS["dagger"]); p["gear"]["weapon"] = dag("weapon")
    p["gear"]["off_hand"] = dag("off_hand")
    mob = make_monster(mdef, {"id": 1, "cx": 5, "cy": 6}); mob["pos"] = [5, 6]
    mob["hp"] = 99; mob["max_hp"] = 99; r.monsters[mob["id"]] = mob
    _o = S.random.randint; S.random.randint = lambda a, b: 1
    await r.handle_throw("p1", mob["id"], "weapon")
    S.random.randint = _o
    check("arremesso mão principal esvaziou a principal", r.players["p1"]["gear"].get("weapon") is None)
    check("arremesso mão principal → desarmado", r.players["p1"]["weapon"]["id"] == "unarmed")
    check("arremesso mão principal preservou a 2ª mão", r.players["p1"]["gear"].get("off_hand") is not None)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
