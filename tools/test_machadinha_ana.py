"""Machadinha de Arremesso Anã: catálogo, loja, mão do escudo (FOR) e arremesso."""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup():
    room = GameRoom("TEST")
    room._errs, room._bc = [], []

    async def send(_pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            room._errs.append(str(msg.get("msg", "")))

    async def bc(msg, *a, **k):
        room._bc.append(msg)

    async def noop(*a, **k):
        pass

    room.send_to, room.broadcast = send, bc
    room.gm_say = room.push_state = room.push_state_or_city = noop
    room.phase = "playing"
    room.round_num = 1
    room.player_order = ["h"]
    room.turn_index = 0
    return room


def mon(pos, hp=100, ac=1):
    return {"id": "m", "type": "orc", "name": "Alvo", "pos": list(pos), "hp": hp,
            "max_hp": hp, "ac": ac, "size": [1, 1], "alive": True,
            "altura": S.ALTURA_MIN}


async def main():
    print("\n[1] Catálogo")
    w = S.WEAPONS["machadinha_ana"]
    loja = next((x for x in S.SHOP_WEAPONS if x["id"] == "machadinha_ana"), None)
    check("existe em WEAPONS e na loja", loja is not None)
    check("dano 1d6 FOR cortante", w["die"] == "1d6" and w["stat"] == "str_" and w["categoria"] == "cortante")
    check("arremesso 3 casas", w["throw_range"] == 3 and loja["throw_range"] == 3)
    check("preço 35", loja["price"] == 35)
    check("só Guerreiro Anão", loja["allowed_classes"] == ["warrior"])
    check("arremesso bruto (FOR)", S._weapon_uses_brutal_throw(w))
    check("compatível com a mão do escudo", GameRoom._eh_arma_offhand(dict(loja)))
    check("não é finesse", not w.get("finesse"))
    check("vendida no ferreiro de Alva e Luz",
          "machadinha_ana" in S.CITY_SHOPS["alva_e_luz"]["ferreiro_weapon"])
    check("tem descrição (FOR na mão do escudo)", "Força" in S.weapon_description(loja) if hasattr(S, "weapon_description") else True)

    print("\n[2] Classes")
    room = setup()
    mage = make_player("m", "Mago", "mage", 0)
    mage["bag"] = [dict(loja)]
    room.players["m"] = mage
    await room.handle_equip_offhand("m", 0)
    check("mago não equipa", mage["gear"].get("off_hand") is None and room._errs)

    print("\n[3] Ataque da mão do escudo usa FOR (DES baixa)")
    room = setup()
    h = make_player("h", "Anao", "warrior", 0)
    h.update(pos=[5, 5], alive=True, fome=50, sede=50, str_=18, dex=8)
    h["bag"] = [dict(loja)]
    room.players["h"] = h
    await room.handle_equip_offhand("h", 0)
    check("equipou na mão do escudo", (h["gear"].get("off_hand") or {}).get("id") == "machadinha_ana")
    check("sem 'off_hand_forca' perdido", h["gear"]["off_hand"].get("off_hand_forca") is True)
    room.monsters = {"m": mon([5, 4])}
    room.initiative_active = False
    msgs = []
    orig = room.broadcast

    async def bc2(msg, *a, **k):
        msgs.append(msg)
    room.broadcast = bc2
    S.d20_attack = lambda bonus, ac: (True, 15, 15 + bonus, False)
    S.roll_dice = lambda die: 3
    hp0 = room.monsters["m"]["hp"]
    await room.handle_attack("h", "m")
    dano_off = [m for m in msgs if m.get("label") and "2" in str(m.get("label")) and m.get("type") == "dice_roll"]
    perdido = hp0 - room.monsters["m"]["hp"]
    # principal desarmado + 2ª mão: FOR 18 = +4 -> 3+4 = 7 na machadinha
    check("golpe da 2ª mão aplicou +4 de FOR (7 de dano)", perdido >= 7)
    check("consumiu a ação bônus", h.get("bonus_action_used") is True)

    print("\n[4] Arremesso a 3 casas, FOR no acerto e dano")
    room = setup()
    h = make_player("h", "Anao", "warrior", 0)
    h.update(pos=[5, 5], alive=True, fome=50, sede=50, str_=18, dex=8)
    h["bag"] = [dict(loja)]
    room.players["h"] = h
    await room.handle_equip_offhand("h", 0)
    room._tem_linha_de_visao = lambda *a, **k: True
    room._free_tile_near = lambda pos, *a, **k: list(pos)
    room._spawn_chest = lambda *a, **k: room._drops.append(a)
    room._drops = []
    room.monsters = {"m": mon([5, 8])}
    fixed = {"n": 0}
    S.random.randint = lambda a, b: 12
    S.roll_dice = lambda die: 3
    ok = await room._executar_arremesso("h", "m", "off_hand")
    check("alcança 3 casas", ok is True)
    check("dano = 3 + FOR(4) = 7", room.monsters["m"]["hp"] == 93)
    check("machadinha saiu da mão", h["gear"].get("off_hand") is None)
    room.monsters = {"m": mon([5, 9])}
    h["bag"] = [dict(loja)]
    await room.handle_equip_offhand("h", 0)
    ok = await room._executar_arremesso("h", "m", "off_hand")
    check("4 casas é recusado", ok is False)

    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
