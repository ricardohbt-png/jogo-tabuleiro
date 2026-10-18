"""Regressions for fixed-spell mage grimoires (shop, loot and casting)."""
import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, GRIMORIO, SHOP_MERCHANT, make_player, slots_max_para


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"  ✅ {name}")


def setup_room():
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room._broadcast_dado = noop
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room.round_num = 1
    room.phase = "playing"
    room.player_order = ["p1"]
    room.turn_index = 0
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    return room


def main():
    print("\n[1] Grimórios de loja: uma magia de 1º círculo, fixos e por 75 moedas")
    mage_first = [mid for mid, spell in GRIMORIO.items()
                  if "mage" in spell.get("classe", []) and spell.get("circulo") == "primeiro"]
    store_books = [item for item in SHOP_MERCHANT if item.get("effect") == "grimoire"]
    check("uma oferta por cada magia de 1º círculo do mago",
          len(store_books) == len(mage_first) and {i["magic_ids"][0] for i in store_books} == set(mage_first))
    check("cada livro da loja custa 75 e fica na mão do escudo",
          all(i.get("price") == 75 and i.get("item_slot") == "off_hand" for i in store_books))
    check("cada livro tem conteúdo imutável e ícone comum",
          all(i.get("fixed_magic_ids") and i.get("icon") == "assets/itens/grimorio.png" for i in store_books))
    check("todos os mercadores anunciam as ofertas de grimório",
          all(set(i["id"] for i in store_books).issubset(shop.get("mercador", []))
              for shop in server.CITY_SHOPS.values() if "mercador" in shop))

    print("\n[1b] Compra respeita preço e classe")
    room = setup_room()
    room.world_location = "alva_e_luz"
    room._em_cidade = lambda pid: True
    room.push_state_or_city = lambda *args, **kwargs: asyncio.sleep(0)
    mage_buyer = make_player("p1", "Pedro", "mage", 0)
    mage_buyer["gold"] = 100
    room.players["p1"] = mage_buyer
    asyncio.run(room.handle_shop_buy("p1", "mercador", "grimorio_voo"))
    check("Mago compra um livro fixo por 75 moedas",
          mage_buyer["gold"] == 25 and any(i.get("id") == "grimorio_voo" for i in mage_buyer["bag"]))
    cleric_buyer = make_player("p2", "Lewis", "cleric", 1)
    cleric_buyer["gold"] = 100
    room.players["p2"] = cleric_buyer
    asyncio.run(room.handle_shop_buy("p2", "mercador", "grimorio_voo"))
    check("Clérigo não compra livro de Mago nem perde ouro",
          cleric_buyer["gold"] == 100 and not cleric_buyer["bag"])

    print("\n[2] Loot raro de baú contém 2–3 magias distintas de mago")
    for count in (2, 3):
        book = server._criar_item_grimorio_bau(count=count, max_circulo="segundo")
        ids = book["magic_ids"]
        check(f"livro de {count} magias tem conteúdo fixo e distinto",
              len(ids) == count and len(set(ids)) == count and book["effect"] == "grimoire"
              and book["fixed_magic_ids"] is True)
        check(f"livro de {count} magias só usa magias do mago até 2º círculo",
              all("mage" in GRIMORIO[mid]["classe"] and
                  list(server.CIRCULOS_MAGIA).index(GRIMORIO[mid]["circulo"]) <= 1 for mid in ids))
        check(f"preço de revenda reflete 75 por círculo dobrado ({count})",
              book["buy_price"] == sum(75 * 2 ** list(server.CIRCULOS_MAGIA).index(GRIMORIO[mid]["circulo"])
                                        for mid in ids))

    print("\n[3] Grimório libera apenas magia equipada e não concede slots")
    room = setup_room()
    mage = make_player("p1", "Pedro", "mage", 0)
    mage["magias_conhecidas"] = ["relampago"]
    mage["action_done"] = False
    room.players["p1"] = mage
    errors = []

    async def capture(pid, message):
        if message.get("type") == "error":
            errors.append(message.get("msg", ""))

    room.send_to = capture
    book = next(i for i in store_books if i["magic_ids"] == ["voo"])
    mage["gear"]["off_hand"] = dict(book)
    max_slots = slots_max_para(mage).copy()
    known_payload = room._magias_conhecidas_com_grimorio(mage)
    check("magia do livro aparece só no payload, sem persistir na ficha",
          "voo" in known_payload and "voo" not in mage["magias_conhecidas"])
    check("equipar livro não aumenta slots", slots_max_para(mage) == max_slots)

    async def cast_equipped():
        await room.handle_magia("p1", {"magia_id": "voo", "target_id": "p1"})

    before = room._slots_disponiveis(mage, "primeiro")
    asyncio.run(cast_equipped())
    check("magia equipada é conjurada e consome o slot normal",
          room._slots_disponiveis(mage, "primeiro") == before - 1 and not errors)
    mage["gear"]["off_hand"] = None
    mage["action_done"] = False
    errors.clear()

    async def cast_unequipped():
        await room.handle_magia("p1", {"magia_id": "voo", "target_id": "p1"})

    before = room._slots_disponiveis(mage, "primeiro")
    asyncio.run(cast_unequipped())
    check("desequipar revoga magia sem gastar slot",
          bool(errors) and room._slots_disponiveis(mage, "primeiro") == before)

    mage["level"] = 1
    mage["gear"]["off_hand"] = server._criar_item_grimorio_bau(count=2, max_circulo="segundo")
    second = next(mid for mid in mage["gear"]["off_hand"]["magic_ids"]
                  if GRIMORIO[mid]["circulo"] == "segundo")
    mage["action_done"] = False
    errors.clear()

    async def cast_too_high():
        await room.handle_magia("p1", {"magia_id": second, "target_id": "p1"})

    before = room._slots_disponiveis(mage, "segundo")
    asyncio.run(cast_too_high())
    check("círculo sem slot máximo bloqueia antes de gastar recurso ou slot",
          bool(errors) and room._slots_disponiveis(mage, "segundo") == before)

    print("\n[4] Baús autorados materializam um conteúdo fixo")
    room = setup_room()
    room._spawn_chest([2, 2], 0, [server._DUNGEON_ITEM_CATALOG["grimorio_bau"]])
    chest = next(iter(room.chests.values()))
    check("o molde vira livro com 2–3 magias ao criar baú",
          chest["items"][0]["id"] == "grimorio_bau"
          and len(chest["items"][0]["magic_ids"]) in (2, 3))

    print("\n[5] Restrição de classe também vale para retirada do baú")
    cleric = make_player("p2", "Lewis", "cleric", 1)
    cleric["pos"] = [2, 2]
    room.players["p2"] = cleric
    erros_clerigo = []

    async def capture_cleric(pid, message):
        if message.get("type") == "error":
            erros_clerigo.append(message.get("msg", ""))

    room.send_to = capture_cleric
    chest_id = next(iter(room.chests))
    asyncio.run(room.handle_take_from_chest("p2", chest_id, "item", 0))
    check("clérigo não retira grimório exclusivo do Mago",
          bool(erros_clerigo) and chest_id in room.chests and len(room.chests[chest_id]["items"]) == 1)

    print("\n[6] Baú procedural sorteia grimório raro sem duplicar conteúdo")
    room = setup_room()
    with patch.object(server.random, "random", return_value=0.01):
        asyncio.run(room._spawn_chest_from_room({"cx": 4, "cy": 4, "looted": False}))
    chest = next(iter(room.chests.values()))
    check("chance rara substitui o primeiro item do baú por grimório",
          chest["items"][0].get("effect") == "grimoire"
          and 2 <= len(chest["items"][0].get("magic_ids", [])) <= 3)


if __name__ == "__main__":
    main()
