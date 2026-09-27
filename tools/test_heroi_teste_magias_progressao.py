"""Progressão D&D 3.5 de slots e escolhas de magia no herói temporário.
Roda da raiz: python -X utf8 tools/test_heroi_teste_magias_progressao.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, slots_max_para


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"  ✅ {name}")


async def main():
    print("\n[1] Progressão de slots do teste")
    for cls, expected_20 in (("mage", (4, 4, 4, 4, 4, 4, 4, 4, 4)),
                             ("cleric", (5, 5, 5, 5, 5, 4, 4, 4, 4))):
        p = make_player("test", "Teste", cls, 0)
        p["test_hero"] = True
        p["level"] = 1
        slots = slots_max_para(p)
        check(f"{cls}: nível 1 tem 2 espaços de 1º e nenhum de 0º",
              slots["primeiro"] == 2 and "zero" not in slots)
        p["level"] = 20
        slots = slots_max_para(p)
        check(f"{cls}: progressão base correta no nível 20",
              tuple(slots[c] for c in S._CIRCULOS_MAGIA_TESTE) == expected_20)

    p = make_player("test", "Teste", "mage", 0)
    p["test_hero"] = True
    check("recarga por círculo vai de 10 a 50 rodadas",
          [S._slot_recarga_para(p, c) for c in ("primeiro", "segundo", "terceiro", "nono")]
          == [10, 15, 20, 50])
    regular = make_player("regular", "Normal", "mage", 0)
    check("recarga padrão do jogo não muda", S._slot_recarga_para(regular, "quarto") == 25)

    print("\n[2] Quantidade de escolhas ao desbloquear e ganhar slots")
    room = GameRoom("TEST_SPELL_PROGRESSION")
    room.round_num = 1
    sent = []

    async def capture_send(pid, message):
        sent.append(message)

    async def noop(*args, **kwargs):
        pass

    room.send_to = capture_send
    room.gm_say = noop
    room.push_state = noop
    mage = make_player("mage", "Mago de teste", "mage", 0)
    mage.update(test_hero=True, level=2, xp=999, magias_conhecidas=[], pending_spell_pick=[])
    room.players["mage"] = mage
    await room._check_level_up(mage)
    mage_choices = [mid for mid, spell in S.GRIMORIO.items()
                    if mid in S.GRIMORIO_IMPLEMENTADAS
                    and "mage" in spell.get("classe", [])
                    and spell.get("circulo") == "segundo"]
    check("primeiro acesso a um círculo pede 2 magias", len(mage["pending_spell_pick"]) == 2
          and sent[-1].get("count") == 2 and sent[-1].get("circulo") == "segundo")
    check("opções só incluem magias existentes e implementadas",
          set(sent[-1].get("opcoes", [])) == set(mage_choices))

    await room.handle_escolher_magia_nivel("mage", mage_choices[0])
    check("após escolher uma, resta exatamente 1 escolha",
          mage["pending_spell_pick"] == ["segundo"] and sent[-1].get("count") == 1)
    await room.handle_escolher_magia_nivel("mage", mage_choices[1])
    check("duas escolhas concluem a fila sem duplicar magias",
          mage["pending_spell_pick"] == [] and len(mage["magias_conhecidas"]) == 2)

    sent.clear()
    mage["level"] = 3
    mage["xp"] = 999
    # Deixa uma opção distinta disponível para observar o ganho unitário.
    mage["magias_conhecidas"] = [mage_choices[0]]
    await room._check_level_up(mage)
    check("cada slot adicional concede +1 escolha no seu círculo",
          mage["pending_spell_pick"] == ["primeiro", "segundo"]
          and sent[-1].get("circulo") == "primeiro" and sent[-1].get("count") == 1)

    cleric = make_player("cleric", "Clérigo de teste", "cleric", 0)
    cleric.update(test_hero=True, level=2, xp=999, magias_conhecidas=[], pending_spell_pick=[])
    room.players["cleric"] = cleric
    await room._check_level_up(cleric)
    check("clérigo recebe 2 escolhas ao desbloquear o 2º círculo",
          cleric["pending_spell_pick"] == ["segundo", "segundo"]
          and sent[-1].get("count") == 2 and sent[-1].get("circulo") == "segundo")

    print("\n[3] Validação e criação com configuração inicial")
    create_room = GameRoom("TEST_HERO_CONFIG")
    create_room.test_mode = True
    create_room.master_pid = "master"
    create_room.phase = "playing"
    create_room.map_w = create_room.map_h = 8
    create_room.tiles = [[S.FLOOR for _ in range(8)] for _ in range(8)]
    create_room.chests = {}
    create_room.ground_items = {}
    create_room.monsters = {}
    async def noop(*args, **kwargs):
        pass
    create_room.push_state = noop
    create_room.gm_say = noop
    errors = []
    async def capture_error(pid, message):
        if message.get("type") == "error":
            errors.append(message.get("msg"))
    create_room.send_to = capture_error
    gear_options = create_room._opcoes_equipamento_heroi_teste("mage")
    check("catálogo autoritativo oferece slots e itens para mago",
          all(slot in gear_options for slot in S.GEAR_SLOTS)
          and any(item["id"] == "staff" for item in gear_options["weapon"])
          and any(item["id"] == "ring_str" for item in gear_options["ring1"]))

    first_circle = [mid for mid, spell in S.GRIMORIO.items()
                    if mid in S.GRIMORIO_IMPLEMENTADAS and "mage" in spell.get("classe", [])
                    and spell.get("circulo") == "primeiro"]
    evolution = next((entry for entry in S.GUILD_CATALOG.values()
                      if entry.get("categoria") == "especializacao"
                      and entry.get("classe") == "mage" and entry.get("nivel") == 1
                      and entry.get("requer") is None), None)
    cfg = {"level": 1, "gear": {"weapon": "staff", "ring1": "ring_str"},
           "all_spells": False, "spells": first_circle[:2],
           "guild_evolutions": ({evolution["linha"]: evolution["id"]} if evolution else {})}
    normalized, error = create_room._validar_config_heroi_teste("mage", cfg)
    check("config aceita 2 magias de 1º e evoluções de nível 1", error is None
          and len(normalized["spells"]) == 2)
    await create_room.handle_mestre_adicionar_heroi_teste("master", "mage", 2, 3, cfg)
    created = create_room.players.get("test_hero_mage")
    check("posicionamento cria o mago no nível e com as escolhas", created is not None
          and created["level"] == 1 and created["magias_conhecidas"] == first_circle[:2])
    check("equipamento selecionado aplica e slots não escolhidos ficam vazios", created is not None
          and created["gear"]["weapon"]["id"] == "staff"
          and created["gear"]["ring1"]["id"] == "ring_str"
          and all(created["gear"][slot] is None for slot in S.GEAR_SLOTS
                  if slot not in ("weapon", "ring1")))
    check("evolução escolhida entra com pré-requisitos na ficha temporária",
          created is not None and (not evolution or evolution["id"] in created["guild_owned"]["especializacoes"]))

    all_spells_cfg, all_spells_error = create_room._validar_config_heroi_teste(
        "mage", {"level": 3, "all_spells": True})
    mage_slots = S.slots_max_para({"test_hero": True, "class_id": "mage", "level": 3})
    expected_all = {mid for mid, spell in S.GRIMORIO.items()
                    if mid in S.GRIMORIO_IMPLEMENTADAS and "mage" in spell.get("classe", [])
                    and mage_slots.get(spell.get("circulo"), 0) > 0}
    check("opção todas as magias libera só círculos alcançados e implementados",
          all_spells_error is None and set(all_spells_cfg["spells"]) == expected_all
          and all(S.GRIMORIO[mid].get("circulo") != "zero" for mid in all_spells_cfg["spells"]))

    evolution_deep = S.GUILD_CATALOG.get("mago_reviver_4")
    deep_cfg, deep_error = create_room._validar_config_heroi_teste(
        "mage", {"level": 4, "all_spells": True,
                 "guild_evolutions": ({evolution_deep["linha"]: evolution_deep["id"]}
                                       if evolution_deep else {})})
    deep_chain = {"mago_reviver_4", "mago_reviver_3", "mago_reviver_2"}
    check("evolução alta inclui automaticamente todos os pré-requisitos",
          deep_error is None and deep_chain.issubset(set(deep_cfg["guild_evolutions"])))

    wrong_circle = next((mid for mid, spell in S.GRIMORIO.items()
                         if mid in S.GRIMORIO_IMPLEMENTADAS and "mage" in spell.get("classe", [])
                         and spell.get("circulo") != "primeiro"), None)
    _, wrong_circle_error = create_room._validar_config_heroi_teste(
        "mage", {"level": 1, "all_spells": False,
                 "spells": [first_circle[0], wrong_circle]})
    check("servidor recusa escolher magia de círculo ainda inacessível",
          wrong_circle is not None and bool(wrong_circle_error))

    warrior_gear = create_room._opcoes_equipamento_heroi_teste("warrior")
    greatsword = next((item["id"] for item in warrior_gear["weapon"]
                       if item["id"] in ("espada2m", "longsword_colossal", "espada_longa_colossal")), None)
    shield = next((item["id"] for item in warrior_gear["off_hand"]
                   if item["id"] in ("escudo_g", "escudo_p")), None)
    _, conflict_error = create_room._validar_config_heroi_teste(
        "warrior", {"level": 1, "gear": {"weapon": greatsword, "off_hand": shield}})
    check("servidor recusa arma de duas mãos junto com item secundário",
          greatsword is not None and shield is not None and bool(conflict_error))

    await create_room.handle_mestre_adicionar_heroi_teste("master", "rogue", 4, 3,
                                                         {"level": 7, "gear": {}})
    rogue = create_room.players.get("test_hero_rogue")
    check("nível alto cria ladino sem equipamento herdado", rogue is not None
          and rogue["level"] == 7 and all(rogue["gear"][slot] is None for slot in S.GEAR_SLOTS))

    bad_cfg = {"level": 1, "gear": {"head": "plate"}, "all_spells": True}
    _, bad_error = create_room._validar_config_heroi_teste("mage", bad_cfg)
    check("servidor recusa item em slot incompatível", bool(bad_error))

    print("\nPASS: progressão e escolhas verificadas")


if __name__ == "__main__":
    asyncio.run(main())
