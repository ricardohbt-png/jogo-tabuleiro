"""Testa a Bota Alada: catálogo, compra, slot de botas e voo derivado."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def test_catalogo():
    item = next(i for i in S.SHOP_MERCHANT if i["id"] == "bota_alada")
    assert item["price"] == 0
    assert item["item_slot"] == "boots"
    assert item["kind"] == "boots"
    assert item["effect"] == "voo"
    assert "bota_alada" in S.CITY_SHOPS["alva_e_luz"]["mercador"]
    assert S.GameRoom._slot_category_for_item(item) == "boots"


def test_compra_equipamento():
    async def run():
        room = S.GameRoom("WINGED_BOOT_TEST")
        room.phase = "city"
        room.world_location = "alva_e_luz"
        player = S.make_player("p1", "Richard", "paladin", 0)
        player["gold"] = 0
        room.players[player["id"]] = player

        room.broadcast = lambda *args, **kwargs: asyncio.sleep(0)
        room.broadcast_city_state = lambda: asyncio.sleep(0)
        room.send_to = lambda *args, **kwargs: asyncio.sleep(0)
        room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)

        await room.handle_shop_buy("p1", "mercador", "bota_alada")
        assert player["gold"] == 0
        assert len(player["bag"]) == 1
        assert player["bag"][0]["id"] == "bota_alada"

        await room.handle_equip_from_bag("p1", 0)
        assert player["gear"]["boots"]["id"] == "bota_alada"
        assert player["voo"] is True
        assert player["voo_bota_alada"] is True
        assert player["altura"] == S.ALTURA_INICIAL_VOO == 2
        assert player["altura_max"] == S.ALTURA_MAX == 10
        assert player["pode_alterar_altura"] is True

        room.phase = "playing"
        room.player_order = ["p1"]
        room.turn_index = 0
        room.push_state = lambda: asyncio.sleep(0)
        player["moves_left"] = 8
        for _ in range(8):
            await room.handle_alterar_altura("p1", 1)
        assert player["altura"] == 10
        assert player["moves_left"] == 0
        await room.handle_alterar_altura("p1", 1)
        assert player["altura"] == 10
        assert player["moves_left"] == 0

        player["altura"] = 3
        await room.handle_unequip("p1", "boots")
        assert player["gear"]["boots"] is None
        assert player["voo"] is False
        assert player["altura"] == S.ALTURA_MIN

    asyncio.run(run())


def test_magia_e_bota_coexistem():
    room = S.GameRoom("WINGED_BOOT_SOURCE_TEST")
    player = S.make_player("p1", "Richard", "paladin", 0)
    player["gear"]["boots"] = {"id": "bota_alada", "effect": "voo", "item_slot": "boots"}
    player["voo_magico"] = True
    player["altura"] = 8
    room._atualizar_voo_heroi(player)
    assert player["voo"] is True
    assert player["altura"] == 8
    assert player["altura_max"] == S.ALTURA_MAX == 10

    player["gear"]["boots"] = None
    room._atualizar_voo_heroi(player)
    assert player["voo"] is True
    assert player["altura_max"] == S.ALTURA_MAX


def test_desequipar_no_ar_causa_queda():
    async def run():
        room = S.GameRoom("WINGED_BOOT_FALL_TEST")
        room.phase = "city"
        player = S.make_player("p1", "Richard", "paladin", 0)
        player["gear"]["boots"] = {"id": "bota_alada", "effect": "voo", "item_slot": "boots"}
        player["voo"] = True
        player["altura"] = 3
        player["hp"] = 20
        room.players[player["id"]] = player
        room.broadcast = lambda *args, **kwargs: asyncio.sleep(0)
        room.broadcast_city_state = lambda: asyncio.sleep(0)
        room.push_state = lambda: asyncio.sleep(0)
        room.send_to = lambda *args, **kwargs: asyncio.sleep(0)
        room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)

        async def fixed_fall_roll(*args, **kwargs):
            return 2
        room._rolar_dano_mostrado = fixed_fall_roll

        await room.handle_unequip("p1", "boots")
        assert player["gear"]["boots"] is None
        assert player["altura"] == S.ALTURA_MIN
        assert player["voo"] is False
        assert player["hp"] == 18

    asyncio.run(run())


def test_substituir_bota_no_ar_causa_queda():
    async def run():
        room = S.GameRoom("WINGED_BOOT_SWAP_FALL_TEST")
        room.phase = "city"
        player = S.make_player("p1", "Richard", "paladin", 0)
        player["gear"]["boots"] = {"id": "bota_alada", "effect": "voo", "item_slot": "boots"}
        player["voo"] = True
        player["altura"] = 3
        player["hp"] = 20
        player["bag"] = [{"id": "boots_leather", "name": "Botas de Couro",
                           "item_slot": "boots", "effect": "def_", "value": 0}]
        room.players[player["id"]] = player
        room.broadcast = lambda *args, **kwargs: asyncio.sleep(0)
        room.broadcast_city_state = lambda: asyncio.sleep(0)
        room.push_state = lambda: asyncio.sleep(0)
        room.send_to = lambda *args, **kwargs: asyncio.sleep(0)
        room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)

        async def fixed_fall_roll(*args, **kwargs):
            return 2
        room._rolar_dano_mostrado = fixed_fall_roll

        await room.handle_equip_from_bag("p1", 0)
        assert player["gear"]["boots"]["id"] == "boots_leather"
        assert player["altura"] == S.ALTURA_MIN
        assert player["hp"] == 18

    asyncio.run(run())


if __name__ == "__main__":
    test_catalogo()
    test_compra_equipamento()
    test_magia_e_bota_coexistem()
    test_desequipar_no_ar_causa_queda()
    test_substituir_bota_no_ar_causa_queda()
    print("5 passed, 0 failed")
