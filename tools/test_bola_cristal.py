"""Regressions for the reusable crystal ball clairvoyance item."""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, SHOP_MERCHANT, make_player, slots_max_para


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"  ✅ {name}")


def setup_room(class_id="warrior"):
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room._broadcast_dado = noop
    room.round_num = 1
    room.phase = "playing"
    room.player_order = ["p1"]
    room.turn_index = 0
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    player = make_player("p1", "Herói", class_id, 0)
    player["action_done"] = False
    player["pos"] = [2, 2]
    room.players["p1"] = player
    return room, player


def main():
    print("\n[1] Bola universal de Clarividência no catálogo e no mercador")
    item = next((it for it in SHOP_MERCHANT if it.get("id") == "bola_cristal_clarividencia"), None)
    check("item custa 1.000 moedas, ocupa a mão do escudo e não restringe classe",
          item is not None and item.get("price") == 1000
          and item.get("buy_price") == 1000
          and item.get("item_slot") == "off_hand" and not item.get("allowed_classes"))
    check("ícone do PNG e efeito dedicados estão no catálogo",
          item.get("icon") == "assets/itens/bola_cristal_clarividencia.png"
          and item.get("effect") == "crystal_ball_clairvoyance")
    check("estoque do mercador inclui a bola em cada cidade com mercador",
          all("bola_cristal_clarividencia" in stock.get("mercador", [])
              for cid, stock in server.CITY_SHOPS.items()
              if "mercador" in stock and cid != "vila_dos_charcos"))   # loja especial da Zumbra

    print("\n[2] Uso por qualquer classe, sem gastar slot, com escala diferenciada")
    for class_id in ("warrior", "rogue", "paladin", "bard", "mage", "cleric"):
        room, player = setup_room(class_id)
        orb = copy.deepcopy(item)
        player["gear"]["off_hand"] = orb
        before_slots = copy.deepcopy(player.get("slots_cooldown", {}))
        before_max_slots = slots_max_para(player).copy()
        executions = []

        async def capture(caster, spell, data, *args, **kwargs):
            executions.append((copy.deepcopy(spell), copy.deepcopy(data)))

        room._executar_magia_grimorio = capture
        asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 8, "ty": 9}))
        check(f"{class_id} usa a bola equipada na mão do escudo",
              len(executions) == 1 and executions[0][1].get("tx") == 8
              and executions[0][1].get("ty") == 9)
        check(f"{class_id} não consome espaço de magia",
              player.get("slots_cooldown", {}) == before_slots
              and slots_max_para(player) == before_max_slots)
        check(f"{class_id} gasta ação principal e aplica recarga de 10 rodadas",
              player.get("action_done") is True and orb.get("clarividencia_pronta_em") == 11)
        if class_id in ("mage", "cleric"):
            check(f"{class_id} preserva escala normal da Clarividência",
                  "area_lado" not in executions[0][0])
        else:
            check(f"{class_id} usa área fixa de 4×4",
                  executions[0][0].get("area_lado") == 4)

    print("\n[3] A recarga pertence ao item e é validada pelo servidor")
    room, player = setup_room("warrior")
    orb = copy.deepcopy(item)
    player["gear"]["off_hand"] = orb
    calls = []

    async def capture(caster, spell, data, *args, **kwargs):
        calls.append(data)

    room._executar_magia_grimorio = capture
    asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 4, "ty": 4}))
    player["action_done"] = False
    room.round_num = 10
    asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 5, "ty": 5}))
    check("não reutiliza antes de completar dez rodadas", len(calls) == 1)
    player["gear"]["off_hand"] = None
    player["action_done"] = False
    errors = []

    async def capture_error(pid, message):
        if message.get("type") == "error":
            errors.append(message.get("msg"))

    room.send_to = capture_error
    asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 6, "ty": 6}))
    check("sem a bola equipada o servidor recusa sem conjurar", bool(errors) and len(calls) == 1)

    room, player = setup_room("warrior")
    player["gear"]["off_hand"] = copy.deepcopy(item)
    player["gear"]["weapon"] = {"id": "staff"}
    room.rooms = []
    asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 8, "ty": 9}))
    check("executor real revela exatamente 16 casas para outra classe",
          len(room.magic_reveal) == 16)
    check("executor real mantém a duração e expiração da Clarividência",
          all(expira == room.round_num + 2 for expira in room.magic_reveal.values()))

    room.round_num = 11
    player["action_done"] = False
    asyncio.run(room.handle_use_crystal_ball("p1", {"tx": 12, "ty": 12}))
    check("bola volta a ficar disponível ao completar dez rodadas",
          player["gear"]["off_hand"].get("clarividencia_pronta_em") == 21)

    print("\n[4] Equipamento concede ação apenas enquanto a bola está equipada")
    room, player = setup_room("cleric")
    check("sem bola, ação não aparece", not any(
        skill.get("id") == "usar_bola_cristal" for skill in
        (room._crystal_ball_skill(player),) if skill))
    player["gear"]["off_hand"] = copy.deepcopy(item)
    granted = room._crystal_ball_skill(player)
    check("bola equipada concede a habilidade de uso", granted["id"] == "usar_bola_cristal")
    max_slots = slots_max_para(player).copy()
    check("slot máximo de magia permanece inalterado", slots_max_para(player) == max_slots)


if __name__ == "__main__":
    main()
