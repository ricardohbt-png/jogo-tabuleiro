"""Verifica o aprendizado e o primeiro efeito da magia Voo."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def _room_com_mapa():
    room = server.GameRoom("SPELL_FLIGHT_TEST")
    room.map_w = room.map_h = 8
    room.tiles = [[server.FLOOR for _ in range(room.map_w)] for _ in range(room.map_h)]
    room._decor_block_tiles = set()
    room._decor_tall_tiles = set()
    room._mat_solid_tiles = set()
    room._mat_oclui_tiles = set()
    return room


def test_catalogo_e_alcance():
    magia = server.GRIMORIO["voo"]
    assert "voo" in server.GRIMORIO_IMPLEMENTADAS
    assert magia["tipo"] == "alvo_aliado"
    assert magia["alcance_base"] == 3
    assert magia["alcance_por_niveis"] == 3
    assert "magia_voo" in server.CITY_SHOPS["alva_e_luz"]["templo"]
    item = next(i for i in server.SHOP_TEMPLE if i["id"] == "magia_voo")
    assert item["price"] == 0
    assert item["effect"] == "learn_spell"

    room = _room_com_mapa()
    caster = {"id": "p1", "level": 1, "pos": [1, 1], "altura": 0}
    assert room._alcance_magia_teto(magia, 1) == 3
    assert room._alcance_magia_teto(magia, 2) == 3
    assert room._alcance_magia_teto(magia, 3) == 4
    assert room._alcance_magia_teto(magia, 6) == 5
    assert room._geminada_alvo2_valido(caster, magia,
        {"id": "p2", "alive": True, "hp": 10, "pos": [5, 1], "altura": 0}) is False


def test_compra_e_ativacao():
    async def run():
        room = _room_com_mapa()
        room.phase = "city"
        room.world_location = "alva_e_luz"
        p = server.make_player("p1", "Pedro", "mage", 0)
        p["gold"] = 0
        p["pos"] = [1, 1]
        room.players[p["id"]] = p
        room.broadcast = lambda *args, **kwargs: asyncio.sleep(0)
        room.broadcast_city_state = lambda: asyncio.sleep(0)
        room.send_to = lambda *args, **kwargs: asyncio.sleep(0)

        await room.handle_shop_buy("p1", "templo", "magia_voo")
        assert p["magias_conhecidas"] == ["voo"]
        assert p["gold"] == 0

        p["level"] = 3
        alvo = server.make_player("p2", "Lewis", "cleric", 1)
        alvo["pos"] = [5, 1]
        room.players[alvo["id"]] = alvo
        await room._executar_voo(p, server.GRIMORIO["voo"], {"target_id": "p2"})
        assert alvo["voo"] is True
        assert alvo["altura"] == server.ALTURA_INICIAL_VOO == 2
        assert alvo["altura_max"] == server.ALTURA_MAX == 10
        assert alvo["pode_alterar_altura"] is True

    asyncio.run(run())


if __name__ == "__main__":
    test_catalogo_e_alcance()
    test_compra_e_ativacao()
    print("2 passed, 0 failed")
