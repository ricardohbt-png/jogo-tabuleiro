"""Testes da Vela Reveladora, consumível de exploração.
Roda da raiz: python tools/test_vela_reveladora.py
"""
import asyncio
import os
import sys
from copy import deepcopy

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import (ARMADILHAS, CITY_SHOPS, FLOOR, GameRoom, SHOP_MERCHANT,
                    _city_shop_items, make_player)

PASS = FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  XX  {name}")


def setup():
    room = GameRoom("VELA_REVELADORA")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    room.round_num = 1
    room.tiles = [[FLOOR for _ in range(12)] for _ in range(12)]
    room.map_w = room.map_h = 12
    player = make_player("p1", "Teste", "warrior", 0)
    player["pos"] = [3, 3]
    room.players["p1"] = player
    return room, player


async def main():
    print("\n[1] Catálogo e uso")
    vela = next((i for i in SHOP_MERCHANT if i["id"] == "vela_reveladora"), None)
    check("é vendida por 80 moedas como consumível de bolsa",
          bool(vela and vela.get("name") == "Vela Reveladora"
               and vela.get("price") == 80 and vela.get("item_slot") == "bag"
               and vela.get("effect") == "reveal_traps_potion"
               and vela.get("value") == 10))
    check("usa o PNG do item no inventário",
          bool(vela and vela.get("icon") == "assets/itens/vela_reveladora.png"
               and os.path.isfile(os.path.join(os.path.dirname(__file__), "..",
                                               "assets", "itens", "vela_reveladora.png"))))
    cidades_com_mercador = [cidade for cidade, lojas in CITY_SHOPS.items()
                            if isinstance(lojas.get("mercador"), list)]
    check("está no estoque dos mercadores das cidades que já têm essa loja",
          len(cidades_com_mercador) == 4 and all(
              any(i["id"] == "vela_reveladora"
                  for i in _city_shop_items(cidade, "mercador"))
              for cidade in cidades_com_mercador))

    room, player = setup()
    player["bag"] = [deepcopy(vela)] if vela else [{
        "id": "vela_reveladora", "name": "Vela Reveladora", "emoji": "🕯️",
        "effect": "reveal_traps_potion", "value": 10,
    }]
    await room.handle_use_item("p1", "vela_reveladora")
    check("consome uma vela, usa ação bônus e ativa por 10 rodadas",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("vela_reveladora_expira_em") == room.round_num + 10
          and room._game_state_payload()["players"][0]["vela_reveladora_rodadas"] == 10)

    room, player = setup()
    player["bonus_action_used"] = True
    player["bag"] = [deepcopy(vela)] if vela else [{
        "id": "vela_reveladora", "name": "Vela Reveladora", "emoji": "🕯️",
        "effect": "reveal_traps_potion", "value": 10,
    }]
    await room.handle_use_item("p1", "vela_reveladora")
    check("não consome a vela nem ativa efeito quando a ação bônus já foi usada",
          len(player["bag"]) == 1 and "vela_reveladora_expira_em" not in player)

    room, player = setup()
    room.round_num = 4
    player["vela_reveladora_expira_em"] = 6
    player["bag"] = [deepcopy(vela)]
    await room.handle_use_item("p1", "vela_reveladora")
    check("acender outra vela renova a duração a partir da rodada atual",
          player.get("vela_reveladora_expira_em") == 14)
    aliado = make_player("p2", "Aliado", "mage", 0)
    aliado["pos"] = [10, 3]
    aliado["vela_reveladora_expira_em"] = 14
    room.players["p2"] = aliado
    room.traps = [{"id": "raio_aliado", "pos": [10, 3], "triggered": False}]
    check("a área de velas de qualquer herói é compartilhada com o grupo",
          any(t["id"] == "raio_aliado" for t in room._game_state_payload()["traps"]))

    print("\n[2] Revelação temporária e raio móvel")
    room, player = setup()
    player["vela_reveladora_expira_em"] = room.round_num + 10
    room.traps = [
        {"id": "dentro", "pos": [4, 3], "triggered": False},
        {"id": "limite", "pos": [3, 6], "triggered": False},
        {"id": "fora", "pos": [10, 3], "triggered": False},
        {"id": "disparada", "pos": [5, 3], "triggered": True},
        {"id": "descoberta", "pos": [9, 3], "triggered": False},
    ]
    tipo_armadilha = next(iter(ARMADILHAS))
    room.armadilhas = [
        {"id": "colocada_dentro", "tipo": tipo_armadilha, "pos": [4, 4],
         "visivel": False, "esgotada": False, "criador": "monstro"},
        {"id": "colocada_fora", "tipo": tipo_armadilha, "pos": [10, 5],
         "visivel": False, "esgotada": False, "criador": "monstro"},
    ]
    room.decorations = [{
        "id": "decor_armadilha", "type": "cama", "pos": [4, 5],
        "facing": [0, 1], "trap": {"tipo": tipo_armadilha},
        "trap_revealed": False, "trap_triggered": False, "trap_disarmed": False,
    }]
    room.explored.add((9, 3))
    payload = room._game_state_payload()
    visiveis = {t["id"] for t in payload["traps"]}
    temporarias = {t["id"] for t in payload["traps"] if t.get("vela_revelada")}
    check("revela armadilhas ativas até 3 casas, incluindo a borda diagonal",
          {"dentro", "limite"}.issubset(visiveis) and "fora" not in visiveis)
    check("marca ao cliente quais armadilhas foram vistas apenas pela vela",
          {"dentro", "limite"}.issubset(temporarias)
          and "descoberta" not in temporarias)
    check("não revela armadilha já disparada e preserva descoberta permanente",
          "disparada" not in visiveis and "descoberta" in visiveis
          and (9, 3) in room.explored)
    colocadas = {a["id"]: a for a in room._serializar_armadilhas()}
    decor = next(d for d in room._serializar_decoracoes() if d["id"] == "decor_armadilha")
    check("também revela armadilhas colocáveis e embutidas em objetos",
          colocadas["colocada_dentro"]["visivel"]
          and not colocadas["colocada_fora"]["visivel"]
          and decor["trap_revealed"])
    check("passa marcadores temporários para colocáveis e armadilhas em objetos",
          colocadas["colocada_dentro"].get("vela_revelada")
          and not colocadas["colocada_fora"].get("vela_revelada")
          and decor.get("trap_revelada_vela"))
    check("revelação temporária não grava descoberta permanente",
          room.armadilhas[0]["visivel"] is False
          and room.decorations[0]["trap_revealed"] is False)

    player["pos"] = [10, 3]
    payload = room._game_state_payload()
    visiveis = {t["id"] for t in payload["traps"]}
    temporarias = {t["id"] for t in payload["traps"] if t.get("vela_revelada")}
    check("o raio acompanha o personagem e retira a revelação temporária fora dele",
          "fora" in visiveis and "dentro" not in visiveis and "limite" not in visiveis
          and "descoberta" in visiveis)
    check("marcador temporário acompanha o herói sem persistir no mapa",
          "fora" in temporarias and "dentro" not in temporarias
          and "limite" not in temporarias)
    colocadas = {a["id"]: a for a in room._serializar_armadilhas()}
    decor = next(d for d in room._serializar_decoracoes() if d["id"] == "decor_armadilha")
    check("armadilhas colocáveis e em objetos também acompanham o raio",
          colocadas["colocada_fora"]["visivel"]
          and not colocadas["colocada_dentro"]["visivel"]
          and not decor["trap_revealed"])

    room.round_num = player["vela_reveladora_expira_em"]
    payload = room._game_state_payload()
    visiveis = {t["id"] for t in payload["traps"]}
    temporarias = {t["id"] for t in payload["traps"] if t.get("vela_revelada")}
    check("a revelação temporária termina após 10 rodadas",
          visiveis == {"descoberta"} and not temporarias
          and not any(a.get("vela_revelada") for a in room._serializar_armadilhas())
          and not any(d.get("trap_revelada_vela")
                      for d in room._serializar_decoracoes()))

    if FAIL:
        print(f"\n{FAIL} falha(s), {PASS} aprovação(ões)")
        raise SystemExit(1)
    print(f"\n{PASS} aprovações, 0 falhas")


if __name__ == "__main__":
    asyncio.run(main())
