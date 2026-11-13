"""Regressões da Lâmpada da Vigília Arcana.
Roda da raiz: python -X utf8 tools/test_lampada_vigilia_arcana.py
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
from server import (CITY_SHOPS, FLOOR, GameRoom, MONSTER_DEFS, SHOP_MERCHANT,
                    _city_shop_items, make_monster, make_player)

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
    room = GameRoom("LAMPADA_VIGILIA_ARCANA")

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
    print("\n[1] Catálogo, estoque e ativação")
    lampada = next((i for i in SHOP_MERCHANT
                    if i["id"] == "lampada_vigilia_arcana"), None)
    check("item universal custa 60 moedas e revela criaturas por 10 rodadas",
          bool(lampada and lampada.get("name") == "Lâmpada da Vigília Arcana"
               and lampada.get("price") == 60 and lampada.get("item_slot") == "bag"
               and lampada.get("effect") == "arcane_vigilance_potion"
               and lampada.get("value") == 10 and lampada.get("radius") == 3
               and not lampada.get("allowed_classes")))
    check("ícone aponta para o PNG transparente criado para o item",
          bool(lampada and lampada.get("icon") == "assets/itens/lampada_vigilia_arcana.png"
               and os.path.isfile(os.path.join(os.path.dirname(__file__), "..", "assets",
                                               "itens", "lampada_vigilia_arcana.png"))))
    cidades = [c for c, shops in CITY_SHOPS.items()
               if isinstance(shops.get("mercador"), list)
               and c != "vila_dos_charcos"]   # loja especial da Zumbra, com estoque próprio
    check("está no estoque de todos os mercadores cadastrados",
          len(cidades) == 4 and all(any(i["id"] == "lampada_vigilia_arcana"
                                        for i in _city_shop_items(c, "mercador"))
                                    for c in cidades))

    room, player = setup()
    player["bag"] = [deepcopy(lampada)] if lampada else [{
        "id": "lampada_vigilia_arcana", "name": "Lâmpada da Vigília Arcana",
        "effect": "arcane_vigilance_potion", "value": 10, "radius": 3,
    }]
    await room.handle_use_item("p1", "lampada_vigilia_arcana")
    check("usa ação bônus, consome o item e inicia duração de 10 rodadas",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("lampada_vigilia_arcana_expira_em") == room.round_num + 10
          and room._game_state_payload()["players"][0]["lampada_vigilia_arcana_rodadas"] == 10)

    room, player = setup()
    player["bonus_action_used"] = True
    player["bag"] = [deepcopy(lampada)] if lampada else [{
        "id": "lampada_vigilia_arcana", "effect": "arcane_vigilance_potion",
        "value": 10, "radius": 3,
    }]
    await room.handle_use_item("p1", "lampada_vigilia_arcana")
    check("se ação bônus já foi gasta, não consome item nem ativa a luz",
          len(player["bag"]) == 1 and "lampada_vigilia_arcana_expira_em" not in player)

    print("\n[2] Revelação de criaturas ocultas")
    room, player = setup()
    player["lampada_vigilia_arcana_expira_em"] = room.round_num + 10
    aliado = make_player("p2", "Aliado", "mage", 0)
    aliado["pos"] = [9, 3]
    room.players["p2"] = aliado
    room.monsters = {
        "inimigo_perto": {"id": "inimigo_perto", "type": "orc", "name": "Orc",
                           "pos": [4, 5], "hp": 10, "invisivel_sombras": True},
        "inimigo_na_borda": {"id": "inimigo_na_borda", "type": "goblin", "name": "Goblin",
                              "pos": [6, 3], "hp": 10, "invisivel_sombras": True},
        "inimigo_longe": {"id": "inimigo_longe", "type": "orc", "name": "Orc distante",
                          "pos": [9, 9], "hp": 10, "invisivel_sombras": True},
        "inimigo_visivel": {"id": "inimigo_visivel", "type": "orc", "name": "Orc visível",
                             "pos": [4, 3], "hp": 10, "invisivel_sombras": False},
        "inimigo_aliado": {"id": "inimigo_aliado", "type": "goblin", "name": "Goblin do aliado",
                           "pos": [9, 5], "hp": 10, "invisivel_sombras": True},
    }
    payload = room._game_state_payload()
    monsters = {m["id"]: m for m in payload["monsters"]}
    check("marca como revelados os ocultos dentro do raio de 3, inclusive diagonal",
          monsters["inimigo_perto"].get("revealed_by_arcane_vigilance")
          and monsters["inimigo_na_borda"].get("revealed_by_arcane_vigilance"))
    check("não revela criatura fora do raio e mantém inimigo visível normal",
          not monsters["inimigo_longe"].get("revealed_by_arcane_vigilance")
          and not monsters["inimigo_visivel"].get("revealed_by_arcane_vigilance"))
    check("revelação não encerra o estado de ocultação do monstro",
          room.monsters["inimigo_perto"].get("invisivel_sombras") is True)

    aliado["lampada_vigilia_arcana_expira_em"] = room.round_num + 10
    player.pop("lampada_vigilia_arcana_expira_em", None)
    player["pos"] = [0, 0]
    monsters = {m["id"]: m for m in room._game_state_payload()["monsters"]}
    check("a área compartilhada acompanha a posição de qualquer aliado ativo",
          monsters["inimigo_aliado"].get("revealed_by_arcane_vigilance")
          and not monsters["inimigo_perto"].get("revealed_by_arcane_vigilance"))

    room.round_num = aliado["lampada_vigilia_arcana_expira_em"]
    monsters = {m["id"]: m for m in room._game_state_payload()["monsters"]}
    check("revelação termina exatamente ao alcançar a rodada de expiração",
          not monsters["inimigo_perto"].get("revealed_by_arcane_vigilance"))

    room, player = setup()
    async def noop(*args, **kwargs):
        pass
    room.send_to = noop
    alvo = make_monster(next(m for m in MONSTER_DEFS if m["type"] == "goblin"),
                        {"id": "oculto", "cx": 4, "cy": 3})
    alvo.update(id="oculto", pos=[4, 3], hp=20, max_hp=20, ac=1,
                invisivel_sombras=True)
    room.monsters = {"oculto": alvo}
    await room.handle_attack("p1", "oculto")
    recusado = not player.get("action_done") and alvo["hp"] == 20
    player["lampada_vigilia_arcana_expira_em"] = room.round_num + 10
    await room.handle_attack("p1", "oculto")
    check("o servidor ainda recusa ocultos sem lâmpada e aceita o ataque revelado",
          recusado and player.get("action_done") and alvo["hp"] < 20)

    if FAIL:
        print(f"\n{FAIL} falha(s), {PASS} aprovação(ões)")
        raise SystemExit(1)
    print(f"\n{PASS} aprovações, 0 falhas")


if __name__ == "__main__":
    asyncio.run(main())
