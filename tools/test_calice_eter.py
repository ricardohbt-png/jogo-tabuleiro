"""Regressions for the Ether Chalice spell-slot recovery item."""
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


def setup_room(class_id="mage"):
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
    print("\n[1] Catálogo e estoque do Cálice de Éter")
    item = next((it for it in SHOP_MERCHANT if it.get("id") == "calice_eter"), None)
    check("catálogo define consumível de 220 moedas para Mago e Clérigo",
          bool(item and item.get("price") == 220 and item.get("buy_price") == 220
               and item.get("item_slot") == "bag"
               and set(item.get("allowed_classes", [])) == {"mage", "cleric"}))
    check("ícone transparente e efeito de recuperar 1º círculo estão associados",
          bool(item and item.get("icon") == "assets/itens/calice_eter.png"
               and item.get("effect") == "restore_spell_slot"
               and item.get("circle") == "primeiro"))
    check("todos os mercadores ativos oferecem o item",
          all("calice_eter" in stock.get("mercador", [])
              for stock in server.CITY_SHOPS.values() if "mercador" in stock))

    print("\n[2] Restaura exatamente um slot gasto sem alterar o máximo")
    for class_id in ("mage", "cleric"):
        room, player = setup_room(class_id)
        chalice = copy.deepcopy(item)
        player["bag"] = [chalice]
        player["slots_cooldown"]["primeiro"] = [5, 9]
        before_max = slots_max_para(player).copy()
        asyncio.run(room.handle_use_item("p1", "calice_eter"))
        check(f"{class_id} recupera exatamente um slot do 1º círculo",
              player["slots_cooldown"]["primeiro"] == [5]
              and len(player["bag"]) == 0)
        check(f"{class_id} usa ação bônus e não aumenta o máximo de slots",
              player.get("bonus_action_used") is True
              and slots_max_para(player) == before_max)

    print("\n[3] Recusas não gastam item nem ação")
    room, player = setup_room("warrior")
    chalice = copy.deepcopy(item) if item else {
        "id": "calice_eter", "effect": "restore_spell_slot", "circle": "primeiro"}
    player["bag"] = [chalice]
    player["slots_cooldown"]["primeiro"] = [5]
    errors = []

    async def capture_error(pid, message):
        if message.get("type") == "error":
            errors.append(message.get("msg"))

    room.send_to = capture_error
    asyncio.run(room.handle_use_item("p1", "calice_eter"))
    check("classe não permitida mantém item e ação bônus", len(player["bag"]) == 1
          and not player.get("bonus_action_used") and bool(errors))

    room, player = setup_room("mage")
    chalice = copy.deepcopy(item) if item else {
        "id": "calice_eter", "effect": "restore_spell_slot", "circle": "primeiro"}
    player["bag"] = [chalice]
    player["slots_cooldown"]["primeiro"] = [2]
    room.round_num = 2  # cooldown vencido já está livre
    errors = []
    room.send_to = capture_error
    asyncio.run(room.handle_use_item("p1", "calice_eter"))
    check("sem slot gasto, mantém item e ação bônus", len(player["bag"]) == 1
          and not player.get("bonus_action_used")
          and player["slots_cooldown"]["primeiro"] == [] and bool(errors))

    room, player = setup_room("mage")
    chalice = copy.deepcopy(item) if item else {
        "id": "calice_eter", "effect": "restore_spell_slot", "circle": "primeiro"}
    player["bag"] = [chalice]
    player["slots_cooldown"]["primeiro"] = [5]
    player["bonus_action_used"] = True
    asyncio.run(room.handle_use_item("p1", "calice_eter"))
    check("ação bônus já usada não consome cálice nem slot", len(player["bag"]) == 1
          and player["slots_cooldown"]["primeiro"] == [5])


if __name__ == "__main__":
    main()
