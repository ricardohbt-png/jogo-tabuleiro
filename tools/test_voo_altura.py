"""Verifica a primeira regra de combate vertical do Voo."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


async def test_alterar_altura_manual():
    room = server.GameRoom("FLIGHT_ALTITUDE_ACTION_TEST")
    room.master_pid = "master"
    room.master_manual_mid = "m1"
    room.push_state = lambda: asyncio.sleep(0)
    room.send_to = lambda *args, **kwargs: asyncio.sleep(0)
    room.monsters["m1"] = {
        "id": "m1", "name": "Elemental de Ar", "hp": 10,
        "voo": True, "altura": 2, "altura_max": 3,
        "pode_alterar_altura": True, "custo_mov_altura": 2,
        "master_moves_left": 3, "_water_moves_left": 3,
    }

    await room.handle_alterar_altura("master", 1, "m1")
    m = room.monsters["m1"]
    assert m["altura"] == 3
    assert m["master_moves_left"] == 1
    assert m["_water_moves_left"] == 1
    assert m["_master_touched"] is True

    # O limite superior não consome movimento.
    await room.handle_alterar_altura("master", 1, "m1")
    assert m["altura"] == 3
    assert m["master_moves_left"] == 1

    # Com dois pontos devolvidos ao orçamento, a descida funciona.
    m["master_moves_left"] = 2
    m["_water_moves_left"] = 2
    await room.handle_alterar_altura("master", -1, "m1")
    assert m["altura"] == 2
    assert m["master_moves_left"] == 0


def test_voo_obstaculos():
    room = server.GameRoom("FLIGHT_OBSTACLE_TEST")
    room.map_w = room.map_h = 5
    room.tiles = [[server.FLOOR for _ in range(room.map_w)] for _ in range(room.map_h)]
    room.tiles[1][2] = server.WALL
    room._decor_block_tiles = {(3, 1)}
    m = {"id": "m1", "hp": 10, "pos": [1, 1], "size": [1, 1],
         "voo": True, "altura": 2, "ignora_obstaculos_voo": False}

    # Voo, por si só, não atravessa obstáculos: a configuração é opt-in.
    assert not room._monster_can_occupy(m, 2, 1)
    assert not room._monster_can_occupy(m, 3, 1)

    m["ignora_obstaculos_voo"] = True
    assert room._monster_can_occupy(m, 2, 1)
    assert room._monster_can_occupy(m, 3, 1)
    # A borda do mapa e criaturas continuam bloqueando o pouso.
    assert not room._monster_can_occupy(m, -1, 1)
    room.monsters["other"] = {"id": "other", "hp": 10, "pos": [3, 1], "size": [1, 1]}
    assert not room._monster_can_occupy(m, 3, 1)


def test_voo_linha_de_visao():
    room = server.GameRoom("FLIGHT_LOS_TEST")
    room.map_w = 5
    room.map_h = 3
    room.tiles = [[server.FLOOR for _ in range(room.map_w)] for _ in range(room.map_h)]
    room.tiles[1][2] = server.WALL
    room._decor_block_tiles = set()
    room._decor_tall_tiles = set()
    room._mat_solid_tiles = set()
    room._mat_oclui_tiles = set()
    room.players["p1"] = {"id": "p1", "pos": [1, 1], "alive": True,
                           "voo": True, "altura": 0,
                           "ignora_obstaculos_voo": True}

    assert not room._tem_linha_de_visao([1, 1], [3, 1])
    room.players["p1"]["altura"] = 2
    assert room._tem_linha_de_visao([1, 1], [3, 1])

    room.tiles[1][2] = server.FLOOR
    room._decor_block_tiles = {(2, 1)}
    assert room._tem_linha_de_visao([1, 1], [3, 1])
    room._decor_tall_tiles = {(2, 1)}
    assert not room._tem_linha_de_visao([1, 1], [3, 1])


def test_voo_alcance_vertical_compartilhado():
    room = server.GameRoom("FLIGHT_SHARED_RANGE_TEST")
    caster = {"id": "p1", "pos": [1, 1], "altura": 0}
    alvo = {"id": "m1", "pos": [5, 1], "altura": 2}

    # A mesma regra usada por magias, arremessos e habilidades: altura 2
    # consome 1 quadrado do alcance horizontal.
    assert room._alcance_com_altura(caster, alvo["pos"], 5, destino=alvo)
    assert not room._alcance_com_altura(caster, alvo["pos"], 4, destino=alvo)

    caster["altura"] = 6
    assert not room._alcance_com_altura(caster, [2, 1], 3, altura_destino=0)
    assert room._alcance_com_altura(caster, [2, 1], 4, altura_destino=0)


def test_ataques_de_monstro_respeitam_altura():
    room = server.GameRoom("FLIGHT_MONSTER_ATTACK_TEST")
    ground = {"id": "m1", "pos": [1, 1], "altura": 0}
    flyer = {"id": "p1", "pos": [2, 1], "altura": 3}

    # Corpo a corpo nÃ£o atravessa nÃ­veis de altura, independentemente da IA
    # que chamou o executor comum.
    assert not room._monster_attack_height_ok(ground, flyer, {})
    flyer["altura"] = 0
    assert room._monster_attack_height_ok(ground, flyer, {})

    # Ataques Ã  distÃ¢ncia pagam o custo vertical: 3 pontos = 2 quadrados.
    flyer["altura"] = 3
    assert not room._monster_attack_height_ok(ground, flyer, {"range": 2})
    assert room._monster_attack_height_ok(ground, flyer, {"range": 3})

    # O alcance estendido do ogro tambÃ©m nÃ£o ignora a altura.
    room.players[flyer["id"]] = flyer
    ogro = {"id": "m2", "pos": [1, 1], "altura": 0, "reach_lanca": True}
    assert not room._em_alcance_ogro(ogro, flyer["pos"])
    flyer["altura"] = 0
    assert room._em_alcance_ogro(ogro, flyer["pos"])


def test_executor_monstro_recusa_alvo_aereo_no_melee():
    async def executar():
        room = server.GameRoom("FLIGHT_MONSTER_EXECUTOR_TEST")
        monster = {"id": "m1", "altura": 0}
        flyer = {"id": "p1", "altura": 3, "hp": 10}
        resultado = await room._execute_one_monster_attack(
            monster, {"atk_bonus": 5, "damage": "1d6"},
            {"kind": "player", "obj": flyer})
        assert resultado is False
        assert flyer["hp"] == 10

    asyncio.run(executar())


def test_bola_fogo_residual_fica_no_chao():
    async def verificar():
        room = server.GameRoom("FLIGHT_FIREBALL_GROUND_TEST")
        room._tem_linha_de_visao = lambda *args, **kwargs: True
        room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)
        voador = {"id": "p1", "name": "Voador", "alive": True, "hp": 30,
                  "max_hp": 30, "pos": [2, 2], "altura": 2, "gear": {}}
        no_chao = {"id": "p2", "name": "No chão", "alive": True, "hp": 30,
                   "max_hp": 30, "pos": [2, 3], "altura": 0, "gear": {}}
        room.players = {"p1": voador, "p2": no_chao}
        zona = {"tipo": "bola_fogo", "ativa": True, "cx": 2, "cy": 2,
                "raio": 1, "area_lado": 3, "dano_r2": 5,
                "rodada_atual": 2, "rodadas_max": 2, "caster": "mago"}

        await room._processar_zona_bola_fogo(zona)
        assert voador["hp"] == 30
        assert no_chao["hp"] < 30

        voador["hp"] = 30
        await room._verificar_entrada_zona_fogo(voador, 2, 2)
        assert voador["hp"] == 30
        voador["altura"] = 0
        zona["ativa"] = True
        zona["rodada_atual"] = 2
        room.zonas_especiais = [zona]
        await room._verificar_entrada_zona_fogo(voador, 2, 2)
        assert voador["hp"] < 30

    asyncio.run(verificar())


def test_voo_imunidade_terreno_e_armadilhas():
    async def verificar():
        room = server.GameRoom("FLIGHT_TERRAIN_IMMUNITY_TEST")
        room.materiais = {
            (1, 1): "lava", (2, 2): "agua_profunda",
            (3, 3): "areia_deserto", (4, 4): "pantano",
        }
        room._campfire_tiles = {(5, 5)}
        voador = {
            "id": "p1", "name": "Voador", "alive": True, "hp": 20,
            "max_hp": 20, "pos": [1, 1], "voo": True, "altura": 2,
            "gear": {"armor": {"armor_category": "pesada"}},
        }

        assert room._water_step_cost(voador, 1, 1) == 1
        assert room._water_step_cost(voador, 2, 2) == 1
        assert room._water_step_cost(voador, 3, 3) == 1
        assert room._water_turn_moves(voador, 6) == 6
        voador["moves_left"] = 6
        room._apply_swamp_entry_penalty(voador, 4, 4)
        assert "_swamp_penalty_applied" not in voador

        await room._aplicar_lava_se_pisar(voador)
        await room._aplicar_fogueira_se_pisar({**voador, "pos": [5, 5]})
        assert voador["hp"] == 20

        room.traps = [{"pos": [1, 1], "triggered": False, "damage": 20}]
        await room._verificar_trap_procedural("p1", voador, 1, 1)
        arm = {"id": "a1", "tipo": "armadilha_urso", "pos": [1, 1]}
        room.armadilhas = [arm]
        await room._disparar_armadilha(voador, arm)
        assert arm in room.armadilhas and voador["hp"] == 20

        voador["altura"] = 0
        assert room._water_step_cost(voador, 2, 2) == 5
        await room._disparar_armadilha(voador, arm)
        assert arm not in room.armadilhas

    asyncio.run(verificar())


def main():
    room = server.GameRoom("FLIGHT_ALTITUDE_TEST")
    player = {"pos": [2, 2], "altura": 0,
              "weapon": server.WEAPONS["hand_crossbow"]}
    monster = {"id": "m1", "pos": [2, 6], "size": [1, 1], "altura": 0}

    # Besta de mão: alcance 4 em linha. Cada 2 pontos de altura consome
    # 1 quadrado; distância 4 + altura 2 já fica fora do alcance.
    monster["pos"] = [2, 5]
    assert room._alvo_no_alcance_arma(player, monster)
    monster["altura"] = 2
    assert room._alvo_no_alcance_arma(player, monster)
    monster["pos"] = [2, 6]
    assert not room._alvo_no_alcance_arma(player, monster)

    # Altura arredondada por blocos de 2: altura 6 custa 3 quadrados.
    monster["pos"] = [2, 3]
    monster["altura"] = 6
    assert room._alvo_no_alcance_arma(player, monster)
    monster["altura"] = 10
    assert not room._alvo_no_alcance_arma(player, monster)

    # Corpo a corpo tolera UM nível de desnível; dois ou mais bloqueiam o golpe.
    # A regra mudou em a0385aa (elevação de terreno) — antes exigia o mesmo nível.
    player["weapon"] = server.WEAPONS["lanca_curta"]
    monster["pos"] = [3, 2]
    monster["altura"] = 1
    assert room._alvo_no_alcance_arma(player, monster)
    monster["altura"] = 2
    assert not room._alvo_no_alcance_arma(player, monster)
    monster["altura"] = 0
    assert room._alvo_no_alcance_arma(player, monster)

    elemental_def = next(d for d in server.MONSTER_DEFS
                         if d["type"] == "elemental_ar")
    elemental = server.make_monster(elemental_def, {"id": "r1", "cx": 0, "cy": 0})
    assert elemental["voo"] is True
    assert elemental["altura"] == server.ALTURA_INICIAL_VOO == 2
    assert elemental["altura_max"] == 10
    assert elemental["pode_alterar_altura"] is True
    assert elemental["custo_mov_altura"] == 1
    authored = dict(elemental_def, altura_max=1)
    limited = server.make_monster(authored, {"id": "r2", "cx": 0, "cy": 0})
    assert limited["altura"] == 1

    asyncio.run(test_alterar_altura_manual())
    test_voo_obstaculos()
    test_voo_linha_de_visao()
    test_voo_alcance_vertical_compartilhado()
    test_ataques_de_monstro_respeitam_altura()
    test_executor_monstro_recusa_alvo_aereo_no_melee()
    test_bola_fogo_residual_fica_no_chao()
    test_voo_imunidade_terreno_e_armadilhas()

    print("35 passed, 0 failed")


if __name__ == "__main__":
    main()
