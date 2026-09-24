"""Regressão do Ataque Giratório da Guilda."""
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

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup():
    room = GameRoom("TEST")
    errors = []
    broadcasts = []

    async def capture_send(_pid, msg, *args, **kwargs):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errors.append(msg.get("msg", ""))

    async def capture_broadcast(msg, *args, **kwargs):
        broadcasts.append(msg)

    async def noop(*args, **kwargs):
        pass

    room.phase = "playing"
    room.round_num = 1
    room.player_order = ["h"]
    room.turn_index = 0
    room.send_to = capture_send
    room.broadcast = capture_broadcast
    room.gm_say = noop
    room.push_state = noop
    room._errs = errors
    room._broadcasts = broadcasts
    return room


def monster(mid, pos, hp=20, ac=10):
    return {
        "id": mid, "type": "orc", "name": mid, "pos": list(pos),
        "hp": hp, "max_hp": hp, "ac": ac, "ca": ac, "size": [1, 1],
        "alive": True, "altura": S.ALTURA_MIN,
    }


async def main():
    print("\n[1] Catálogo")
    item = S.guild_item("tecnica_ataque_giratorio")
    check("técnica existe", item is not None)
    check("recarga 6", item and item["recarga_rodadas"] == 6)
    check("preço intermediário 220", item and item["preco"] == 220)
    check("custo 4/4", item and item["custo_fome"] == 4 and item["custo_sede"] == 4)

    print("\n[2] Uma jogada, dano separado e área ortogonal")
    room = setup()
    hero = make_player("h", "Heroi", "warrior", 0)
    hero["pos"] = [5, 5]
    hero["alive"] = True
    hero["fome"] = 50
    hero["sede"] = 50
    hero["guild_owned"]["tecnicas"] = ["tecnica_ataque_giratorio"]
    hero["guild_equip"]["tecnica"] = "tecnica_ataque_giratorio"
    hero["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6",
                       "stat": "str_", "categoria": "cortante", "throw_range": 2}
    room.players["h"] = hero
    room.monsters = {
        "n": monster("n", [5, 4]),
        "s": monster("s", [5, 6]),
        "e": monster("e", [6, 5]),
        "diag": monster("diag", [6, 6]),
    }
    room._rolar_ataque = lambda *args, **kwargs: (True, 15, 20, False, None)
    roll_calls = {"n": 0, "d": 0}

    def fixed_damage(*args, **kwargs):
        roll_calls["d"] += 1
        return 4, "Machado", "[1d6=4+0]", 4, "1d6"

    room._resolver_dano_ataque_basico = fixed_damage
    room._monster_dies = lambda *args, **kwargs: asyncio.sleep(0)
    original_roll = room._rolar_ataque

    def count_roll(*args, **kwargs):
        roll_calls["n"] += 1
        return original_roll(*args, **kwargs)

    room._rolar_ataque = count_roll
    await room.handle_usar_tecnica("h", "tecnica_ataque_giratorio")
    check("um único d20 para a varredura", roll_calls["n"] == 1)
    check("dano rolado separadamente para 3 alvos", roll_calls["d"] == 3)
    check("norte atingido", room.monsters["n"]["hp"] == 16)
    check("sul atingido", room.monsters["s"]["hp"] == 16)
    check("leste atingido", room.monsters["e"]["hp"] == 16)
    check("diagonal não atingida", room.monsters["diag"]["hp"] == 20)
    check("ação consumida", hero["action_done"] is True)
    check("custo total fome = técnica + ação", hero["fome"] == 45)
    check("custo sede da técnica", hero["sede"] == 46)
    check("recarga começa em 6 rodadas", hero["technique_cooldowns"].get("tecnica_ataque_giratorio") == 7)
    check("feedback tem um d20", sum(m.get("type") == "dice_roll" and m.get("die") == "d20" for m in room._broadcasts) == 1)
    spin_starts = [m for m in room._broadcasts if m.get("type") == "attack_feedback" and m.get("phase") == "start"]
    check("feedback identifica um único giro", len({m.get("spin_id") for m in spin_starts}) == 1)

    print("\n[3] Redemoinho da Morte — seleção e recargas")
    morte = S.guild_item("tecnica_redemoinho_morte")
    check("Redemoinho existe", morte is not None)
    check("Redemoinho custa 350", morte and morte["preco"] == 350)
    check("Redemoinho exige Ataque Giratório", morte and morte["requer"] == "tecnica_ataque_giratorio")
    check("Redemoinho é do Guerreiro", morte and morte["classe"] == "warrior")

    def setup_morte(especializacao=False):
        r = setup()
        h = make_player("h", "Heroi", "warrior", 0)
        h["pos"] = [5, 5]
        h["fome"] = h["sede"] = 50
        h["guild_owned"]["tecnicas"] = ["tecnica_ataque_giratorio", "tecnica_redemoinho_morte"]
        h["guild_equip"]["tecnica"] = "tecnica_redemoinho_morte"
        if especializacao:
            h["guild_owned"]["especializacoes"] = ["guerreiro_furia_3"]
        h["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6",
                        "stat": "str_", "categoria": "cortante"}
        r.players["h"] = h
        r.monsters = {"m": monster("m", [5, 4], hp=50)}
        calls = {"d20": 0, "dano": 0}

        def fixed_roll(*_args, **_kwargs):
            calls["d20"] += 1
            return True, 15, 20, False, None

        def fixed_dmg(*_args, **_kwargs):
            calls["dano"] += 1
            return 4, "Machado", "[1d6=4+0]", 4, "1d6"

        r._rolar_ataque = fixed_roll
        r._resolver_dano_ataque_basico = fixed_dmg
        r._monster_dies = lambda *args, **kwargs: asyncio.sleep(0)
        r._calls = calls
        return r, h

    room5, hero5 = setup_morte()
    await room5.handle_usar_tecnica("h", "tecnica_redemoinho_morte", ataques=2)
    check("dois giros fazem dois d20", room5._calls["d20"] == 2)
    check("dois giros rolam dano duas vezes", room5._calls["dano"] == 2)
    spin_ids = {m.get("spin_id") for m in room5._broadcasts if m.get("type") == "attack_feedback" and m.get("phase") == "start"}
    spin_indexes = {m.get("spin_index") for m in room5._broadcasts if m.get("type") == "attack_feedback" and m.get("phase") == "start"}
    check("dois giros têm grupos visuais distintos", len(spin_ids) == 2 and spin_indexes == {1, 2})
    check("dois giros custam 8/8 mais a ação", hero5["fome"] == 41 and hero5["sede"] == 42)
    check("dois giros entram em recarga 8", hero5["technique_cooldowns"].get("tecnica_redemoinho_morte") == 9)

    room6, hero6 = setup_morte()
    await room6.handle_usar_tecnica("h", "tecnica_redemoinho_morte", ataques=3)
    check("três giros sem Fúria III são recusados", room6._errs)
    check("recusa dos três giros não cobra recursos", hero6["fome"] == 50 and hero6["sede"] == 50)

    room7, hero7 = setup_morte(especializacao=True)
    await room7.handle_usar_tecnica("h", "tecnica_redemoinho_morte", ataques=3)
    check("Fúria III libera três giros", room7._calls["d20"] == 3)
    check("três giros custam 14/14 mais a ação", hero7["fome"] == 35 and hero7["sede"] == 36)
    check("três giros entram em recarga 10", hero7["technique_cooldowns"].get("tecnica_redemoinho_morte") == 11)

    print("\n[4] Arremessável permitido, sem arremesso")
    room2 = setup()
    hero2 = make_player("h", "Heroi", "warrior", 0)
    hero2["pos"] = [5, 5]
    hero2["fome"] = hero2["sede"] = 50
    hero2["guild_owned"]["tecnicas"] = ["tecnica_ataque_giratorio"]
    hero2["guild_equip"]["tecnica"] = "tecnica_ataque_giratorio"
    hero2["weapon"] = {"id": "lanca", "name": "Lança", "die": "1d8", "stat": "str_",
                        "reach": "lanca", "throw_range": 4, "categoria": "perfurante"}
    room2.players["h"] = hero2
    room2.monsters = {"m": monster("m", [5, 4])}
    room2._rolar_ataque = lambda *args, **kwargs: (True, 12, 17, False, None)
    room2._resolver_dano_ataque_basico = fixed_damage
    room2._monster_dies = lambda *args, **kwargs: asyncio.sleep(0)
    await room2.handle_usar_tecnica("h", "tecnica_ataque_giratorio")
    check("lança pode usar o giro", not room2._errs)
    check("lança não foi removida/arremessada", hero2["weapon"].get("id") == "lanca")

    print("\n[5] Armas à distância recusadas sem custo")
    room3 = setup()
    hero3 = make_player("h", "Heroi", "warrior", 0)
    hero3["pos"] = [5, 5]
    hero3["fome"] = hero3["sede"] = 50
    hero3["guild_owned"]["tecnicas"] = ["tecnica_ataque_giratorio"]
    hero3["guild_equip"]["tecnica"] = "tecnica_ataque_giratorio"
    hero3["weapon"] = {"id": "arco_curto", "name": "Arco", "die": "1d6", "stat": "dex",
                        "range": 6, "categoria": "perfurante"}
    room3.players["h"] = hero3
    await room3.handle_usar_tecnica("h", "tecnica_ataque_giratorio")
    check("arco recusado", room3._errs)
    check("recusa não consome fome/sede", hero3["fome"] == 50 and hero3["sede"] == 50)
    check("recusa não consome ação/recarga", not hero3["action_done"] and not hero3["technique_cooldowns"])

    print("\n[6] Desarmado permitido")
    room4 = setup()
    hero4 = make_player("h", "Heroi", "warrior", 0)
    hero4["pos"] = [5, 5]
    hero4["fome"] = hero4["sede"] = 50
    hero4["guild_owned"]["tecnicas"] = ["tecnica_ataque_giratorio"]
    hero4["guild_equip"]["tecnica"] = "tecnica_ataque_giratorio"
    hero4["weapon"] = {"id": "unarmed", "name": "Desarmado", "die": None, "stat": "str_"}
    room4.players["h"] = hero4
    room4.monsters = {"m": monster("m", [5, 4])}
    room4._rolar_ataque = lambda *args, **kwargs: (True, 12, 17, False, None)
    await room4.handle_usar_tecnica("h", "tecnica_ataque_giratorio")
    check("desarmado pode usar", not room4._errs and hero4["action_done"] is True)

    print(f"\n{'=' * 40}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
