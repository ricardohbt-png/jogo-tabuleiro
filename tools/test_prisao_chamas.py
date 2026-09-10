"""Testes da magia Prisão de Chamas.

Roda da raiz:
    python -X utf8 tools/test_prisao_chamas.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


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
    room = S.GameRoom("TEST")
    errors = []

    async def noop(*args, **kwargs):
        return None

    async def send_to(pid, msg, *args, **kwargs):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errors.append(msg.get("msg", ""))

    room.broadcast = noop
    room.push_state = noop
    room.gm_say = noop
    room.send_to = send_to
    room._is_turn = lambda pid: True
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room._alcance_com_altura = lambda *args, **kwargs: True
    room.phase = "playing"
    room.map_w = room.map_h = 12
    room.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    room.monsters = {}
    room.players = {}
    room.zonas_especiais = []
    room.round_num = 1
    room._errors = errors
    return room


def add_mage(room, level=5, pos=(1, 1)):
    mage = S.make_player("p", "Pedro", "mage", 0)
    mage.update(level=level, pos=list(pos), alive=True, hp=50, max_hp=50,
                fome=40, sede=40, action_done=False)
    mage["magias_conhecidas"] = ["prisao_chamas"]
    room.players[mage["id"]] = mage
    room.player_order = [mage["id"]]
    room.initiative_active = True
    room._rebuild_initiative()
    return mage


async def main():
    old_roll = S.roll_dice

    def fixed_roll(expr):
        expr = str(expr)
        if expr == "2d4":
            return 4
        if expr == "2d8":
            return 8
        return old_roll(expr)

    S.roll_dice = fixed_roll
    try:
        room = setup()
        mage = add_mage(room, level=5)
        adjacent = S.make_player("a", "Aliado", "warrior", 0)
        adjacent.update(level=1, pos=[3, 3], alive=True, hp=30, max_hp=30)
        room.players[adjacent["id"]] = adjacent
        monster = {"id": "m", "name": "Monstro", "pos": [4, 4],
                   "hp": 30, "max_hp": 30, "alive": True, "ac": 10}
        room.monsters[monster["id"]] = monster
        flying = {"id": "alto", "name": "Criatura alta", "pos": [5, 4],
                  "hp": 30, "max_hp": 30, "alive": True, "ac": 10, "altura": 4}
        room.monsters[flying["id"]] = flying

        await room.handle_magia("p", {"magia_id": "prisao_chamas",
                                       "tx": 5, "ty": 5, "lado": 3})
        zone = next(z for z in room.zonas_especiais
                    if z.get("tipo") == "prisao_chamas")
        check("magia de 4º círculo no catálogo", S.GRIMORIO["prisao_chamas"]["circulo"] == "quarto")
        check("nível 5 alcança 6 quadrados", S.GRIMORIO["prisao_chamas"]["alcance_base"] + 5 // 2 == 6)
        check("área 3x3", zone["lado"] == 3 and len(zone["tiles"]) == 9)
        check("somente a borda vira chama", len(zone["flame_tiles"]) == 8)
        check("parede pode ser ignorada no conjunto de chão", all(
            room.tiles[y][x] in (S.FLOOR, S.DOOR) for x, y in zone["flame_tiles"]))
        check("dano inicial nas chamas", monster["hp"] == 22)
        check("dano inicial adjacente inclui diagonal", adjacent["hp"] == 26)
        check("altura acima de 3 atravessa sem dano", flying["hp"] == 30)

        adjacent["hp"] = 30
        adjacent["pos"] = [4, 4]
        await room._aplicar_prisao_chamas_se_pisar(adjacent)
        check("entrada na borda causa 2d8", adjacent["hp"] == 22)
        flying["pos"] = [4, 5]
        await room._aplicar_prisao_chamas_se_pisar(flying)
        check("criatura alta entra livremente", flying["hp"] == 30)

        adjacent["hp"] = 30
        adjacent["pos"] = [3, 3]
        await room._processar_prisao_chamas_inicio_turno(adjacent)
        check("início do turno adjacente causa 2d4", adjacent["hp"] == 26)

        await room.handle_encerrar_prisao_chamas("p")
        check("encerramento é aceito como ação livre", not zone["ativa"])

        room = setup()
        add_mage(room, level=1)
        room.tiles[4][4] = S.WALL
        await room.handle_magia("p", {"magia_id": "prisao_chamas",
                                       "tx": 5, "ty": 5, "lado": 3})
        zone = next(z for z in room.zonas_especiais
                    if z.get("tipo") == "prisao_chamas")
        check("área sobre parede afeta somente chão", [4, 4] not in zone["tiles"] and len(zone["tiles"]) == 8)
        room.round_num = zone["expira_em"]
        await room._processar_zonas_turno()
        check("zona expira após 10 rodadas", not zone["ativa"])
    finally:
        S.roll_dice = old_roll

    print("\n" + "=" * 58)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 58)
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
