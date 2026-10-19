"""Testes das poções consumíveis do Templo.
Roda da raiz: python tools/test_potions.py
"""
import asyncio
import os
import sys
from copy import deepcopy
from unittest.mock import patch

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import ARREMESSAVEIS, CITY_SHOPS, FLOOR, GameRoom, SHOP_TEMPLE, _city_shop_items, make_player, mod, _hero_attack_bonus_with_weapon, get_bonus_constituicao

PASS = FAIL = 0

def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  XX  {name}")

def potion(item_id):
    return deepcopy(next(i for i in SHOP_TEMPLE if i["id"] == item_id))

def setup():
    room = GameRoom("POTION")
    async def noop(*args, **kwargs):
        pass
    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    player = make_player("p1", "Teste", "warrior", 0)
    room.players["p1"] = player
    return room, player

async def main():
    print("\n[1] Catálogo do Templo")
    small = potion("health_potion_small")
    normal = potion("health_potion")
    concentrated = potion("health_potion_concentrated")
    improved = potion("health_potion_improved")
    regeneration = potion("regeneration_potion")
    check("pequena cura 5 e custa 40% arredondado", small["value"] == 5 and small["price"] == 3)
    check("concentrada custa cinco vezes a normal", concentrated["price"] == normal["price"] * 5)
    check("concentrada começa com três doses", concentrated["max_uses"] == 3 and concentrated["uses_left"] == 3)
    check("aprimorada cura 20 e custa três vezes a normal", improved["value"] == 20 and improved["price"] == normal["price"] * 3)
    check("regeneração tem reserva 10 e custa duas vezes a normal", regeneration["value"] == 10 and regeneration["price"] == normal["price"] * 2)

    print("\n[1b] Poção de Invisibilidade")
    invis = next((i for i in SHOP_TEMPLE if i["id"] == "pocao_invisibilidade"), None)
    check("é vendida por 60 moedas no templo e dura 6 rodadas",
          bool(invis and invis.get("price") == 60 and invis.get("value") == 6
               and invis.get("effect") == "invisibility"
               and invis.get("item_slot") == "bag"))
    check("tem ícone PNG associado",
          bool(invis and invis.get("icon") == "assets/itens/pocao_invisibilidade.png"))
    templos_ativos = [city for city, stock in CITY_SHOPS.items()
                      if isinstance(stock.get("templo"), list)]
    check("está à venda em todos os quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "pocao_invisibilidade"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["bag"] = [deepcopy(invis) if invis else {
        "id": "pocao_invisibilidade", "name": "Poção de Invisibilidade",
        "emoji": "🧪", "effect": "invisibility", "value": 6,
    }]
    await room.handle_use_item("p1", "pocao_invisibilidade")
    check("beber consome a poção e ativa a invisibilidade por 6 rodadas",
          not player["bag"] and player.get("invisivel_magico")
          and player.get("invisivel_magico_rodadas") == 6)
    check("beber usa a ação bônus",
          player.get("bonus_action_used") is True)
    for _ in range(6):
        await room._processar_buffs_magicos_turno(player)
    check("a invisibilidade termina após seis turnos",
          not player.get("invisivel_magico")
          and "invisivel_magico_rodadas" not in player)

    room, player = setup()
    player["bag"] = [deepcopy(invis) if invis else {
        "id": "pocao_invisibilidade", "name": "Poção de Invisibilidade",
        "emoji": "🧪", "effect": "invisibility", "value": 6,
    }]
    player["invisivel_magico"] = True
    player["invisivel_magico_rodadas"] = 2
    await room.handle_use_item("p1", "pocao_invisibilidade")
    check("beber durante a invisibilidade renova a duração para 6 rodadas",
          not player["bag"] and player.get("invisivel_magico")
          and player.get("invisivel_magico_rodadas") == 6)

    print("\n[1c] Poção de Velocidade")
    speed = next((i for i in SHOP_TEMPLE if i["id"] == "pocao_velocidade"), None)
    check("custa 120 e usa a fórmula 1d4+1",
          bool(speed and speed.get("price") == 120 and speed.get("value") == "1d4+1"
               and speed.get("effect") == "speed" and speed.get("item_slot") == "bag"))
    check("tem ícone PNG associado",
          bool(speed and speed.get("icon") == "assets/itens/pocao_velocidade.png"))
    check("está à venda em todos os quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "pocao_velocidade"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["bag"] = [deepcopy(speed) if speed else {
        "id": "pocao_velocidade", "name": "Poção de Velocidade",
        "emoji": "⚡", "effect": "speed", "value": "1d4+1",
    }]
    rolled = []
    # 1d4+1: o mock retorna 4, como se o d4 fosse 3 e o modificador fosse +1.
    room._rolar_dado = lambda expression: (rolled.append(expression) or 4)
    await room.handle_use_item("p1", "pocao_velocidade")
    check("beber consome o frasco e ativa Velocidade por 4 rodadas",
          not player["bag"] and player.get("velocidade_rodadas") == 4
          and player.get("velocidade_extra_usada") is False
          and rolled == ["1d4+1"])
    check("beber usa a ação bônus",
          player.get("bonus_action_used") is True)
    player["action_done"] = True
    check("Velocidade concede uma ação principal extra no turno",
          room._acao_bloqueada(player) is False
          and player.get("action_done") is False
          and player.get("velocidade_extra_usada") is True)
    await room._processar_buffs_magicos_turno(player)
    check("a ação extra renova no turno seguinte e a duração cai uma rodada",
          player.get("velocidade_rodadas") == 3
          and player.get("velocidade_extra_usada") is False)
    for _ in range(3):
        await room._processar_buffs_magicos_turno(player)
    check("o efeito e seus marcadores expiram ao fim da duração",
          "velocidade_rodadas" not in player
          and "velocidade_extra_usada" not in player
          and "velocidade_visual_id" not in player)

    print("\n[1c] Poção de Voo")
    flight = next((i for i in SHOP_TEMPLE if i["id"] == "pocao_voo"), None)
    check("custa 220 moedas e dura 10 rodadas",
          bool(flight and flight.get("price") == 220 and flight.get("value") == 10
               and flight.get("effect") == "flight_potion"
               and flight.get("item_slot") == "bag"))
    check("tem ícone PNG associado",
          bool(flight and flight.get("icon") == "assets/itens/pocao_voo.png"))
    check("está à venda em todos os quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "pocao_voo"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    room.tiles = [[FLOOR for _ in range(8)] for _ in range(8)]
    room.map_w = room.map_h = 8
    player["pos"] = [3, 3]
    player["bag"] = [deepcopy(flight) if flight else {
        "id": "pocao_voo", "name": "Poção de Voo",
        "emoji": "🪽", "effect": "flight_potion", "value": 10,
    }]
    eventos = []
    async def capture_broadcast(event):
        eventos.append(event)
    room.broadcast = capture_broadcast
    await room.handle_use_item("p1", "pocao_voo")
    check("beber consome o frasco, usa ação bônus e ativa voo até altura 10",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("voo") is True and player.get("altura") == 2
          and player.get("altura_max") == 10
          and player.get("voo_pocao_rodadas") == 10)
    check("reutiliza a animação de voo existente",
          [e.get("phase") for e in eventos if e.get("type") == "spell_animation"
           and e.get("spell_id") == "voo"] == ["start", "resolve"])
    for _ in range(9):
        await room._processar_buffs_magicos_turno(player)
    check("o voo permanece ativo durante as primeiras nove rodadas",
          player.get("voo") is True and player.get("voo_pocao_rodadas") == 1)
    player["altura"] = 8
    hp_antes = player["hp"]
    eventos = []
    await room._processar_buffs_magicos_turno(player)
    check("ao fim da 10ª rodada pousa com segurança e sem dano de queda",
          player.get("voo") is False and player.get("altura") == 0
          and "voo_pocao_rodadas" not in player and player["hp"] == hp_antes
          and not any(e.get("type") == "fall_result" for e in eventos))

    room, player = setup()
    room.tiles = [[FLOOR for _ in range(8)] for _ in range(8)]
    room.map_w = room.map_h = 8
    player["pos"] = [3, 3]
    player["voo_pocao_rodadas"] = 1
    player["altura"] = 6
    player["voo"] = True
    player["paralisado"] = True
    hp_antes = player["hp"]
    eventos = []
    room.broadcast = capture_broadcast
    async def dano_fixo(*args, **kwargs):
        return 4
    room._rolar_dano_mostrado = dano_fixo
    await room._processar_buffs_magicos_turno(player)
    check("se perder o controle durante a expiração, aplica a queda normal",
          player["voo"] is False and player.get("altura") == 0
          and player["hp"] == hp_antes - 4
          and any(e.get("type") == "fall_result"
                  and e.get("motivo") == "pocao_voo_expirou_sem_controle"
                  for e in eventos))

    room, player = setup()
    room.tiles = [["WALL" for _ in range(8)] for _ in range(8)]
    room.map_w = room.map_h = 8
    player["pos"] = [3, 3]
    player["voo_pocao_rodadas"] = 1
    player["altura"] = 6
    player["voo"] = True
    hp_antes = player["hp"]
    eventos = []
    room.broadcast = capture_broadcast
    room._rolar_dano_mostrado = dano_fixo
    await room._processar_buffs_magicos_turno(player)
    check("sem casa segura, aplica a queda normal ao expirar",
          player["voo"] is False and player.get("altura") == 0
          and player["hp"] == hp_antes - 4
          and any(e.get("type") == "fall_result"
                  and e.get("motivo") == "pocao_voo_sem_piso_seguro"
                  for e in eventos))

    print("\n[1d] Poção do Manto da Escuridão")
    mantle = next((i for i in SHOP_TEMPLE if i["id"] == "pocao_manto_escuridao"), None)
    check("custa 90 e usa a fórmula 1d4",
          bool(mantle and mantle.get("price") == 90 and mantle.get("value") == "1d4"
               and mantle.get("effect") == "darkness_mantle"
               and mantle.get("item_slot") == "bag"))
    check("tem ícone PNG associado",
          bool(mantle and mantle.get("icon") == "assets/itens/pocao_manto_escuridao.png"))
    check("está à venda em todos os quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "pocao_manto_escuridao"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["bag"] = [deepcopy(mantle) if mantle else {
        "id": "pocao_manto_escuridao", "name": "Poção do Manto da Escuridão",
        "emoji": "🌑", "effect": "darkness_mantle", "value": "1d4",
    }]
    rolled = []
    room._rolar_dado = lambda expression: (rolled.append(expression) or 3)
    events = []
    async def capture_broadcast(event):
        events.append(event)
    room.broadcast = capture_broadcast
    slot_checks = []
    room._slots_disponiveis = lambda *args: (slot_checks.append(args) or 0)
    room._cajado_arcano_area_lado = lambda *args: 8
    await room.handle_use_item("p1", "pocao_manto_escuridao")
    zone = next((z for z in room.zonas_especiais if z.get("tipo") == "escuridao"), None)
    check("beber consome o frasco e cria Manto móvel de raio 3 por 3 rodadas",
          not player["bag"] and zone is not None
          and zone.get("raio") == 3 and zone.get("duracao") == 3
          and zone.get("area_lado") is None
          and zone.get("seguir_caster") is True and zone.get("concede_visao") is True
          and rolled == ["1d4"])
    check("o herói recebe visão no escuro e gasta a ação bônus, sem consultar slot",
          player.get("visao_escuro") is True
          and player.get("visao_escuro_manto") is True
          and player.get("bonus_action_used") is True
          and not slot_checks)
    check("a animação existente do Manto é emitida",
          any(e.get("type") == "spell_animation" and e.get("spell_id") == "manto_escuridao"
              and e.get("phase") == "start" for e in events))
    for _ in range(2):
        await room._processar_zonas_turno_impl()
    check("o Manto permanece ativo até consumir as 3 rodadas",
          zone in room.zonas_especiais and zone.get("duracao") == 1
          and player.get("visao_escuro_manto") is True)
    await room._processar_zonas_turno_impl()
    check("ao expirar, remove a zona e restaura a visão anterior",
          not room.zonas_especiais and player.get("visao_escuro") is False
          and not player.get("visao_escuro_manto"))

    print("\n[1e] Poções de Proteção Elemental")
    elementos = {
        "fogo": "fogo", "gelo": "gelo", "eletricidade": "eletricidade",
        "acido": "acido", "agua": "agua", "sagrado": "sagrado",
    }
    pocoes_elementais = {
        elemento: next((i for i in SHOP_TEMPLE
                        if i["id"] == f"pocao_resistencia_{elemento}"), None)
        for elemento in elementos
    }
    check("há um frasco de 80 moedas para cada um dos seis elementos",
          all(item and item.get("price") == 80 and item.get("value") == "1d6+4"
              and item.get("effect") == "elemental_resistance_potion"
              and item.get("element") == elemento and item.get("item_slot") == "bag"
              for elemento, item in pocoes_elementais.items()))
    check("cada frasco tem ícone próprio associado",
          all(item and item.get("icon") == f"assets/itens/pocao_resistencia_{elemento}.png"
              for elemento, item in pocoes_elementais.items()))
    check("os seis ícones PNG existem no workspace",
          all(item and os.path.isfile(os.path.join(
              os.path.dirname(os.path.dirname(os.path.abspath(__file__))), item["icon"]))
              for item in pocoes_elementais.values()))
    check("os seis frascos estão disponíveis nos quatro templos",
          len(templos_ativos) == 4 and all(
              all(any(i["id"] == f"pocao_resistencia_{elemento}"
                      for i in _city_shop_items(city, "templo"))
                  for elemento in elementos)
              for city in templos_ativos))

    room, player = setup()
    fogo = deepcopy(pocoes_elementais["fogo"] or {
        "id": "pocao_resistencia_fogo", "effect": "elemental_resistance_potion",
        "element": "fogo", "value": "1d6+4", "item_slot": "bag",
    })
    acido = deepcopy(pocoes_elementais["acido"] or {
        "id": "pocao_resistencia_acido", "effect": "elemental_resistance_potion",
        "element": "acido", "value": "1d6+4", "item_slot": "bag",
    })
    player["bag"] = [fogo]
    room._rolar_dado = lambda expression: 8
    await room.handle_use_item("p1", fogo["id"])
    protecoes = player.get("protecao_pocoes_elementais", {})
    fogo_ativo = protecoes.get("fogo", {})
    check("beber fogo usa ação bônus e inicia 1d6+4 rodadas de proteção 10",
          not player["bag"] and player.get("bonus_action_used") is True
          and fogo_ativo.get("rodadas") == 8 and fogo_ativo.get("max") == 10
          and fogo_ativo.get("restante") == 10)
    dano = await room._absorver_energia(player, 6, "fire")
    player["bag"] = [acido]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", acido["id"])
    protecoes = player.get("protecao_pocoes_elementais", {})
    acido_ativo = protecoes.get("acido", {})
    check("cada poção absorve apenas o próprio elemento e tipos diferentes coexistem",
          dano == 0 and protecoes.get("fogo", {}).get("restante") == 4
          and acido_ativo.get("rodadas") == 8 and acido_ativo.get("restante") == 10
          and await room._absorver_energia(player, 5, "acid") == 0)

    await room._processar_buffs_magicos_turno(player)
    protecoes = player.get("protecao_pocoes_elementais", {})
    check("a cada turno renova 10 pontos por elemento e reduz uma rodada",
          protecoes.get("fogo", {}).get("restante") == 10
          and protecoes.get("fogo", {}).get("rodadas") == 7
          and protecoes.get("acido", {}).get("restante") == 10
          and protecoes.get("acido", {}).get("rodadas") == 7)

    player["bag"] = [deepcopy(pocoes_elementais["fogo"] or fogo)]
    player["bonus_action_used"] = False
    await room._absorver_energia(player, 6, "fogo")
    player["bag"] = [deepcopy(pocoes_elementais["fogo"] or fogo)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", fogo["id"])
    protecoes = player.get("protecao_pocoes_elementais", {})
    check("repetir fogo renova a duração sem restaurar nem dobrar o limite atual",
          protecoes.get("fogo", {}).get("rodadas") == 8
          and protecoes.get("fogo", {}).get("restante") == 4
          and protecoes.get("fogo", {}).get("max") == 10)

    check("as proteções permanecem ativas antes de expirar",
          bool(player.get("protecao_pocoes_elementais"))
          and player.get("protecao_pocoes_elementais", {}).get("fogo", {}).get("rodadas") == 8)
    for _ in range(7):
        await room._processar_buffs_magicos_turno(player)
    check("a proteção ainda existe até o último turno", bool(player.get("protecao_pocoes_elementais")))
    await room._processar_buffs_magicos_turno(player)
    check("as proteções elementais expiram após a duração e limpam o estado",
          not player.get("protecao_pocoes_elementais"))

    room, player = setup()
    player["protecao_rodadas"] = 4
    player["protecao_max"] = 10
    player["protecao_restante"] = 4
    player["protecao_tipos"] = ["fogo", "gelo", "eletricidade", "acido", "agua", "sagrado"]
    player["protecao_visual_id"] = "protecao_magia_existente"
    player["bag"] = [deepcopy(pocoes_elementais["fogo"] or fogo)]
    room._rolar_dado = lambda expression: 8
    await room.handle_use_item("p1", fogo["id"])
    protecao_fogo = player.get("protecao_pocoes_elementais", {}).get("fogo", {})
    dano = await room._absorver_energia(player, 7, "fogo")
    check("a poção de fogo compartilha os 10 pontos restantes com a magia ativa",
          protecao_fogo.get("restante") == 0
          and player.get("protecao_restante") == 0 and dano == 3)

    room, player = setup()
    player["bag"] = [deepcopy(pocoes_elementais["fogo"] or fogo)]
    room._rolar_dado = lambda expression: 8
    await room.handle_use_item("p1", "pocao_resistencia_fogo")
    await room._absorver_energia(player, 6, "fogo")
    await room._executar_protecao_energia(player, {
        "duracao": "1d6+1", "reducao_por_rodada": 10,
        "tipos": ["fogo", "gelo", "eletricidade", "acido", "agua", "sagrado"],
    }, 0)
    fogo_ativo = player["protecao_pocoes_elementais"]["fogo"]
    dano = await room._absorver_energia(player, 7, "fogo")
    check("a magia não recarrega o limite já gasto pela poção do mesmo elemento",
          fogo_ativo.get("restante") == 0 and player.get("protecao_restante") == 0 and dano == 3)

    print("\n[1f] Poção de Barreira Arcana")
    pocao_barreira = next((i for i in SHOP_TEMPLE if i["id"] == "pocao_barreira_arcana"), None)
    check("custa 110 moedas, tem duração 1d6+2 e ícone próprio",
          bool(pocao_barreira and pocao_barreira.get("price") == 110
               and pocao_barreira.get("value") == "1d6+2"
               and pocao_barreira.get("icon") == "assets/itens/pocao_barreira_arcana.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/pocao_barreira_arcana.png"))))
    check("está à venda nos quatro templos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "pocao_barreira_arcana"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["bag"] = [deepcopy(pocao_barreira or {
        "id": "pocao_barreira_arcana", "effect": "arcane_barrier_potion",
        "value": "1d6+2", "item_slot": "bag",
    })]
    room._rolar_dado = lambda expression: 6
    await room.handle_use_item("p1", "pocao_barreira_arcana")
    check("beber usa ação bônus e dá redução 5 por oito rodadas fixas",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("barreira_arcana_rodadas") == 8
          and player.get("barreira_arcana_reducao") == 5)
    hp_antes = player["hp"]
    await room._aplicar_dano_alvo(player, 8, "fisico", _protetor_bypass=True)
    check("reduz em 5 também um golpe físico comum",
          player["hp"] == hp_antes - 3)

    player["protecao_pocoes_elementais"] = {
        "fogo": {"rodadas": 5, "max": 10, "restante": 10}}
    hp_antes = player["hp"]
    await room._aplicar_dano_alvo(player, 16, "fogo", _protetor_bypass=True)
    check("barreira arcana e poção elemental coexistem e reduzem o mesmo golpe",
          player["hp"] == hp_antes - 1
          and player["protecao_pocoes_elementais"]["fogo"]["restante"] == 0)
    for _ in range(8):
        await room._processar_buffs_magicos_turno(player)
    check("a barreira da poção expira ao fim das oito rodadas",
          player.get("barreira_arcana_rodadas", 0) <= 0)

    print("\n[1g] Gole do Gigante")
    gole = next((i for i in SHOP_TEMPLE if i["id"] == "gole_do_gigante"), None)
    check("custa 150, concede 1d4+1 Força por 1d6+4 e tem ícone PNG",
          bool(gole and gole.get("price") == 150
               and gole.get("effect") == "strength_potion"
               and gole.get("value") == "1d6+4"
               and gole.get("strength_bonus") == "1d4+1"
               and gole.get("icon") == "assets/itens/gole_do_gigante.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/gole_do_gigante.png"))))
    check("está à venda nos quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "gole_do_gigante"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    base_forca = player["str_"]
    base_ataque = player["atk_bonus"]
    base_ataque_ficha = player.get("base_atk_bonus")
    gole_item = deepcopy(gole or {
        "id": "gole_do_gigante", "effect": "strength_potion",
        "value": "1d6+4", "strength_bonus": "1d4+1", "item_slot": "bag",
    })
    player["bag"] = [deepcopy(gole_item)]
    rolagens = []
    def rolar_gole(expressao):
        rolagens.append(expressao)
        return 4 if expressao == "1d4+1" else 8
    room._rolar_dado = rolar_gole
    await room.handle_use_item("p1", "gole_do_gigante")
    check("beber é ação bônus, consome o item, rola Força +4 e duração de 8 turnos",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("str_") == base_forca + 4
          and player.get("gole_gigante_rodadas") == 8
          and player.get("gole_gigante_bonus") == 4
          and rolagens == ["1d4+1", "1d6+4"])
    bonus_mod = mod(base_forca + 4) - mod(base_forca)
    check("a Força temporária atualiza acerto, dano e testes pelo modificador normal",
          _hero_attack_bonus_with_weapon(player) == base_ataque + bonus_mod
          and mod(player["str_"]) == mod(base_forca + 4))

    player["bag"] = [deepcopy(gole_item)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "gole_do_gigante")
    check("beber novamente renova a duração e mantém o bônus sem acumular",
          player.get("str_") == base_forca + 4
          and player.get("gole_gigante_bonus") == 4
          and player.get("gole_gigante_rodadas") == 8
          and rolagens == ["1d4+1", "1d6+4", "1d6+4"])
    for _ in range(7):
        await room._processar_buffs_magicos_turno(player)
    check("o bônus permanece até a última rodada",
          player.get("str_") == base_forca + 4
          and player.get("gole_gigante_rodadas") == 1)
    await room._processar_buffs_magicos_turno(player)
    check("ao expirar, restaura Força e bônus de ataque originais",
          player.get("str_") == base_forca
          and player.get("atk_bonus") == base_ataque
          and player.get("base_atk_bonus") == base_ataque_ficha
          and "gole_gigante_rodadas" not in player
          and "gole_gigante_bonus" not in player)

    room, player = setup()
    fogo = next(i for i in SHOP_TEMPLE if i["id"] == "pocao_resistencia_fogo")
    player["bag"] = [deepcopy(gole_item), deepcopy(fogo)]
    room._rolar_dado = lambda expression: 8 if expression == "1d6+4" else 4
    await room.handle_use_item("p1", "gole_do_gigante")
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", fogo["id"])
    check("pode coexistir com poção de resistência elemental",
          player.get("gole_gigante_rodadas") == 8
          and player.get("protecao_pocoes_elementais", {}).get("fogo", {}).get("rodadas") == 8)

    print("\n[1h] Bote da Serpente")
    bote = next((i for i in SHOP_TEMPLE if i["id"] == "bote_da_serpente"), None)
    check("custa 150, concede 1d4+1 Destreza por 1d6+4 e tem ícone PNG",
          bool(bote and bote.get("price") == 150
               and bote.get("effect") == "dexterity_potion"
               and bote.get("value") == "1d6+4"
               and bote.get("dexterity_bonus") == "1d4+1"
               and bote.get("icon") == "assets/itens/bote_da_serpente.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/bote_da_serpente.png"))))
    check("está à venda nos quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "bote_da_serpente"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room = GameRoom("POTION")
    async def noop(*args, **kwargs):
        pass
    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    player = make_player("p1", "Teste", "rogue", 0)
    room.players["p1"] = player
    dex_item = deepcopy(bote or {
        "id": "bote_da_serpente", "effect": "dexterity_potion",
        "value": "1d6+4", "dexterity_bonus": "1d4+1", "item_slot": "bag",
    })
    player["bag"] = [deepcopy(dex_item)]
    base_dex = player["dex"]
    base_ac = player["ac"]
    base_ac_ficha = player["ac_base"]
    base_ref = player["ref_"]
    base_ataque = player["atk_bonus"]
    base_ataque_ficha = player.get("base_atk_bonus")
    base_iniciativa = room.initiative_value(player)
    base_visao = room._get_raio_visao(player)
    weapon_finesse = {"id": "dagger", "finesse": True, "stat": "dex"}
    rolagens = []
    def rolar_bote(expressao):
        rolagens.append(expressao)
        return 4 if expressao == "1d4+1" else 8
    room._rolar_dado = rolar_bote
    await room.handle_use_item("p1", "bote_da_serpente")
    bonus_mod = mod(base_dex + 4) - mod(base_dex)
    check("beber é ação bônus e aumenta Destreza +4 por oito rodadas",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("dex") == base_dex + 4
          and player.get("bote_serpente_bonus") == 4
          and player.get("bote_serpente_rodadas") == 8
          and rolagens == ["1d4+1", "1d6+4"])
    check("atualiza CA, Reflexos e ataques que usam Destreza",
          player.get("ac") == base_ac + bonus_mod
          and player.get("ac_base") == base_ac_ficha + bonus_mod
          and player.get("ref_") == base_ref + bonus_mod
          and player.get("atk_bonus") == base_ataque + bonus_mod
          and _hero_attack_bonus_with_weapon(player, weapon_finesse)
              == base_ataque + bonus_mod)
    check("atualiza dano de arma finesse, iniciativa, visão e testes de Destreza",
          room._bonus_atributo_dano_arma(player, weapon_finesse) == mod(base_dex + 4)
          and room.initiative_value(player) == base_iniciativa + 4
          and room._get_raio_visao(player) >= base_visao
          and mod(player["dex"]) == mod(base_dex + 4))

    player["bag"] = [deepcopy(dex_item)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "bote_da_serpente")
    check("repetir a poção renova duração sem rerrolar nem acumular Destreza",
          player.get("dex") == base_dex + 4
          and player.get("bote_serpente_bonus") == 4
          and player.get("bote_serpente_rodadas") == 8
          and rolagens == ["1d4+1", "1d6+4", "1d6+4"])
    for _ in range(8):
        await room._processar_buffs_magicos_turno(player)
    check("ao expirar, restaura Destreza e todos os bônus derivados",
          player.get("dex") == base_dex
          and player.get("ac") == base_ac
          and player.get("ac_base") == base_ac_ficha
          and player.get("ref_") == base_ref
          and player.get("atk_bonus") == base_ataque
          and player.get("base_atk_bonus") == base_ataque_ficha
          and "bote_serpente_rodadas" not in player
          and "bote_serpente_bonus" not in player)

    room = GameRoom("POTION")
    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    player = make_player("p1", "Teste", "rogue", 0)
    room.players["p1"] = player
    player["bag"] = [deepcopy(dex_item), potion("gole_do_gigante"),
                     potion("pocao_resistencia_fogo")]
    room._rolar_dado = lambda expression: 8 if expression == "1d6+4" else 4
    await room.handle_use_item("p1", "bote_da_serpente")
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "gole_do_gigante")
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "pocao_resistencia_fogo")
    check("pode coexistir com o Gole do Gigante e proteção elemental",
          player.get("bote_serpente_rodadas") == 8
          and player.get("gole_gigante_rodadas") == 8
          and player.get("protecao_pocoes_elementais", {}).get("fogo", {}).get("rodadas") == 8)

    print("\n[1i] Elixir do Cavalo de Ferro")
    elixir = next((i for i in SHOP_TEMPLE if i["id"] == "elixir_cavalo_ferro"), None)
    check("custa 180, aumenta Constituição por 1d6+4 e tem ícone PNG",
          bool(elixir and elixir.get("price") == 180
               and elixir.get("effect") == "constitution_potion"
               and elixir.get("value") == "1d6+4"
               and elixir.get("constitution_bonus") == "1d4+1"
               and elixir.get("icon") == "assets/itens/elixir_cavalo_ferro.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/elixir_cavalo_ferro.png"))))
    check("está à venda nos quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "elixir_cavalo_ferro"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["level"] = 3
    elixir_item = deepcopy(elixir) if elixir else {
        "id": "elixir_cavalo_ferro", "effect": "constitution_potion",
        "value": "1d6+4", "constitution_bonus": "1d4+1", "item_slot": "bag",
    }
    base_con = player["con_"]
    base_fort = player["fort"]
    base_max_hp = player["max_hp"]
    base_hp = player["hp"] = base_max_hp
    player["bag"] = [deepcopy(elixir_item)]
    rolagens = []
    def rolar_elixir(expressao):
        rolagens.append(expressao)
        return 4 if expressao == "1d4+1" else 8
    room._rolar_dado = rolar_elixir
    await room.handle_use_item("p1", "elixir_cavalo_ferro")
    dm = get_bonus_constituicao(base_con + 4) - get_bonus_constituicao(base_con)
    check("beber usa ação bônus e aumenta CON, Fortitude e PV máximos pelo nível",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("con_") == base_con + 4
          and player.get("elixir_cavalo_ferro_bonus") == 4
          and player.get("elixir_cavalo_ferro_rodadas") == 8
          and player.get("fort") == base_fort + dm
          and player.get("max_hp") == base_max_hp + dm * 3
          and player.get("hp") == min(base_max_hp + dm * 3, base_hp + dm * 3)
          and rolagens == ["1d4+1", "1d6+4"])

    player["bag"] = [deepcopy(elixir_item)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "elixir_cavalo_ferro")
    check("repetir renova duração sem rerrolar nem acumular CON",
          player.get("con_") == base_con + 4
          and player.get("elixir_cavalo_ferro_bonus") == 4
          and player.get("elixir_cavalo_ferro_rodadas") == 8
          and rolagens == ["1d4+1", "1d6+4", "1d6+4"])
    for _ in range(8):
        await room._processar_buffs_magicos_turno(player)
    check("ao expirar, restaura CON e Fortitude e limita PV ao novo máximo",
          player.get("con_") == base_con
          and player.get("fort") == base_fort
          and player.get("max_hp") == base_max_hp
          and player.get("hp") == base_max_hp
          and "elixir_cavalo_ferro_rodadas" not in player
          and "elixir_cavalo_ferro_bonus" not in player)

    room, player = setup()
    base_con = player["con_"] = 24
    base_fort = player["fort"]
    player["max_hp"] = player["hp"] = 20
    base_max_hp = player["max_hp"]
    player["bag"] = [deepcopy(elixir_item)]
    room._rolar_dado = lambda expression: 8 if expression == "1d6+4" else 4
    await room.handle_use_item("p1", "elixir_cavalo_ferro")
    check("mantém o CON bruto mesmo quando o bônus de Fortitude/PV já chegou ao teto",
          player.get("con_") == 28 and player.get("elixir_cavalo_ferro_bonus") == 4
          and player.get("fort") == base_fort and player.get("max_hp") == base_max_hp)
    for _ in range(8):
        await room._processar_buffs_magicos_turno(player)
    check("o término no teto restaura o valor original de CON, Fortitude e PV máximos",
          player.get("con_") == base_con
          and player.get("fort") == base_fort
          and player.get("max_hp") == base_max_hp
          and "elixir_cavalo_ferro_rodadas" not in player)

    print("\n[1j] Sabedoria Líquida")
    sabedoria = next((i for i in SHOP_TEMPLE if i["id"] == "sabedoria_liquida"), None)
    check("custa 200, aumenta INT por 1d6+4 e tem ícone PNG",
          bool(sabedoria and sabedoria.get("price") == 200
               and sabedoria.get("effect") == "intelligence_potion"
               and sabedoria.get("value") == "1d6+4"
               and sabedoria.get("intelligence_bonus") == "1d4+1"
               and sabedoria.get("icon") == "assets/itens/sabedoria_liquida.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/sabedoria_liquida.png"))))
    check("está à venda nos quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "sabedoria_liquida"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player = make_player("p1", "Teste", "cleric", 0)
    room.players["p1"] = player
    player["level"] = 4
    player["int_"] = 14
    base_int = player["int_"]
    base_will = player["will"]
    base_dc = room._dif_magia(player, {"circulo": "primeiro"})
    base_initiative = room.initiative_value(player)
    base_vision = room._get_raio_visao(player)
    base_reviver_slots = room._reviver_slots_max(player)
    sabedoria_item = deepcopy(sabedoria) if sabedoria else {
        "id": "sabedoria_liquida", "effect": "intelligence_potion",
        "value": "1d6+4", "intelligence_bonus": "1d4+1", "item_slot": "bag",
    }
    player["bag"] = [deepcopy(sabedoria_item)]
    target = make_player("p2", "Aliado", "warrior", 1)
    target["hp"], target["max_hp"] = 10, 100
    room.players["p2"] = target
    room._no_raio = lambda *args, **kwargs: True
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    player["action_done"] = False
    with patch("server.random.randint", return_value=4):
        await room.handle_cura("p1", {"target_id": "p2", "num_dados": 1})
    cura_base = target["hp"] - 10
    target["hp"] = 10
    player["action_done"] = False
    rolagens = []
    def rolar_sabedoria(expressao):
        rolagens.append(expressao)
        return 4 if expressao == "1d4+1" else 8
    room._rolar_dado = rolar_sabedoria
    await room.handle_use_item("p1", "sabedoria_liquida")
    dm_int = mod(base_int + 4) - mod(base_int)
    check("beber usa ação bônus e atualiza INT, Vontade, CD, iniciativa, visão e Reviver",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("int_") == base_int + 4
          and player.get("will") == base_will + dm_int
          and room._dif_magia(player, {"circulo": "primeiro"}) == base_dc + dm_int
          and room.initiative_value(player) == base_initiative + dm_int
          and room._get_raio_visao(player) >= base_vision + 1
          and room._reviver_slots_max(player) == base_reviver_slots + dm_int
          and rolagens == ["1d4+1", "1d6+4"])

    player["action_done"] = False
    with patch("server.random.randint", return_value=4):
        await room.handle_cura("p1", {"target_id": "p2", "num_dados": 1})
    check("aumenta também o bônus de INT adicionado às curas do clérigo",
          cura_base == 4 + mod(base_int) and target["hp"] - 10 == 4 + mod(base_int + 4))

    player["bag"] = [deepcopy(sabedoria_item)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "sabedoria_liquida")
    check("repetir renova duração sem rerrolar nem acumular Inteligência",
          player.get("int_") == base_int + 4
          and player.get("sabedoria_liquida_bonus") == 4
          and player.get("sabedoria_liquida_rodadas") == 8
          and rolagens == ["1d4+1", "1d6+4", "1d6+4"])
    for _ in range(8):
        await room._processar_buffs_magicos_turno(player)
    check("ao expirar, restaura INT, Vontade, CD, iniciativa, visão e slots de controle",
          player.get("int_") == base_int
          and player.get("will") == base_will
          and room._dif_magia(player, {"circulo": "primeiro"}) == base_dc
          and room.initiative_value(player) == base_initiative
          and room._get_raio_visao(player) == base_vision
          and room._reviver_slots_max(player) == base_reviver_slots
          and "sabedoria_liquida_rodadas" not in player
          and "sabedoria_liquida_bonus" not in player)

    print("\n[2] Uso da concentrada")
    room, player = setup()
    player["bag"] = [concentrated]
    for expected_uses in (2, 1):
        player["hp"] = 1
        player["bonus_action_used"] = False
        await room.handle_use_item("p1", "health_potion_concentrated")
        check(f"cura 10 HP e mantém a dose {expected_uses}",
              player["hp"] == 11 and player["bag"] == [concentrated]
              and concentrated["uses_left"] == expected_uses)

    player["hp"] = 1
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "health_potion_concentrated")
    check("terceira dose cura e remove a poção", player["hp"] == 11 and not player["bag"])

    print("\n[3] Regeneração da poção")
    room, player = setup()
    player["bag"] = [regeneration]
    player["hp"] = player["max_hp"]
    await room.handle_use_item("p1", "regeneration_potion")
    check("ativa a reserva e consome o frasco", player.get("potion_regen_pool") == 10 and not player["bag"])
    await room._processar_regeneracao_pocao_turno(player)
    check("HP cheio preserva toda a reserva", player.get("potion_regen_pool") == 10)
    player["hp"] = player["max_hp"] - 1
    await room._processar_regeneracao_pocao_turno(player)
    check("cura 1 e reduz a reserva só quando necessário", player["hp"] == player["max_hp"] and player.get("potion_regen_pool") == 9)

    print("\n[1k] Elixir da Mira do Falcão")
    mira = next((i for i in SHOP_TEMPLE if i["id"] == "mira_do_falcao"), None)
    check("custa 120, dá +2 a arcos e arremessos por 1d4+1 rodadas e tem PNG",
          bool(mira and mira.get("price") == 120
               and mira.get("effect") == "archery_potion"
               and mira.get("value") == "1d4+1"
               and mira.get("attack_bonus") == 2
               and mira.get("icon") == "assets/itens/mira_do_falcao.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/mira_do_falcao.png"))))
    templos_ativos = [city for city, stock in CITY_SHOPS.items()
                      if isinstance(stock.get("templo"), list)]
    check("está à venda em todos os quatro templos ativos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "mira_do_falcao"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))

    room, player = setup()
    player["bag"] = [deepcopy(mira or {
        "id": "mira_do_falcao", "effect": "archery_potion",
        "value": "1d4+1", "attack_bonus": 2, "item_slot": "bag",
    })]
    room._rolar_dado = lambda expression: 3
    await room.handle_use_item("p1", "mira_do_falcao")
    check("beber consome ação bônus, remove o frasco e ativa três rodadas",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("mira_falcao_rodadas") == 3)
    player["bag"] = [deepcopy(mira)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "mira_do_falcao")
    check("beber outra renova a duração sem criar bônus cumulativo",
          not player["bag"] and player.get("mira_falcao_rodadas") == 3
          and "mira_falcao_bonus" not in player)

    alvo = {"id": "m1", "type": "goblin", "name": "Alvo", "hp": 30,
            "ac": 12, "pos": [2, 0]}
    arco = {"id": "arco_curto", "range": 6, "die": "1d6", "stat": "dex"}
    player["weapon"] = arco
    player.pop("mira_falcao_rodadas", None)
    sem_pocao = room._modificadores_ataque_heroi(
        player, alvo, alvo["pos"], arco["range"], previa=True)["eff_atk"]
    player["mira_falcao_rodadas"] = 3
    com_pocao = room._modificadores_ataque_heroi(
        player, alvo, alvo["pos"], arco["range"], previa=True)["eff_atk"]
    check("o bônus também aparece na prévia e no ataque de arco (+2)",
          com_pocao == sem_pocao + 2)
    espada = {"id": "shortsword", "die": "1d6", "stat": "str_"}
    player["weapon"] = espada
    corpo_a_corpo = room._modificadores_ataque_heroi(
        player, alvo, alvo["pos"], None, previa=True)["eff_atk"]
    check("não concede bônus a ataques corpo a corpo",
          corpo_a_corpo == _hero_attack_bonus_with_weapon(player, espada)
          + room._modificador_sobrevivencia(player)
          + room._pen(player, "ataque") + room._mod_magia(player, "ataque")
          + int(espada.get("atk_bonus", 0) or 0)
          + room._cancao_bonus(player, "bonus_acerto")
          + room._maldicao_mod(player, "ataque"))

    room, player = setup()
    player["mira_falcao_rodadas"] = 3
    machadinha = {"id": "machadinha_ana", "name": "Machadinha Anã",
                  "die": "1d6", "throw_range": 3,
                  "granted_ability": "arremesso_bruto",
                  "item_slot": "off_hand"}
    player["gear"]["off_hand"] = machadinha
    room._alcance_com_altura = lambda *args, **kwargs: True
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room._free_tile_near = lambda *args, **kwargs: (1, 1)
    room._spawn_chest = lambda *args, **kwargs: None
    alvo = {"id": "m2", "type": "goblin", "name": "Alvo", "hp": 30,
            "pos": [1, 0]}
    base_arremesso = _hero_attack_bonus_with_weapon(player, machadinha)
    alvo["ac"] = base_arremesso + 14
    room.monsters[alvo["id"]] = alvo
    with patch("server.random.randint", return_value=13), patch("server.roll_dice", return_value=4):
        await room._executar_arremesso("p1", alvo["id"], "off_hand")
    check("o arremesso acerta graças ao +2 e o bônus não altera o dano",
          alvo["hp"] == 30 - (4 + mod(player["str_"]))
          and player.get("gear", {}).get("off_hand") is None)

    player["mira_falcao_rodadas"] = 1
    await room._processar_buffs_magicos_turno(player)
    check("expira após a última rodada e remove o estado do herói",
          player.get("mira_falcao_rodadas", 0) == 0
          and "mira_falcao_rodadas" not in player)

    print("\n[1l] Essência do Vento Favorável")
    essencia = next((i for i in SHOP_TEMPLE
                     if i["id"] == "essencia_vento_favoravel"), None)
    check("custa 100, dura 1d6+2, tem ícone e aumenta alcance em 2",
          bool(essencia and essencia.get("price") == 100
               and essencia.get("effect") == "ranged_range_potion"
               and essencia.get("value") == "1d6+2"
               and essencia.get("range_bonus") == 2
               and essencia.get("icon") == "assets/itens/essencia_vento_favoravel.png"
               and os.path.isfile(os.path.join(
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets/itens/essencia_vento_favoravel.png"))))
    check("está à venda nos quatro templos",
          len(templos_ativos) == 4 and all(
              any(i["id"] == "essencia_vento_favoravel"
                  for i in _city_shop_items(city, "templo"))
              for city in templos_ativos))
    check("efeito concede +2 aos três tipos de alcance sem afetar arma corpo a corpo",
          room._bonus_alcance_arma_distancia(player) == 0
          and room._bonus_alcance_arremesso(player) == 0)
    player["weapon"] = {"id": "arco_curto", "range": 6}
    player["essencia_vento_rodadas"] = 2
    check("bônus se aplica a armas com projéteis e a arremessos, mas não a corpo a corpo",
          room._bonus_alcance_arma_distancia(player) == 2
          and room._bonus_alcance_arremesso(player) == 2)
    player["weapon"] = {"id": "shortsword", "range": None}
    check("não aumenta alcance de arma corpo a corpo",
          room._bonus_alcance_arma_distancia(player) == 0)

    room, player = setup()
    player["bag"] = [deepcopy(essencia or {
        "id": "essencia_vento_favoravel", "effect": "ranged_range_potion",
        "value": "1d6+2", "item_slot": "bag"})]
    room._rolar_dado = lambda expression: 6
    await room.handle_use_item("p1", "essencia_vento_favoravel")
    check("beber usa ação bônus e ativa seis rodadas sem consumir outros recursos",
          not player["bag"] and player.get("bonus_action_used") is True
          and player.get("essencia_vento_rodadas") == 6)
    player["bag"] = [deepcopy(essencia)]
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "essencia_vento_favoravel")
    check("beber novamente renova a duração sem acumular alcance",
          player.get("essencia_vento_rodadas") == 6
          and room._bonus_alcance_arremesso(player) == 2)
    player["essencia_vento_rodadas"] = 1
    await room._processar_buffs_magicos_turno(player)
    check("expira ao fim da duração e remove o bônus de alcance",
          "essencia_vento_rodadas" not in player
          and room._bonus_alcance_arremesso(player) == 0)

    room, player = setup()
    player["pos"] = [1, 1]
    player["essencia_vento_rodadas"] = 3
    arco = {"id": "arco_curto", "range": 6}
    player["weapon"] = arco
    alvo_longe = {"id": "m3", "name": "Alvo distante", "pos": [8, 1],
                  "hp": 20, "ac": 12, "alive": True}
    check("servidor permite ataque de arco a duas casas além do alcance-base",
          room._alvo_no_alcance_arma(player, alvo_longe))

    room, player = setup()
    player["pos"] = [1, 1]
    player["essencia_vento_rodadas"] = 3
    player["bag"] = [deepcopy(ARREMESSAVEIS["cola_alquimica"])]
    alvo = {"id": "m4", "name": "Alvo", "pos": [7, 1], "hp": 20,
            "max_hp": 20, "ac": 12, "alive": True}
    room.monsters[alvo["id"]] = alvo
    alcances = []
    room._alcance_com_altura = lambda _p, _pos, alcance, **_kwargs: alcances.append(alcance) or alcance >= 6
    room._tem_linha_de_visao = lambda *_args, **_kwargs: True
    with patch("server.random.randint", return_value=1):
        await room._throw_item_alvo_impl(
            player, ARREMESSAVEIS["cola_alquimica"], player["bag"][0], alvo["id"])
    check("servidor aplica +2 ao alcance de item arremessável contra alvo único",
          alcances == [6] and not player["bag"] and player.get("action_done") is True)

    room, player = setup()
    player["pos"] = [1, 1]
    player["essencia_vento_rodadas"] = 3
    machadinha = {"id": "machadinha_ana", "name": "Machadinha Anã",
                  "throw_range": 3, "die": "1d6", "item_slot": "off_hand"}
    player["gear"]["off_hand"] = machadinha
    alvo = {"id": "m5", "name": "Alvo", "pos": [6, 1], "hp": 20,
            "max_hp": 20, "ac": 99, "alive": True}
    room.monsters[alvo["id"]] = alvo
    alcances = []
    room._alcance_com_altura = lambda _p, _pos, alcance, **_kwargs: alcances.append(alcance) or alcance >= 5
    room._tem_linha_de_visao = lambda *_args, **_kwargs: True
    room._free_tile_near = lambda *_args, **_kwargs: (5, 1)
    room._spawn_chest = lambda *_args, **_kwargs: None
    with patch("server.random.randint", return_value=10):
        await room._executar_arremesso("p1", alvo["id"], "off_hand")
    check("servidor aplica +2 ao alcance de armas arremessadas",
          alcances == [5] and player["gear"].get("off_hand") is None)

    room, player = setup()
    player["pos"] = [1, 1]
    player["essencia_vento_rodadas"] = 3
    room.tiles = [[FLOOR] * 9 for _ in range(9)]
    room.map_w = room.map_h = 9
    item_area = deepcopy(ARREMESSAVEIS["frasco_oleo"])
    player["bag"] = [item_area]
    room._tem_linha_de_visao = lambda *_args, **_kwargs: True
    await room._throw_item_area_impl(
        player, ARREMESSAVEIS["frasco_oleo"], item_area, 7, 1)
    check("servidor permite arremesso de área a duas casas além do alcance-base",
          not player["bag"] and player.get("action_done") is True)

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    return FAIL

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
