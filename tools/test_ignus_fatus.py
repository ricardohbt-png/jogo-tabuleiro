"""Regressions for the Ignus Fatus and Fata Morgana consumables."""
import asyncio
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import CITY_SHOPS, FLOOR, SHOP_MERCHANT, GameRoom, _city_shop_items, make_player

PASS = FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  XX  {name}")


def setup_room():
    room = GameRoom("IGNUS_FATUS_TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room.phase = "playing"
    room.round_num = 1
    room.tiles = [[FLOOR for _ in range(12)] for _ in range(12)]
    room.map_w = room.map_h = 12
    room.player_order = ["p1"]
    room.turn_index = 0
    player = make_player("p1", "Teste", "warrior", 0)
    player["pos"] = [3, 3]
    player["action_done"] = False
    room.players["p1"] = player
    room._is_turn = lambda pid: pid == "p1"
    return room, player


async def use_at(room, item_id, pos):
    try:
        await room.handle_use_item("p1", item_id, target_pos=pos)
        return True
    except TypeError:
        return False


def add_illusion(room, owner="p1", kind="fata_morgana", pos=None):
    illusion_id = f"illusion-{owner}"
    room.illusions[illusion_id] = {
        "id": illusion_id, "owner_pid": owner, "room_id": None,
        "kind": kind, "pos": list(pos or [4, 3]), "created_round": room.round_num,
        "expires_round": room.round_num + (4 if kind == "fata_morgana" else 2),
    }
    return room.illusions[illusion_id]


def add_monster(room, mid="goblin", pos=None, **extra):
    monster = {
        "id": mid, "name": "Goblin", "type": "goblin", "pos": list(pos or [7, 3]),
        "hp": 12, "max_hp": 12, "ca": 12, "atk_bonus": 0, "damage": "1d4",
        "movement": 4, "base_movement": 6, "vision_base": 0,
        "room_id": None, "special_abilities": [], "attacks": [],
        **extra,
    }
    room.monsters[mid] = monster
    return monster


async def main():
    ids = {
        "ignus_fatus": (45, 2, "assets/itens/ignus_fatus.png"),
        "fata_morgana": (120, 4, "assets/itens/fata_morgana.png"),
    }
    catalog = {item.get("id"): item for item in SHOP_MERCHANT}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("\n[1] Catálogo, imagens e estoque")
    for item_id, (price, rounds, icon) in ids.items():
        item = catalog.get(item_id)
        check(f"{item_id} custa {price}, dura {rounds} rodadas e tem efeito de isca",
              bool(item and item.get("price") == price and item.get("buy_price", price) == price
                   and item.get("item_slot") == "bag" and item.get("effect") == "illusion_lure"
                   and item.get("value") == rounds))
        check(f"{item_id} usa o PNG aprovado", bool(item and item.get("icon") == icon
              and os.path.isfile(os.path.join(root, icon))))
    merchant_cities = [city for city, shops in CITY_SHOPS.items()
                       if isinstance(shops.get("mercador"), list)]
    check("os dois itens aparecem em todos os mercadores cadastrados",
          len(merchant_cities) == 4 and all(
              {item["id"] for item in _city_shop_items(city, "mercador")}
              >= set(ids) for city in merchant_cities))

    print("\n[2] Uso autoritativo e duração")
    for item_id, (price, rounds, _icon) in ids.items():
        room, player = setup_room()
        item = deepcopy(catalog[item_id]) if item_id in catalog else {
            "id": item_id, "effect": "illusion_lure", "value": rounds,
        }
        player["bag"] = [item]
        accepted = await use_at(room, item_id, [4, 3])
        active = list(getattr(room, "illusions", {}).values())
        check(f"{item_id} cria uma ilusão com duração e estado sincronizado",
              accepted and len(active) == 1 and active[0].get("kind") == item_id
              and active[0].get("owner_pid") == "p1" and active[0].get("pos") == [4, 3]
              and active[0].get("expires_round") == room.round_num + rounds
              and room._game_state_payload().get("illusions", [None])[0] == active[0])
        check(f"{item_id} consome item e ação bônus ao criar",
              accepted and player.get("bonus_action_used") is True and not player["bag"])

    print("\n[3] Validação antes do consumo")
    for item_id, (price, rounds, _icon) in ids.items():
        room, player = setup_room()
        item = deepcopy(catalog[item_id]) if item_id in catalog else {
            "id": item_id, "effect": "illusion_lure", "value": rounds,
        }
        player["bag"] = [item]
        supported = await use_at(room, item_id, [10, 3])
        check(f"{item_id} rejeita posição fora do alcance sem cobrar custo",
              supported and len(player["bag"]) == 1 and not player.get("bonus_action_used")
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        room._is_turn = lambda pid: False
        supported = await use_at(room, item_id, [4, 3])
        check(f"{item_id} rejeita uso fora do turno sem cobrar custo",
              supported and len(player["bag"]) == 1 and not player.get("bonus_action_used")
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        room.monsters = {"guard": {"id": "guard", "pos": [4, 3], "hp": 10}}
        supported = await use_at(room, item_id, [4, 3])
        check(f"{item_id} rejeita casa ocupada sem cobrar custo",
              supported and len(player["bag"]) == 1 and not player.get("bonus_action_used")
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        room.tiles[3][4] = server.WALL
        supported = await use_at(room, item_id, [5, 3])
        check(f"{item_id} rejeita linha de visão bloqueada sem cobrar custo",
              supported and len(player["bag"]) == 1 and not player.get("bonus_action_used")
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        player["bonus_action_used"] = True
        supported = await use_at(room, item_id, [4, 3])
        check(f"{item_id} rejeita ação bônus já gasta sem cobrar item",
              supported and len(player["bag"]) == 1
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        supported = await use_at(room, item_id, [4, 3])
        check(f"{item_id} rejeita ausência do item sem gastar ação",
              supported and not player.get("bonus_action_used")
              and not getattr(room, "illusions", {}))

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        await use_at(room, item_id, [4, 3])
        player["bonus_action_used"] = False
        player["bag"].append(deepcopy(item))
        await use_at(room, item_id, [5, 3])
        check(f"{item_id} impede segunda ilusão sem consumir item ou ação",
              len(player["bag"]) == 1 and not player.get("bonus_action_used")
              and len(getattr(room, "illusions", {})) == 1)

        room, player = setup_room()
        player["bag"] = [deepcopy(item)]
        accepted = await use_at(room, item_id, [4, 3])
        room.round_num += rounds
        payload = room._game_state_payload()
        check(f"{item_id} expira na rodada prevista e some do estado publicado",
              accepted and not payload.get("illusions"))

    print("\n[7] Remoção de memória após dissipação e expiração")
    room, _player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    monster = add_monster(room, pos=[7, 3], ai_last_seen={
        "target_id": illusion["id"], "pos": [4, 3], "round": room.round_num,
        "room_id": None,
    })
    room._remove_illusion(illusion["id"])
    check("dissipação limpa a última posição conhecida da isca",
          not monster.get("ai_last_seen"))
    illusion = add_illusion(room, pos=[4, 3])
    monster["ai_last_seen"] = {"target_id": illusion["id"], "pos": [4, 3],
                               "round": room.round_num, "room_id": None}
    room.round_num = illusion["expires_round"]
    room._expire_illusions()
    check("expiração limpa a última posição conhecida da isca",
          not room.illusions and not monster.get("ai_last_seen"))

    print("\n[4] Percepção e prioridade da isca")
    room, player = setup_room()
    illusion = add_illusion(room, pos=[5, 3])
    monster = add_monster(room, pos=[7, 3])
    targets = room._alvos_hostis_para_monstros()
    visible = room._alvos_visiveis_para_monstro(monster, targets)
    selected = room._get_monster_primary_target(monster, visible)
    check("a ilusão visível entra na lista de alvos hostis", any(
        target.get("kind") == "illusion" and target["obj"] is illusion
        for target in targets))
    check("monstro automático prioriza ilusão sobre herói visível",
          selected and selected.get("kind") == "illusion")

    room, _player = setup_room()
    illusion = add_illusion(room, pos=[11, 3])
    monster = add_monster(room, pos=[3, 3])
    check("ilusão além do raio de percepção não aparece como alvo",
          not any(target.get("kind") == "illusion" for target in
                  room._alvos_visiveis_para_monstro(monster,
                                                    room._alvos_hostis_para_monstros())))

    room, _player = setup_room()
    illusion = add_illusion(room, pos=[5, 3])
    monster = add_monster(room, pos=[7, 3])
    room.tiles[3][6] = server.WALL
    check("ilusão atrás de parede não aparece como alvo",
          not any(target.get("kind") == "illusion" for target in
                  room._alvos_visiveis_para_monstro(monster,
                                                    room._alvos_hostis_para_monstros())))

    room, _player = setup_room()
    illusion = add_illusion(room, pos=[5, 3])
    manual = add_monster(room, pos=[7, 3], control_mode="manual")
    check("monstro manual não recebe desvio automático para a ilusão",
          room._monster_illusion_target(manual) is None)

    print("\n[5] Movimento da Fata Morgana")
    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    player["moves_left"] = 5
    moved = getattr(room, "handle_move_illusion", None)
    accepted = False
    if moved:
        await moved("p1", illusion["id"], [10, 3])
        accepted = illusion.get("pos") == [10, 3]
    check("Fata Morgana percorre até seis casas por ordem do herói",
          accepted and illusion.get("move_order_round") == room.round_num)
    check("mover a ilusão não consome o movimento do herói",
          player.get("moves_left") == 5)

    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    moved = getattr(room, "handle_move_illusion", None)
    if moved:
        await moved("p1", illusion["id"], [11, 3])
    check("trajeto acima de seis casas é recusado sem registrar ordem",
          moved is not None and illusion["pos"] == [4, 3]
          and illusion.get("move_order_round") != room.round_num)

    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    for y in range(room.map_h):
        room.tiles[y][6] = server.WALL
    moved = getattr(room, "handle_move_illusion", None)
    if moved:
        await moved("p1", illusion["id"], [8, 3])
    check("Fata Morgana não atravessa parede nem registra ordem inválida",
          moved is not None and illusion["pos"] == [4, 3]
          and illusion.get("move_order_round") != room.round_num)

    room, _player = setup_room()
    illusion = add_illusion(room, pos=[5, 3])
    monster = add_monster(room, pos=[7, 3])
    seen = room._monster_illusion_target(monster)
    if seen:
        room._monster_remember_visible_targets(monster, [seen])
    room.tiles[3][6] = server.WALL
    remembered = room._monster_illusion_target(monster)
    check("monstro que já viu a isca persegue a última posição conhecida",
          remembered and remembered.get("remembered")
          and remembered.get("pursuit_pos") == [5, 3])

    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    moved = getattr(room, "handle_move_illusion", None)
    if moved:
        await moved("p1", illusion["id"], [5, 3])
        room.round_num += 1
        player["moved_this_turn"] = False
        player["action_done"] = False
        await moved("p1", illusion["id"], [6, 3])
    check("Fata Morgana recebe uma nova ordem na rodada seguinte",
          moved is not None and illusion["pos"] == [6, 3]
          and illusion.get("move_order_round") == room.round_num)

    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    moved = getattr(room, "handle_move_illusion", None)
    accepted = False
    if moved:
        await moved("p1", illusion["id"], None)
        accepted = illusion.get("move_order_round") == room.round_num
        before = list(illusion["pos"])
        await moved("p1", illusion["id"], [5, 3])
        accepted = accepted and illusion.get("pos") == before
    check("pular movimento encerra a ordem e impede outra na mesma rodada", accepted)

    for field, value in (("moved_this_turn", True), ("action_done", True)):
        room, player = setup_room()
        illusion = add_illusion(room, pos=[4, 3])
        player[field] = value
        moved = getattr(room, "handle_move_illusion", None)
        if moved:
            await moved("p1", illusion["id"], [5, 3])
        check(f"ordem rejeitada após {field}",
              moved is not None and illusion["pos"] == [4, 3]
              and illusion.get("move_order_round") != room.round_num)

    room, _player = setup_room()
    illusion = add_illusion(room, kind="ignus_fatus", pos=[4, 3])
    moved = getattr(room, "handle_move_illusion", None)
    if moved:
        await moved("p1", illusion["id"], [5, 3])
    check("Ignus Fatus não aceita movimento", moved is not None
          and illusion["pos"] == [4, 3]
          and illusion.get("move_order_round") != room.round_num)

    print("\n[6] Dissipação no turno do monstro e retomada da busca")
    room, player = setup_room()
    add_illusion(room, pos=[4, 3])
    monster = add_monster(room, pos=[8, 3])
    player["alive"] = False
    room._monstro_ativo_em_combate = lambda _m: True
    async def no_turn_cost(*_args, **_kwargs):
        return True
    async def no_retaliation(*_args, **_kwargs):
        return False
    room._upkeep_inicio_turno_monstro = no_turn_cost
    room._monster_search_retaliation = no_retaliation
    await room.gm_phase(only_monster=monster)
    check("monstro ainda persegue uma ilusão ativa se o herói cair",
          monster["pos"] != [8, 3] and bool(room.illusions))

    room, player = setup_room()
    illusion = add_illusion(room, pos=[4, 3])
    monster = add_monster(room, pos=[5, 3])
    hp_before = player["hp"]

    async def no_turn_cost(*_args, **_kwargs):
        return True

    async def no_retaliation(*_args, **_kwargs):
        return False

    room._monstro_ativo_em_combate = lambda _m: True
    room._upkeep_inicio_turno_monstro = no_turn_cost
    room._monster_search_retaliation = no_retaliation
    room._monster_hostile_targets = lambda _m: []
    await room.gm_phase(only_monster=monster)
    check("primeiro ataque dissipa a ilusão, não fere o herói e encerra o turno",
          illusion["id"] not in room.illusions and player["hp"] == hp_before
          and not monster.get("ai_last_seen"))
    after = room._alvos_visiveis_para_monstro(monster,
                                             room._alvos_hostis_para_monstros())
    selected = room._get_monster_primary_target(monster, after)
    check("depois da dissipação a IA volta a escolher heróis normalmente",
          selected and selected.get("kind") == "player" and selected["obj"] is player)

    if FAIL:
        print(f"\n{FAIL} falha(s), {PASS} aprovação(ões)")
        raise SystemExit(1)
    print(f"\n{PASS} aprovações, 0 falhas")


if __name__ == "__main__":
    asyncio.run(main())
