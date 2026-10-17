"""Lâmina do Vento: só Paladino/Guerreiro, 1d10 com crítico do Machado Duplo, sem arremesso."""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = FAIL = 0
def check(n, c):
    global PASS, FAIL
    if c: PASS += 1; print(f"  ✅ {n}")
    else: FAIL += 1; print(f"  ❌ {n}")

async def main():
    room = GameRoom("T"); errs = []
    async def send(_p, m, *a, **k):
        if isinstance(m, dict) and m.get("type") == "error": errs.append(str(m["msg"]))
    async def noop(*a, **k): pass
    room.send_to = send
    room.broadcast = room.gm_say = room.push_state = room.push_state_or_city = noop
    room.phase = "playing"; room.round_num = 1; room.player_order = ["h"]; room.turn_index = 0

    w = S.WEAPONS["lamina_do_vento"]
    md = S.WEAPONS["machado_duplo"]
    check("cópia do machado duplo removida", "machado_duplo_copia" not in S.WEAPONS
          and not any(x["id"] == "machado_duplo_copia" for x in S.SHOP_WEAPONS))
    check("dano = o do Machado Duplo", w["die"] == md["die"] == "1d10")
    check("crítico do Machado Duplo", w["extra_attack_on_crit_min_nat"] == md["extra_attack_on_crit_min_nat"] == 19)
    check("sem arremesso", not w.get("throw_range"))
    sh = next(x for x in S.SHOP_WEAPONS if x["id"] == "lamina_do_vento")
    check("só Paladino e Guerreiro", sorted(sh["allowed_classes"]) == ["paladin", "warrior"])
    check("mantém +1/+1 e a técnica", w["atk_bonus"] == 1 and w["damage_bonus"] == 1
          and w["granted_ability"] == "guild_tecnica_ataque_giratorio")

    for cls, ok in (("warrior", True), ("paladin", True), ("bard", False), ("mage", False), ("rogue", False), ("cleric", False)):
        h = make_player("h", "H", cls, 0); h.update(pos=[5, 5], alive=True)
        h["bag"] = [dict(sh)]; room.players["h"] = h; errs.clear()
        await room.handle_equip_from_bag("h", 0)
        eq = (h["gear"].get("weapon") or {}).get("id") == "lamina_do_vento"
        check(f"{cls} {'equipa' if ok else 'é recusado'}", eq == ok)
        if ok:
            check(f"{cls}: copia de combate com 1d10 e crítico", h["weapon"].get("die") == "1d10"
                  and h["weapon"].get("extra_attack_on_crit_min_nat") == 19)

    h = make_player("h", "H", "warrior", 0); h.update(pos=[5, 5], alive=True, fome=50, sede=50)
    h["bag"] = [dict(sh)]; room.players["h"] = h
    await room.handle_equip_from_bag("h", 0)
    room.monsters = {"m": {"id": "m", "type": "orc", "name": "A", "pos": [5, 6], "hp": 50, "max_hp": 50,
                           "ac": 1, "size": [1, 1], "alive": True, "altura": S.ALTURA_MIN}}
    errs.clear()
    r = await room._executar_arremesso("h", "m", "weapon")
    check("arremesso recusado", r is False and h["gear"].get("weapon") is not None)

    print(f"\n{PASS} passed, {FAIL} failed"); sys.exit(1 if FAIL else 0)
asyncio.run(main())
